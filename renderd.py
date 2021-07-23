#!/usr/bin/env python3

import argparse
import json
import logging
import logging.handlers
import multiprocessing
import os
import platform
import sys
import time

import pika
import uuid
import xattr

from env import *
from toposm import *
from stats import *


def parse_strategy(candidate):
    if ':' in candidate:
        strategy, count_str = candidate.split(':')
        count = int(count_str)
    else:
        strategy = candidate
        count = 1
    return (strategy, count)
        
def parse_args():
    parser = argparse.ArgumentParser(
        epilog="""
Each `strategy' entry can either be the name of a dequeueing strategy
("by_zoom") or a name followed by a colon and a number ("by_zoom:2").
This gives the number of parallel processes to start with the named
dequeueing strategy.  A missing number is equivalent to a single process.

Multiple strategy entries may be given to cause the creation of processes
with different dequeueing strategies.

Valid strategies are:
 * missing - only render requested-but-absent tiles
 * important - only process important rerenders and missing tiles
 * by_zoom - continuously rerender old tiles, prioritizing tiles at high
   zoom levels.
 * by_work_available - continuously rerender old tiles, prioritizing tiles
   from zoom levels with the greatest amount of rerendering work
   available.

""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--log-level', default='info',
                        choices=['critical', 'error', 'warning', 'info', 'debug'])
    parser.add_argument('strategy', default=[('by_work_available', 1)], nargs='*', type=parse_strategy)
    args = parser.parse_args()

    args.log_level = getattr(logging, args.log_level.upper())
    
    return args


class ContinuousRenderThread:
    def __init__(self, dequeue_strategy, log_queue, ppid, threadNumber):
        logger.info("Creating thread %d" % (threadNumber))
        self.dequeue_strategy = dequeue_strategy
        self.ppid = ppid
        self.threadNumber = threadNumber
        self.tilesizes = []
        self.maps = []

        self.logger = logging.getLogger('toposm.renderd')
        
        rconn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST, heartbeat_interval=0))
        self.chan = rconn.channel()

        self.commandQueue = 'toposm-render-{}-{}-{}'.format(os.uname()[1], ppid, threadNumber)
        self.chan.queue_declare(self.commandQueue, exclusive=True)
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command')
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.{0}'.format(os.uname()[1]))
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm')
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render')
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render.{0}'.format(os.uname()[1]))
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render.{0}.{1}'.format(os.uname()[1], ppid))
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render.{0}.{1}.{2}'.format(os.uname()[1], ppid, threadNumber + 1))
        self.chan.basic_consume(self.on_command, queue=self.commandQueue)
        self.logger.info("Created thread")

    def loadMaps(self, zoom):
        if len(self.maps) <= zoom:
            self.tilesizes.extend([ getTileSize(NTILES[z], True) for z in range(len(self.tilesizes), zoom + 1) ])
            self.maps.extend([None] * (zoom - len(self.maps) + 1))
        self.maps[zoom] = {}
        for mapname in MAPNIK_LAYERS:
            self.logger.debug('Loading mapnik.Map: {0}/{1}'.format(zoom, mapname))
            self.maps[zoom][mapname] = mapnik.Map(self.tilesizes[zoom], self.tilesizes[zoom])
            mapnik.load_map(self.maps[zoom][mapname], mapname + ".xml")

    def runAndLog(self, message, function, args):
        self.logger.info(message)
        try:
            return function(*args)        
        except Exception as ex:
            self.logger.exception('Failed: ' + message)
            raise

    def renderMetaTileFromMsg(self, mt):
        if not mt:
            return
        start_time = time.time()
        layerTimes = None
        if metaTileNeedsRendering(mt.z, mt.x, mt.y):
            self.logger.info('Rendering {0}'.format(mt))
            if len(self.maps) <= mt.z or not self.maps[mt.z]:
                self.loadMaps(mt.z)
            try:
                layerTimes = renderMetaTile(mt.z, mt.x, mt.y, NTILES[mt.z], self.maps[mt.z])
            except:
                self.logger.exception('Failed to render {}'.format(mt))
        if layerTimes:
            stats.recordRender(mt, time.time() - start_time, layerTimes)
        self.logger.debug('Notifying queuemaster of completion.')
        self.chan.basic_publish(
            exchange='osm',
            routing_key='toposm.rendered.{0}.{1}.{2}'.format(mt.z, mt.x, mt.y),
            properties=pika.BasicProperties(reply_to=self.commandQueue,
                                            content_type='application/json'),
            body=json.dumps({'command': 'rendered',
                             'metatile': mt.tojson()}))

    def on_command(self, chan, method, props, body):
        body = body.decode('utf-8')
        self.logger.debug('Received message: ' + body)
        message = json.loads(body)
        if 'command' in message:
            command = message['command']
            if command == 'quit' or command == 'exit':
                chan.stop_consuming()
            elif command == 'newmaps':
                self.maps = []
            elif command == 'reload':
                reload(globals()[parts[1]])
            elif command == 'queuemaster online':
                self.register()
            elif command == 'render':
                self.renderMetaTileFromMsg(Tile.fromjson(message['metatile']))
            else:
                self.logger.warning('Unknown command: ' + body)
        else:
            self.logger.warning('Unrecognized message: ' + body)
        chan.basic_ack(delivery_tag=method.delivery_tag)

    def register(self):
        self.logger.info('Registering with queuemaster.')
        self.chan.basic_publish(
            exchange='osm',
            routing_key='toposm.queuemaster',
            properties=pika.BasicProperties(reply_to=self.commandQueue,
                                            content_type='application/json'),
            body=json.dumps({'command': 'register',
                             'strategy': self.dequeue_strategy,
                             'hostname': platform.node(),
                             'pid': self.ppid,
                             'threadid': self.threadNumber}))

    def unregister(self):
        self.logger.info('Unregistering with queuemaster.')
        pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST)).\
            channel().basic_publish(
                exchange='osm',
                routing_key='toposm.queuemaster',
                properties=pika.BasicProperties(reply_to=self.commandQueue,
                                                content_type='application/json'),
                body=json.dumps({'command': 'unregister'}))

    def renderLoop(self):
        self.register()
        try:
            self.chan.start_consuming()
        finally:
            self.unregister()


def isOldTile(z, x, y):
    tile_path = getTilePath(REFERENCE_TILESET, z, x, y)
    return path.isfile(tile_path) and b'user.toposm_dirty' in xattr.list(tile_path)

def tileNeedsRendering(z, x, y):
    return not tileExists(REFERENCE_TILESET, z, x, y) or isOldTile(z, x, y)

def isOldMetaTile(z, x, y):
    ntiles = NTILES[z]
    tile_path = getTilePath(REFERENCE_TILESET, z, x*ntiles, y*ntiles)
    return path.isfile(tile_path) and b'user.toposm_dirty' in xattr.list(tile_path)

def metaTileNeedsRendering(z, x, y):
    ntiles = NTILES[z]
    return not tileExists(REFERENCE_TILESET, z, x*ntiles, y*ntiles) or isOldMetaTile(z, x, y)

def logging_processor(log_level, queue):
    log_handler = logging.StreamHandler()
    log_handler.setLevel(log_level)
    log_handler.setFormatter(logging.Formatter(
        '{asctime} [{processName}] {message}',
        style='{',
        datefmt='%Y-%m-%d %H:%M:%S'))
    log_handler.addFilter(logging.Filter('toposm'))
    root = logging.getLogger()
    root.addHandler(log_handler)
    root.setLevel(log_level)
    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import sys, traceback
            print('Problem in logging thread:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    

if __name__ == "__main__":
    args = parse_args()
    log_queue = multiprocessing.Queue()
    log_process = multiprocessing.Process(target=logging_processor, args=(args.log_level, log_queue))
    log_process.start()
    
    try:
        logger.info('Initializing.')
    
        conn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST))
        chan = conn.channel()
        chan.exchange_declare(exchange="osm", exchange_type="topic", durable=True, auto_delete=False)
        conn.close()
        
        root_logger = logging.getLogger()
        root_logger.addHandler(logging.handlers.QueueHandler(log_queue))
        root_logger.setLevel(logging.DEBUG)
        
        logger.info('Starting renderer.')
        processes = []
        for strategy, count in args.strategy:
            for i in range(0, count):
                thread_id = len(processes)
                renderer = ContinuousRenderThread(strategy, log_queue, os.getpid(), thread_id)
                process = multiprocessing.Process(target=renderer.renderLoop, name='{:02d} {}'.format(thread_id, strategy))
                process.start()
                processes.append(process)
        for process in processes:
            process.join()

    finally:
        logger.info('Terminating.')
        log_queue.put(None)
        log_process.join()
