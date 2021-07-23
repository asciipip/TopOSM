#!/usr/bin/env python3

import argparse
import json
import logging
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


logger = logging.getLogger('toposm.renderd')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('strategy', default='by_work_available', nargs='?')
    args = parser.parse_args()

    return args


class ContinuousRenderThread:
    def __init__(self, dequeue_strategy, amqp_channel, threadNumber):
        logger.info("Creating thread %d" % (threadNumber))
        self.dequeue_strategy = dequeue_strategy
        self.chan = amqp_channel
        self.threadNumber = threadNumber
        self.tilesizes = []
        self.maps = []

        self.commandQueue = self.chan.queue_declare(exclusive=True).method.queue
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command')
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.{0}'.format(os.uname()[1]))
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm')
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render')
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render.{0}'.format(os.uname()[1]))
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render.{0}.{1}'.format(os.uname()[1], os.getpid()))
        self.chan.queue_bind(queue=self.commandQueue, exchange='osm', routing_key='command.toposm.render.{0}.{1}.{2}'.format(os.uname()[1], os.getpid(), threadNumber + 1))
        self.chan.basic_consume(self.on_command, queue=self.commandQueue)
        logger.info("Created thread")

    def loadMaps(self, zoom):
        if len(self.maps) <= zoom:
            self.tilesizes.extend([ getTileSize(NTILES[z], True) for z in range(len(self.tilesizes), zoom + 1) ])
            self.maps.extend([None] * (zoom - len(self.maps) + 1))
        self.maps[zoom] = {}
        for mapname in MAPNIK_LAYERS:
            logger.debug('Loading mapnik.Map: {0}/{1}'.format(zoom, mapname))
            self.maps[zoom][mapname] = mapnik.Map(self.tilesizes[zoom], self.tilesizes[zoom])
            mapnik.load_map(self.maps[zoom][mapname], mapname + ".xml")

    def runAndLog(self, message, function, args):
        logger.info(message)
        try:
            return function(*args)        
        except Exception as ex:
            logger.exception('Failed: ' + message)
            raise

    def renderMetaTileFromMsg(self, mt):
        if not mt:
            return
        start_time = time.time()
        layerTimes = None
        if metaTileNeedsRendering(mt.z, mt.x, mt.y):
            logger.info('Rendering {0}'.format(mt))
            if len(self.maps) <= mt.z or not self.maps[mt.z]:
                self.loadMaps(mt.z)
            try:
                layerTimes = renderMetaTile(mt.z, mt.x, mt.y, NTILES[mt.z], self.maps[mt.z])
            except:
                logger.exception('Failed to render {}'.format(mt))
        if layerTimes:
            stats.recordRender(mt, time.time() - start_time, layerTimes)
        logger.debug('Notifying queuemaster of completion.')
        self.chan.basic_publish(
            exchange='osm',
            routing_key='toposm.rendered.{0}.{1}.{2}'.format(mt.z, mt.x, mt.y),
            properties=pika.BasicProperties(reply_to=self.commandQueue,
                                            content_type='application/json'),
            body=json.dumps({'command': 'rendered',
                             'metatile': mt.tojson()}))

    def on_command(self, chan, method, props, body):
        body = body.decode('utf-8')
        logger.debug('Received message: ' + body)
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
                logger.warning('Unknown command: ' + body)
        else:
            logger.warning('Unrecognized message: ' + body)
        chan.basic_ack(delivery_tag=method.delivery_tag)

    def register(self):
        logger.info('Registering with queuemaster.')
        self.chan.basic_publish(
            exchange='osm',
            routing_key='toposm.queuemaster',
            properties=pika.BasicProperties(reply_to=self.commandQueue,
                                            content_type='application/json'),
            body=json.dumps({'command': 'register',
                             'strategy': self.dequeue_strategy,
                             'hostname': platform.node(),
                             'pid': os.getpid(),
                             'threadid': self.threadNumber}))

    def unregister(self):
        logger.info('Unregistering with queuemaster.')
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


if __name__ == "__main__":
    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(logging.Formatter(
        '{asctime} [{threadName}] {message}',
        style='{',
        datefmt='%Y-%m-%d %H:%M:%S'))
    log_handler.addFilter(logging.Filter('toposm'))
    root = logging.getLogger('toposm')
    root.addHandler(log_handler)
    root.setLevel(logging.DEBUG)

    logger.info('Initializing.')
    args = parse_args()

    conn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST))
    chan = conn.channel()
    chan.exchange_declare(exchange="osm", exchange_type="topic", durable=True, auto_delete=False)
    conn.close()

    logger.info('Starting renderer.')
    rconn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST, heartbeat_interval=0))
    rchan = rconn.channel()
    renderer = ContinuousRenderThread(args.strategy, rchan, 0)
    renderer.renderLoop()
