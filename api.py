#! coding: utf-8
# pylint: disable-msg=W0311

from time import time
from pymongo import Connection as MongoDB
from redis import Redis
from ast import literal_eval

import settings

DATABASE = MongoDB(settings.mongod).log
DATABASE.response_time.ensure_index([('timestamp', -1)], background=True)
DATABASE.response_time.ensure_index('url', background=True)
CACHE = Redis()

def set_cache(key, value, expires=60):
  CACHE.set(key, value)
  CACHE.expire(key, expires)
  return True

def get_cache(key):
  value = CACHE.get(key)
  if value:
    return literal_eval(value)

def flush_cache(key):
  return CACHE.delete(key)


def save(info):
  """info = {'timestamp': 1315884726, 'Total': 0.005, 'TTFB': 0.005, 'Connect': 0.004},"""
  record = DATABASE.response_time.find_one({'url': info['url'], 'timestamp': info['timestamp']})
  if record:
    return False
  else:
    DATABASE.response_time.insert(info)
  return True


def fetch(url, start, end):
  key = '%s:%s-%s' % (url, start, end)
  records = get_cache(key)
  if not records:
    while end % settings.step_size != 0:
      end -= 1
      start -= 1
      
    mod = [settings.step_size, 0]
    if (end - start) / 1440 > 5:    # 1440 points = 3600 * 2 / 5
      mod = [(end - start) / 1440, 0]
      
      while end % mod[0] != 0:
        end -= 1
        start -= 1
    
      records =  DATABASE.response_time.find({'url': url,
                                              '$and': [
                                                       {'timestamp': {'$gte': start}},
                                                       {'timestamp': {'$lt': end}},
                                                       {'timestamp': {'$mod': mod}}
                                                      ]
                                              })
    else:
      records =  DATABASE.response_time.find({'url': url,
                                              '$and': [
                                                       {'timestamp': {'$gte': start}},
                                                       {'timestamp': {'$lt': end}}
                                                      ]
                                              })
   
      
    records = list(records)
    
    # fix missing records
    timestamp_list = [record.get('timestamp') for record in records]   
    
    for ts in range(start, end, mod[0]):
      if ts not in timestamp_list:
        records.append({'timestamp': ts})
    
    records = sorted(records, key=lambda k: k['timestamp'])
    print len(records)
    
    set_cache(key, records)
        
  return records

def get_urls():
  key = 'urls'
  urls = get_cache(key)
  if not urls:
    urls = [i['url'] for i in DATABASE['urls'].find()]
    set_cache(key, urls)
  return urls

def get_keys():
  key = 'keys'
  keys = get_cache(key)
  if not keys:
    sample_record = DATABASE.response_time.find_one()
    keys = ["date"]
    sample_record_keys = sample_record.keys()
    for k in sample_record_keys:
      if k not in ['_id', 'timestamp', 'url']:
        keys.append(k)
    set_cache(key, keys, expires=86400)
  return keys

def get_urls_and_hostname():
  """ list of urls included hostname """
  key = 'urls+hostname'
  urls = get_cache(key)
  if not urls:
    urls = [{'url': i['url'],
             'hostname': i.get('hostname')} for i in DATABASE['urls'].find()]
    set_cache(key, urls)
  return urls
  
  

def add_url(url, hostname=None):
  if DATABASE.urls.find_one({'url': url}):
    return False
  else:
    flush_cache('urls')
    DATABASE.urls.insert({'url': url, 
                          'timestamp': time(),
                          'hostname': hostname})    
    return True

def remove_url(url):
  flush_cache('urls')
  DATABASE.urls.remove({'url': url})
  return True





