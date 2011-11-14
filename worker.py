#! coding: utf-8
# pylint: disable-msg=W0311
from commands import getoutput
from hotqueue import HotQueue
from time import time, sleep
from threading import Thread
from functools import wraps

import api
import settings
import logging
formatter = logging.Formatter(
  '(%(asctime)-6s) %(levelname)s: %(message)s' + '\n' + '-' * 80)

console_logger = logging.StreamHandler()
console_logger.setLevel(logging.DEBUG)
console_logger.setFormatter(formatter)
logging.getLogger('').addHandler(console_logger)

file_logger = logging.FileHandler(filename='errors.log')
file_logger.setLevel(logging.ERROR)
file_logger.setFormatter(formatter)
logging.getLogger('').addHandler(file_logger)

LOG = logging.getLogger('MFS')
LOG.setLevel(logging.DEBUG)


QUEUE = HotQueue("urls", host=settings.queue.split(':')[0],
                         port=int(settings.queue.split(':')[1]),
                         db=int(settings.queue.split(':')[2]))
def async(func):
  @wraps(func)
  def async_func(*args, **kwargs):
    func_hl = Thread(target = func, args = args, kwargs = kwargs)
    func_hl.start()
    return func_hl
  return async_func

@async
def check(url): 
  at, url, hostname = url.split('|') 
  at = int(at)
  while True:
    current_ts = int(time())
    if current_ts < at:
      sleep(0.2)
    elif current_ts > at:
      LOG.debug('Aborted: %s - %s' % (at, url))
      return False
    else:
      break
  if hostname:
    cmd = 'curl -o /dev/null -w "connect:%{time_connect}\tttfb:%{time_starttransfer}\ttotal:%{time_total} \n" -H "Host: ' + hostname + '" '  + url
  else:
    cmd = 'curl -o /dev/null -w "connect:%{time_connect}\tttfb:%{time_starttransfer}\ttotal:%{time_total} \n" ' + url
  LOG.debug(cmd)
  output = getoutput(cmd)
  data = output.split('\n')[-1].split()
  info = dict()
  for i in data:
    key, value = i.split(':')
    info[key] = float(value)
  info['url'] = url
  info['timestamp'] = at
  LOG.debug('Saved: %s - %s' % (current_ts, url))
  api.save(info)
  return True

@QUEUE.worker
def run(url):
  check(url)
  LOG.debug('Started: %s' % url)
  return True

if __name__ == '__main__':
  run()