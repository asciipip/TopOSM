#!/usr/bin/python

import json
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


REFERENCE_FILE = '/srv/tiles/tirex/planet-import-complete'
REFERENCE_MTIME = path.getmtime(REFERENCE_FILE)


class ContinuousRenderThread:
    def __init__(self, dequeue_strategy, amqp_channel, threadNumber):
        console.printMessage("Creating thread %d" % (threadNumber))
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
        self.printMessage("Created thread")

    def loadMaps(self, zoom):
        if len(self.maps) <= zoom:
            self.tilesizes.extend([ getTileSize(NTILES[z], True) for z in xrange(len(self.tilesizes), zoom + 1) ])
            self.maps.extend([None] * (zoom - len(self.maps) + 1))
        self.maps[zoom] = {}
        for mapname in MAPNIK_LAYERS:
            console.debugMessage('Loading mapnik.Map: {0}/{1}'.format(zoom, mapname))
            self.maps[zoom][mapname] = mapnik.Map(self.tilesizes[zoom], self.tilesizes[zoom])
            mapnik.load_map(self.maps[zoom][mapname], mapname + ".xml")

    def printMessage(self, message):
        message = '[%02d] %s' % (self.threadNumber+1,  message)
        console.printMessage(message)

    def runAndLog(self, message, function, args):
        message = '[%02d] %s' % (self.threadNumber+1,  message)
        console.printMessage(message)
        try:
            return function(*args)        
        except Exception as ex:
            console.printMessage('Failed: ' + message)
            errorLog.log('Failed: ' + message, ex)
            raise

    def renderMetaTileFromMsg(self, mt):
        if not mt:
            return
        start_time = time.time()
        layerTimes = None
        if metaTileNeedsRendering(mt.z, mt.x, mt.y):
            print time.strftime('%Y-%m-%d %H:%M:%S')
            message = 'Rendering {0}'.format(mt)
            if len(self.maps) <= mt.z or not self.maps[mt.z]:
                self.loadMaps(mt.z)
            layerTimes = self.runAndLog(message, renderMetaTile, (mt.z, mt.x, mt.y, NTILES[mt.z], self.maps[mt.z]))
            print time.strftime('%Y-%m-%d %H:%M:%S')
        if layerTimes:
            stats.recordRender(mt.z, time.time() - start_time, layerTimes)
        self.printMessage('Notifying queuemaster of completion.')
        self.chan.basic_publish(
            exchange='osm',
            routing_key='toposm.rendered.{0}.{1}.{2}'.format(mt.z, mt.x, mt.y),
            properties=pika.BasicProperties(reply_to=self.commandQueue,
                                            content_type='application/json'),
            body=json.dumps({'command': 'rendered',
                             'metatile': mt.tojson()}))

    def on_command(self, chan, method, props, body):
        self.printMessage('Received message: ' + body)
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
                self.printMessage('Unknown command: ' + body)
        else:
            self.printMessage('Unrecognized message: ' + body)
        chan.basic_ack(delivery_tag=method.delivery_tag)

    def register(self):
        self.printMessage('Registering with queuemaster.')
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
        self.printMessage('Unregistering with queuemaster.')
        self.chan.basic_publish(
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
    return path.isfile(tile_path) and 'user.toposm_dirty' in xattr.listxattr(tile_path)

def tileNeedsRendering(z, x, y):
    return not tileExists(REFERENCE_TILESET, z, x, y) or isOldTile(z, x, y)

def isOldMetaTile(z, x, y):
    ntiles = NTILES[z]
    tile_path = getTilePath(REFERENCE_TILESET, z, x*ntiles, y*ntiles)
    return path.isfile(tile_path) and 'user.toposm_dirty' in xattr.listxattr(tile_path)

def metaTileNeedsRendering(z, x, y):
    ntiles = NTILES[z]
    return not tileExists(REFERENCE_TILESET, z, x*ntiles, y*ntiles) or isOldMetaTile(z, x, y)


if __name__ == "__main__":
    console.printMessage('Initializing.')

    if len(sys.argv) >= 2:
        dequeue_strategy = sys.argv[1]
    else:
        dequeue_strategy = 'by_work_available'
    
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST))
    chan = conn.channel()
    chan.exchange_declare(exchange="osm", type="topic", durable=True, auto_delete=False)
    conn.close()

    console.printMessage('Starting renderer.')
    rconn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST, heartbeat_interval=0))
    rchan = rconn.channel()
    renderer = ContinuousRenderThread(dequeue_strategy, rchan, 0)
    renderer.renderLoop()
