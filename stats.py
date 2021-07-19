#!/usr/bin/python

import lockfile
import os.path
import pickle

import influxdb

from coords import *
from env import *

class StatsManager:
    lock = lockfile.FileLock('stats')
    def __init__(self):
        self.influx_client = influxdb.InfluxDBClient(database='toposm')
        with self.lock:
            if not os.path.isfile('stats'):
                with open('stats', 'wb') as f:
                    pickle.dump({}, f)

    def recordRender(self, metatile, totalTime, layerTimes):
        with self.lock:
            influx_frames = [{
                'measurement': 'render',
                'tags': {
                    'zoom': str(metatile.z),
                    #'geohash': getTileGeohash(metatile.z, metatile.x, metatile.y, NTILES[metatile.z]),
                },
                'fields': {'render_time': totalTime, 'z': metatile.z}
            }]
            for layer, layer_time in layerTimes.items():
                influx_frames.append({
                    'measurement': 'render_layer',
                    'tags': {
                        'zoom': str(metatile.z),
                        'layer': layer,
                    },
                    'fields': {'render_time': layer_time}
                })
            self.influx_client.write_points(influx_frames)
        
            with open('stats', 'rb') as f:
                stats = pickle.load(f)
            (c, t) = stats.setdefault(metatile.z, {}).setdefault('total', (0, 0))
            stats[metatile.z]['total'] = (c + 1, t + totalTime)
            for layer in layerTimes:
                (c, t) = stats[metatile.z].setdefault(layer, (0, 0))
                stats[metatile.z][layer] = (c + 1, t + layerTimes[layer])
            with open('stats', 'wb') as f:
                pickle.dump(stats, f)

stats = StatsManager()
