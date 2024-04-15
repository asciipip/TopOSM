#!/usr/bin/env python3

# standard modules
import collections
import datetime
import dateutil.parser
import json
import logging
import os
import os.path
import random
import re
import threading

# addon modules
import pika
import xattr

import pprint

from toposm import *
import tileexpire


# How often the tile expiry thread should wake up and see if it should process
# the dequeued expirations.
EXPIRE_SLEEP_INTERVAL = 10
# How long we can go without hearing from a renderer before we consider it
# stale.
RENDERER_STALE_TIME = 3600
# For the initial queue loading, wait until after this zoom level is complete
# before starting to render things.  (This prevents the renderers always being
# asked to render stuff at zoom 2 to start with.)
INITIAL_QUEUE_NOTIFY_ZOOM = 7
# Maximum age of the database for rendering, in seconds.  If the database age is
# greater than this, non-important rendering will cease until the database
# catches up.
# Half an hour.
MAXIMUM_DATABASE_AGE = 30 * 60
# One month (30 days)
#MAXIMUM_DATABASE_AGE = 30 * 24 * 60 * 60


logger = logging.getLogger('toposm.queuemaster')


def database_age():
    try:
        with open(MINUTELY_STATE_FILE) as state:
            for line in state:
                m = re.search('^timestamp=(.*)', line)
                if m:
                    minutely_timestamp = dateutil.parser.parse(m.group(1).replace('\\', ''))
                    return (datetime.datetime.now(minutely_timestamp.tzinfo) - minutely_timestamp).total_seconds()
    except:
        # Any errors just result in None being returned, same as if we couldn't
        # find a timestamp line in the file.
        pass
    return None


class Renderer:
    def __init__(self, registration, render_queue, amqp_queue, channel):
        self.render_queue = render_queue
        self.amqp_queue = amqp_queue
        self.channel = channel
        self.hostname = registration['hostname']
        self.pid = registration['pid']
        self.threadid = registration['threadid']
        self.dequeue_strategy = registration['strategy']
        self.working_on = None
        self.last_activity = time.time()

    @property
    def name(self):
        return '%s.%s.%s' % (self.hostname, self.pid, self.threadid)

    @property
    def idle(self):
        return not self.working_on

    @property
    def status(self):
        if self.idle:
            return 'idle'
        base = 'rendering: %s' % self.working_on
        time_since_last_contact = time.time() - self.last_activity
        if time_since_last_contact > RENDERER_STALE_TIME:
            if time_since_last_contact > (60 * 60 * 24):
                stale = ' (STALE %d days)' % (time_since_last_contact / (60 * 60 * 24))
            elif time_since_last_contact > (60 * 60):
                stale = ' (STALE %d hours)' % (time_since_last_contact / (60 * 60))
            elif time_since_last_contact > 60:
                stale = ' (STALE %d minutes)' % (time_since_last_contact / 60)
            else:
                stale = ' (STALE %d seconds)' % time_since_last_contact
        else:
            stale = ''
        return base + stale

    def send_request(self):
        if self.idle:
            mt = self.render_queue.dequeue(self.dequeue_strategy)
            if mt:
                logger.info('%s -> render %s' % (self.name, mt))
                self.working_on = mt
                self.last_activity = time.time()
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.amqp_queue,
                    properties=pika.BasicProperties(
                        content_type='application/json'),
                    body=json.dumps({'command': 'render',
                                     'metatile': mt.tojson()}))

    def finished(self, metatile):
        # Check to see if it's what we think we're working on.  If not, assume
        # it's from a previous queuemaster and ignore the message.
        if self.working_on == metatile:
            self.working_on = None
        # This counts as the client being active, though.
        self.last_activity = time.time()


