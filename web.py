#! coding: utf-8
# pylint: disable-msg=W0311

from flask import Flask, render_template, make_response, request
from mimetypes import guess_type
from hashlib import md5
from time import time
from datetime import datetime
from simplejson import dumps

import api
import settings

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
  response.headers['Cache-Control'] = 'max-age=86400'
  return response


@app.route('/data.js')
def dataset():
  url = request.args.get('url')  
  offset = request.args.get('offset')
  skip = request.args.get('skip').rstrip('+')
  
  cookie_key = 'ts_%s' % md5(url).hexdigest()  
  start = end = None
  
  current_ts = int(time())
  if not offset:
    ts = request.args.get(cookie_key)
    if not ts:
      ts = request.cookies.get(cookie_key)
    
    if ts:
      start = int(ts)
      while start % settings.step_size != 0:
        start += 1
  
  if not start:
    start = current_ts - int(offset)
  end = current_ts
  records = []
  keys = api.get_keys()
  data = api.fetch(url, start, end)  
  
  for i in data:
    if i.get('total') > float(skip):  # skip if larger than 100ms
      record = [int(i.get('timestamp')), '', '', '']
    else:
      if i.get('code', 200) == 200:
        record = [int(i.get('timestamp')), 
                  abs(float(i.get('connect'))) * 100 if i.has_key('connect') else '', 
                  abs(float(i.get('ttfb'))) * 100 if i.has_key('ttfb') else '', 
                  abs(float(i.get('total'))) * 100 if i.has_key('total') else '']
      else:        
        record = [int(i.get('timestamp')), 
                  abs(float(i.get('connect'))) * -100 if i.has_key('connect') else '', 
                  abs(float(i.get('ttfb'))) * -100 if i.has_key('ttfb') else '', 
                  abs(float(i.get('total'))) * -100 if i.has_key('total') else '']
    ts = datetime.fromtimestamp(record[0]).isoformat()
    record.pop(0)
    record.insert(0, 'new Date("%s+07:00")' % ts)
      
    records.append(record)
  
  code = render_template('data.js', 
                         records=records, 
                         url=url, 
                         keys=keys, 
                         offset=offset)
  resp = make_response(code)
  resp.set_cookie(cookie_key, int(time()))

  resp.headers['Content-Type'] = 'text/javascript'
  resp.headers['Content-Length'] = len(code)
  resp.headers['Cache-Control'] = 'max-age=60'
  return resp

@app.route('/')
def main():
  offset = request.args.get('offset', 15 * 60)
  offset = int(offset)
  url = request.args.get('url')
  domain = request.args.get('domain')
  skip = request.args.get('skip', 10)
  if url:
    urls = [api.get_info(url)]
    domains = [url.lstrip('http://').split('/')[0].split(':')[0]]
  elif domain:
    domains = [domain]
    urls = [info for info in api.get_urls_and_hostname() if domain in info.get('url')]
  else:
    urls = api.get_urls_and_hostname()
    domains = [info.get('url').lstrip('http://').split('/')[0].split(':')[0] for info in urls]
    
    
    # remove port from domain if domain is ip
    domains = [i if ':' not in i else i.split(':')[0] for i in domains if i]
    
    domains = list(set(domains))
    domains.sort()
    
    # only display 1 url per domain
    short_list = []
    for domain in domains:
      for info in urls:
        if domain in info.get('url'):
          short_list.append(info)
          break
    urls = short_list
  return render_template('home.html', 
                         urls=urls, 
                         domains=domains, 
                         offset=offset,
                         skip=skip)


@app.route("/preferences")
def preferences():
  """
  Add new url, group
  Remove existed urls
  """
  passcode = request.cookies.get('passcode')
  if passcode != settings.passcode:
    return render_template('enter_passcode.html')
  
  action = request.args.get('action')  
  url = request.args.get('url')
  hostname = request.args.get('hostname')
  
  if action == 'remove':
    state = api.remove_url(url)
    if state is True:
      return md5(url).hexdigest()
    else:
      return ''
  elif action == 'add':
    state = api.add_url(url, hostname)
    if state is True:
      return dumps({"id": md5(url).hexdigest(),
                    "url": url,
                    "hostname": hostname})
    else:
      return ''
  else:
    urls = api.get_urls_and_hostname()
    urls.reverse()
    return render_template('preferences.html', urls=urls)

import werkzeug.serving
@werkzeug.serving.run_with_reloader
def cherrypy_server():
  app.debug = True
  from cherrypy import wsgiserver
  server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 5000), app)
  try:
    server.start()
  except KeyboardInterrupt:
    server.stop()

if __name__ == '__main__':
#  app.run(debug=True, host='0.0.0.0')
  cherrypy_server
  
  
  