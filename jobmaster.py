#! coding: utf-8
# pylint: disable-msg=W0311
import sys
import os
import api
import worker
import settings
from time import time, sleep

plugins_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(plugins_dir)
sys.path.append(src_dir)


if __name__ == '__main__':
  while True:
    ts = int(time())
    if ts % settings.step_size == 0:
      urls = api.get_urls_and_hostname()
      for info in urls:
        url = info.get('url')
        hostname = info.get('hostname')
        
        ts += settings.step_size
        worker.LOG.debug('Sent to queue: %s - %s' % (ts, url))
        print '[%s] %s' % (ts, url)
        if hostname:
          worker.QUEUE.put('%s|%s|%s' % (ts, url, hostname))
        else:
          worker.QUEUE.put('%s|%s|' % (ts, url))
    sleep(1)