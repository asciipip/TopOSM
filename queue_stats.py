#!/usr/bin/python

import json
import math
import time
import uuid

import pika

from toposm import *

def print_stats(s):
    print 'expire queue: %s' % s['expire']
    print ''
    queues = [0] * len(s['queue'])
    weighted_queues = [0] * len(s['queue'])
    fixed_pct_queues = [0] * len(s['queue'])
    q_width = 1
    for k, v in s['queue'].items():
        z = int(k)
        if v > 0:
            w = int(math.ceil(math.log(v, 10)))
            if w > q_width:
                q_width = w
            fixed_pct_queues[z] = 2**z
        queues[z] = v
        weighted_queues[z] = v * pow(4, z) / pow(NTILES[z], 2)
    z = 0
    total = sum(queues)
    total_w = sum(weighted_queues)
    total_fp = sum(fixed_pct_queues)
    print 'zoom  count  weighted    fixed'
    print '----  -----  --------    -----'
    for z in xrange(0, len(queues)):
        count = queues[z]
        count_w = weighted_queues[z]
        count_fp = fixed_pct_queues[z]
        print '  {0:2}: {1:>5}  {2:8.2%}  {3:7.3%}'.format(z, str(count).rjust(q_width),
                                                       float(count_w) / float(total_w),
                                                       float(count_fp) / float(total_fp))

conn = pika.BlockingConnection(pika.ConnectionParameters(host=DB_HOST))
chan = conn.channel()
queue = chan.queue_declare(exclusive=True).method.queue

correlation_id = str(uuid.uuid4())
time_sent = time.time()
chan.basic_publish(exchange='osm',
                   routing_key='toposm.queuemaster',
                   properties=pika.BasicProperties(reply_to=queue,
                                                   correlation_id=correlation_id),
                   body=json.dumps({'command': 'stats'}))

result_received = False
while not result_received:
    (method, props, body) = chan.basic_get(queue=queue, no_ack=True)
    if method and props.correlation_id == correlation_id:
        print '%0.2f seconds to receive message' % (time.time() - time_sent)
        print ''
        print_stats(json.loads(body))
        result_received = True