class Queue:
    def __init__(self, maxz):
        self.maxz = maxz
        self.lock = threading.Lock()
        self.queued_metatiles = set()
        self.zoom_queues = [ collections.deque() for z in range(0, self.maxz + 1) ]
        self.missing_queue = collections.deque()
        self.important_stack = collections.deque()
        self.pending_metatiles = set()

    def queue_metatile(self, mt, queue, source):
        assert mt.is_metatile
        if mt in self.pending_metatiles:
            logger.info('skipping pending metatile: {0}'.format(mt))
            return
        added = False
        if queue is self.zoom_queues[mt.z]:
            # Ordinary, by-zoom queue.
            with self.lock:
                if mt not in self.queued_metatiles:
                    queue.append(mt)
                    self.queued_metatiles.add(mt)
                    added = True
        else:
            # Specialty queue.
            with self.lock:
                if mt not in queue:
                    queue.append(mt)
                    self.queued_metatiles.add(mt)
                    if mt in self.zoom_queues[mt.z]:
                        self.zoom_queues[mt.z].remove(mt)
                    added = True
        if added:
            if source:
                logger.info('queue from %s: %s' % (source, mt))
            else:
                logger.info('queue: %s' % mt)

    def queue_tile(self, t, queue='zoom', source=None):
        assert not t.is_metatile
        if queue == 'missing':
            self.queue_metatile(t.metatile, self.missing_queue, source)
        elif queue == 'important':
            self.queue_metatile(t.metatile, self.important_stack, source)
        elif queue == 'zoom':
            self.queue_metatile(t.metatile, self.zoom_queues[t.z], source)

    def dequeue(self, strategy):
        try:
            mt = self.missing_queue.popleft()
        except IndexError:
            if strategy == 'missing':
                return None
            try:
                mt = self.important_stack.pop()
            except IndexError:
                db_age = database_age()
                if db_age is None or db_age > MAXIMUM_DATABASE_AGE:
                    return None
                elif strategy == 'important':
                    return None
                elif strategy == 'by_work_available':
                    mt = self.dequeue_by_work_available()
                elif strategy == 'by_zoom':
                    mt = self.dequeue_by_zoom()
                else:
                    logger.warning('unknown dequeue strategy: %s' % strategy)
                    return None
        if not mt:
            return None
        with self.lock:
            if mt in self.queued_metatiles:
                self.queued_metatiles.remove(mt)
            self.pending_metatiles.add(mt)
        return mt

    def mark_metatile_rendered(self, mt):
        assert mt.is_metatile
        with self.lock:
            if mt in self.pending_metatiles:
                self.pending_metatiles.remove(mt)

    def mark_metatile_abandoned(self, mt):
        assert mt.is_metatile
        with self.lock:
            if mt in self.pending_metatiles:
                self.pending_metatiles.remove(mt)
        self.queue_metatile(mt, self.important_stack, 'abandoned')

    def get_stats(self):
        stats = {z: len(self.zoom_queues[z]) for z in range(0, self.maxz + 1)}
        stats.update({'important': len(self.important_stack),
                      'missing': len(self.missing_queue)})
        return stats

    def dequeue_by_work_available(self):
        # Queues are weighted according to how many messages they have and the
        # likelihood of further updates invalidating the queue's tiles.  (At
        # zoom level 0, every update invalidates the tile.  At zoom 1, an update
        # has a one-in-four chance of invalidating the tile, and so on.  Thus,
        # the higher the zoom level, the more weight they're given, so low-zoom
        # tiles are not rendered as often as their queue length might otherwise
        # dictate.)
        weighted_queues = [ len(self.zoom_queues[z]) * pow(4, z) / pow(NTILES[z], 2) for z in range(0, self.maxz + 1) ]
        if sum(weighted_queues) == 0:
            return None
        queue_pcts = [ float(t) / sum(weighted_queues) for t in weighted_queues ]
        chosen_pct = random.random()
        pct_sum = 0
        chosen_queue = self.maxz
        for z in range(0, self.maxz + 1):
            pct_sum += queue_pcts[z]
            if chosen_pct < pct_sum and chosen_queue == self.maxz:
                chosen_queue = z
        try:
            return self.zoom_queues[chosen_queue].popleft()
        except IndexError:
            return self.dequeue_by_work_available()

    def dequeue_by_zoom(self):
        # Considers only the total number of tiles at each zoom level, not the
        # number of tiles present.  (Exception: empty queues are not considered
        # at all.)  Good for clearing out nearly-empty high-zoom queues that the
        # by_pct strategy will neglect.
        queues = [ 2**z if len(self.zoom_queues[z]) > 0 else 0 for z in range(0, self.maxz + 1) ]
        if sum(queues) == 0:
            return None
        queue_pcts = [ float(t) / sum(queues) for t in queues ]
        chosen_pct = random.random()
        pct_sum = 0
        chosen_queue = self.maxz
        for z in range(0, self.maxz + 1):
            pct_sum += queue_pcts[z]
            if chosen_pct < pct_sum and chosen_queue == self.maxz:
                chosen_queue = z
        try:
            return self.zoom_queues[chosen_queue].popleft()
        except IndexError:
            return self.dequeue_by_zoom()
        

