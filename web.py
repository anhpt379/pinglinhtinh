#! coding: utf-8
# pylint: disable-msg=W0311

from flask import Flask, render_template, make_response, request
from mimetypes import guess_type
from hashlib import md5
from urlparse import urlparse

import api

app = Flask('Realtime-Monitoring')


@app.template_filter('md5sum')
def md5sum(value):
  return md5(value).hexdigest()


@app.route("/public/<path:filename>")
def public_files(filename):
  path = 'public/' + filename
  filedata = open(path).read()
  response = make_response(filedata)
  response.headers['Content-Length'] = len(filedata)
  response.headers['Content-Type'] = guess_type(filename)[0]
  return response

from time import time
from random import randint

@app.route('/i')
def interactive_version():
  return render_template('interactive_version.html', urls=api.get_urls())

@app.route('/data.js')
def dataset():
  url = request.args.get('url')
  current_ts = int(time())
  start = current_ts - 3600 * 2
  end = current_ts
  records = []
  keys = api.get_keys()
  data = api.fetch(url, start, end)

  for i in data:
    record = [i.get('timestamp', ''), 
              i.get('connect', ''), 
              i.get('ttfb', ''),
              i.get('total', '')]
    records.append(record)
  
  return render_template('data.js', records=records, url=url, keys=keys)

@app.route('/')
def main():
  urls = api.get_urls()
  domains = [urlparse(url).netloc for url in urls]
  domains = set(domains)
  return render_template('home.html', urls=urls, domains=domains)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')