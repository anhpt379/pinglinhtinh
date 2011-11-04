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
      urls = api.get_urls()
      for url in urls:
        ts += settings.step_size
        worker.LOG.debug('Sent to queue: %s - %s' % (ts, url))
        worker.QUEUE.put('%s|%s' % (ts, url))
    sleep(1)