class QueueFiller(threading.Thread):
    def __init__(self, maxz, queue):
        threading.Thread.__init__(self)
        self.maxz = maxz
        self.queue = queue
        self.keep_running = True
        self.current_zoom = None
        self.lock = threading.Lock()
        self.conn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST))
        self.chan = self.conn.channel()
        
    def run(self):
        logger.info('Initializing queue.')
        for z in range(2, self.maxz + 1):
            with self.lock:
                self.current_zoom = z
            for root, dirs, files in os.walk(os.path.join(BASE_TILE_DIR, REFERENCE_TILESET, str(z))):
                dirty_tiles = []
                for file in files:
                    full_path = os.path.join(root, file)
                    if b'user.toposm_dirty' in xattr.list(full_path):
                        cs = root.split('/')
                        dirty_tiles.append(
                            (os.stat(full_path).st_mtime, Tile(int(cs[-2]), int(cs[-1]), int(file.split('.')[0]))))
                    if not self.keep_running:
                        return
                dirty_tiles.sort()
                for time, t in dirty_tiles:
                    self.queue.queue_tile(t, 'zoom', 'init')
                if len(dirty_tiles) > 0 and z >= INITIAL_QUEUE_NOTIFY_ZOOM:
                    self.notify_queuemaster()
        with self.lock:
            self.current_zoom = -1
        logger.info('Queue initialized.')

    def notify_queuemaster(self):
        self.chan.basic_publish(
            exchange='osm',
            routing_key='toposm.queuemaster',
            body=json.dumps({'command': 'queued'}))

    def get_status(self):
        with self.lock:
            return self.current_zoom

    def quit(self):
        self.keep_running = False


class TileExpirer(threading.Thread):
    def __init__(self, maxz, queue):
        threading.Thread.__init__(self)
        self.maxz = maxz
        self.queue = queue
        self.keep_running = True
        self.input_queue = collections.deque()
        self.lock = threading.Lock()
        self.current_expire = None
        self.current_expire_zoom = None
        self.conn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST, heartbeat=0))
        self.chan = self.conn.channel()

    def run(self):
        while self.keep_running or len(self.input_queue) > 0:
            if len(self.input_queue) > 0:
                logger.info('reading expiry input queue')
                expire = tileexpire.OSMTileExpire()
                try:
                    while True:
                        t = self.input_queue.popleft()
                        expire.expire(t.z, t.x, t.y)
                except IndexError:
                    logger.info('expiry input queue empty; expiring')
                    self.process_expire(expire)
                    self.notify_queuemaster()
                    logger.info('expiration pass finished')
            else:
                time.sleep(EXPIRE_SLEEP_INTERVAL)

    def process_expire(self, expire):
        with self.lock:
            self.current_expire = expire
        for z in range(self.maxz, 2 - 1, -1):
            with self.lock:
                self.current_expire_zoom = z
            for (x, y) in expire.expiredAt(z):
                t = Tile(z, x, y)
                tile_path = getTilePath(REFERENCE_TILESET, z, x, y)
                if path.isfile(tile_path):
                    if b'user.toposm_dirty' not in xattr.list(tile_path):
                        xattr.set(tile_path, 'user.toposm_dirty', 'yes')
                    mt = t.metatile
                    tile_path = getTilePath(REFERENCE_TILESET, mt.z, mt.x * NTILES[z], mt.y * NTILES[z])
                    if path.isfile(tile_path) and b'user.toposm_dirty' not in xattr.list(tile_path):
                        xattr.set(tile_path, 'user.toposm_dirty', 'yes')
                    self.queue.queue_tile(t, 'zoom', 'expire')
        with self.lock:
            self.current_expire = None
            self.current_expire_zoom = None

    def add_expired(self, t):
        assert not t.is_metatile
        self.input_queue.append(t)

    def get_input_length(self):
        return len(self.input_queue)

    def get_expire_status(self):
        with self.lock:
            if self.current_expire:
                try:
                    return (self.current_expire_zoom, self.current_expire.countExpiredAt(self.current_expire_zoom))
                except:
                    return None
            else:
                return None

    def notify_queuemaster(self):
        try:
            self.chan.basic_publish(
                exchange='osm',
                routing_key='toposm.queuemaster',
                body=json.dumps({'command': 'queued'}))
        except pika.exceptions.ConnectionClosed:
            self.conn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST, heartbeat_interval=0))
            self.chan = self.conn.channel()
            self.notify_queuemaster()

    def quit(self):
        self.keep_running = False


