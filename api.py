#! coding: utf-8
# pylint: disable-msg=W0311

from time import time
from pymongo import Connection as MongoDB

import settings

DATABASE = MongoDB(settings.mongod).log
DATABASE.response_time.ensure_index([('timestamp', -1)], background=True)
DATABASE.response_time.ensure_index('url', background=True)


def save(info):
  """info = {'timestamp': 1315884726, 'Total': 0.005, 'TTFB': 0.005, 'Connect': 0.004},"""
  record = DATABASE.response_time.find_one({'url': info['url'], 'timestamp': info['timestamp']})
  if record:
    return False
  else:
    DATABASE.response_time.insert(info)
  return True


def fetch(url, start, end):
  while end % settings.step_size != 0:
    end -= 1
    start -= 1
    
  records =  DATABASE.response_time.find({'url': url,
                                             '$and': [{'timestamp': {'$gte': start}},
                                                      {'timestamp': {'$lt': end}}]})
  records = list(records)
  # fix missing records
  timestamp_list = [record.get('timestamp') for record in records]
  for ts in range(start, end, settings.step_size):
    if ts not in timestamp_list:
      records.append({'timestamp': ts})
  
  records = sorted(records, key=lambda k: k['timestamp'])
  return records

def get_urls():
  return [i['url'] for i in DATABASE['urls'].find()]

def get_keys():
  sample_record = DATABASE.response_time.find_one()
  keys = ["date"]
  sample_record_keys = sample_record.keys()
  for k in sample_record_keys:
    if k not in ['_id', 'timestamp', 'url']:
      keys.append(k)
  return keys

def add_urls(urls):
  if isinstance(urls, str):
    urls = [urls]
    
  for url in urls:
    DATABASE['urls'].update({'url': url}, 
                            {'$set': {'timestamp': time()}}, 
                            upsert=True)    
  return True



