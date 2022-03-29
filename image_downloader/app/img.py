#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import requests
import redis
import time
import datetime
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
logger = logging.getLogger(__name__)

cache = redis.Redis(host='redis', port=6379)

# TODO extract this IPs from the file.
picUrls = {'photo_garage12' : 'https://192.168.2.248/cgi-bin/currentpic.cgi',
            'photo_garage13' : 'https://192.168.2.249/cgi-bin/currentpic.cgi',
            'photo_office4' : 'https://192.168.100.201/cgi-bin/currentpic.cgi'}

def update(msg):
    for key in picUrls:
        val = cache.get(key)
        if val is not None:
            cache.delete(key)
            valStr = val.decode("utf-8")
            resultTarget = valStr.split(',')[1]
            logging.info("loading photo from: " + picUrls[key])
            # TODO Extract the authentication from this file.
            content = requests.get(picUrls[key], verify=False, auth=('root','')).content
            logging.info("sending photo to: (" + resultTarget + ')')
            cache.setex(resultTarget, datetime.timedelta(seconds=10), value=content)

pubsub = cache.pubsub()
# Set Config redis key expire listener
cache.config_set('notify-keyspace-events', 'Exsg')
pubsub.psubscribe(**{"__key*__:*": update})
pubsub.run_in_thread(sleep_time=0.01)


if __name__ == "__main__":
    logging.info("Starting image loader")

    while True:
        time.sleep(1)