class Queuemaster:

    def __init__(self, maxz):
        self.maxz = maxz
        self.exiting = False
        self.queue = Queue(self.maxz)
        self.initializer = None
        self.expirer = TileExpirer(self.maxz, self.queue)
        self.expirer.start()
        self.renderers = {}
        self.influx_client = connect_to_influxdb()

    ### Startup sequence.
    
    def run(self):
        self.connection = pika.SelectConnection(
            parameters=pika.ConnectionParameters(host=DB_HOST),
            on_open_callback=self.on_connection_open)
        self.connection.ioloop.start()
        
    def on_connection_open(self, conn):
        conn.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, chan):
        self.channel = chan
        chan.exchange_declare(
            "osm",
            exchange_type="topic",
            durable=True,
            auto_delete=False,
            callback=self.on_exchange_declare)

    def on_exchange_declare(self, frame):
        self.channel.queue_declare(
            'toposm-queuemaster',
            exclusive=True,
            auto_delete=True,
            callback=self.on_command_declare)
        self.channel.queue_declare(
            'expire_toposm',
            durable=True,
            auto_delete=False,
            callback=self.on_expire_declare)
            
    def on_expire_declare(self, frame):
        self.channel.queue_bind(
            'expire_toposm', 'osm',
            routing_key='expire',
            callback=self.on_expire_bind)

    def on_expire_bind(self,frame):
        self.channel.basic_consume('expire_toposm',
                                   self.on_expire,
                                   exclusive=True, auto_ack=True)
        self.channel.add_on_cancel_callback(self.on_cancel)
        self.channel.add_on_close_callback(self.on_close)
        self.initializer = QueueFiller(self.maxz, self.queue)
        self.initializer.start()
    
    def on_command_declare(self, frame):
        self.command_queue = frame.method.queue
        self.channel.queue_bind(
            queue=self.command_queue,
            exchange='osm',
            routing_key='toposm.rendered.#')
        self.channel.queue_bind(
            queue=self.command_queue,
            exchange='osm',
            routing_key='toposm')
        self.channel.queue_bind(
            queue=self.command_queue,
            exchange='osm',
            routing_key='toposm.queuemaster',
            callback=self.on_command_bind)

    def on_command_bind(self, frame):
        self.channel.basic_consume(queue=self.command_queue,
                                   on_message_callback=self.on_command,
                                   exclusive=True)
        logger.info('queuemaster online')
        self.channel.basic_publish(exchange='osm',
                                   routing_key='toposm',
                                   body=json.dumps({'command': 'queuemaster online'}))

    def on_cancel(self, frame):
        logger.info('AMQP cancelled: {}'.format(frame))

    def on_close(self, channel, reason):
        logger.info('AMQP closed channel {}: {}'.format(channel, reason))
        if self.exiting:
            return
        # Unless we're actively exiting, assume the connection loss was
        # transient and we should reconnect.
        self.connection = pika.SelectConnection(
            pika.ConnectionParameters(host=DB_HOST), self.on_connection_open)
        self.connection.ioloop.start()

    ### AMQP commands.
    
    def on_expire(self, chan, method, props, body):
        body = body.decode('utf-8')
        for tile_str in body.split(';'):
            self.expirer.add_expired(Tile.fromstring(tile_str))

    def on_command(self, chan, method, props, body):
        body = body.decode('utf-8')
        try:
            message = json.loads(body)
            command = message['command']
            if command == 'register':
                self.add_renderer(message, props.reply_to)
                self.send_render_requests()
            elif command == 'unregister':
                if props.reply_to in self.renderers:
                    self.remove_renderer(props.reply_to)
            elif command == 'rendered':
                mt = Tile.fromjson(message['metatile'], True)
                if props.reply_to in self.renderers:
                    self.renderers[props.reply_to].finished(mt)
                self.queue.mark_metatile_rendered(mt)
                self.send_render_requests()
            elif command == 'stats':
                chan.basic_publish(
                    exchange='',
                    routing_key=props.reply_to,
                    properties=pika.BasicProperties(
                        correlation_id=props.correlation_id,
                        content_type='application/json'),
                    body=self.get_stats())
            elif command == 'render':
                self.handle_render_request(Tile.fromjson(message['tile']), props)
                self.send_render_requests()
            elif command == 'queued':
                self.send_render_requests()
            elif command == 'quit':
                self.quit()
            elif command == 'queuemaster online':
                pass
            else:
                logger.warning('unknown message: %s' % body)
        except ValueError:
            logger.exception('Non-JSON message: %s' % body)
        if chan.is_open:
            chan.basic_ack(delivery_tag=method.delivery_tag)

    def get_stats(self):
        result = {'queue': self.queue.get_stats(),
                  'expire': {'input': self.expirer.get_input_length(),
                             'status': self.expirer.get_expire_status()},
                  'render': {r.name: (r.status, r.dequeue_strategy) for r in self.renderers.values()}}
        if self.initializer and self.initializer.is_alive():
            result['init'] = self.initializer.get_status()
        return json.dumps(result)

    def add_renderer(self, message, queue):
        self.renderers[queue] =  Renderer(message, self.queue, queue, self.channel)

    def remove_renderer(self, queue):
        if self.renderers[queue].working_on:
            self.queue.mark_metatile_abandoned(self.renderers[queue].working_on)
        del self.renderers[queue]

    def send_render_requests(self):
        for renderer in self.renderers.values():
            renderer.send_request()
        self.send_queue_metrics()

    def handle_render_request(self, t, props):
        if not t.is_valid:
            logger.warning('ignoring request for invalid tile: %s' % t)
            return
        if t.exists(REFERENCE_TILESET):
            importance = 'important'
        else:
            importance = 'missing'
        self.queue.queue_tile(t, importance, 'request')

    def send_queue_metrics(self):
        frames = []
        for queue_name, queue_len in self.queue.get_stats().items():
            frames.append({
                'measurement': 'queue',
                'tags': {'name': str(queue_name)},
                'fields': {'length': queue_len}
            })
        try:
            self.influx_client.write_points(frames)
        except influxdb.exceptions.InfluxDBServerError as e:
            logger.warning('InfluxDB error, reconnecting: {}'.format(e))
            self.influx_client = connect_to_influxdb()
            time.sleep(1)
            self.send_queue_metrics()
        
    def quit(self):
        logger.info('Exiting.')
        self.exiting = True
        self.initializer.quit()
        self.expirer.quit()
        self.expirer.join()
        self.initializer.join()
        self.connection.close()
        self.connection.ioloop.start()
        logger.info('Shutdown process concluded.')


if __name__ == "__main__":
    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(logging.Formatter(
        '{asctime} {message}',
        style='{',
        datefmt='%Y-%m-%d %H:%M:%S'))
    log_handler.addFilter(logging.Filter('toposm'))
    root = logging.getLogger('toposm')
    root.addHandler(log_handler)
    root.setLevel(logging.DEBUG)
    qm = Queuemaster(16)
    qm.run()
