import fabric

# Define sets of servers as roles
fabric.api.env.roledefs = {
  'production'   : [
                    '192.168.6.206',
#                    '192.168.6.160'
                ],
}

fabric.api.env.user = 'anhpt'
fabric.api.env.warn_only = True


@fabric.api.roles('production')
def update():
  print
  print "Uploading changes..."
  print
  
  
  fabric.contrib.project.rsync_project(remote_dir='/srv/',
                                       exclude=['.hg', '.git', '*.log', '*.pyc'])

##
#  Disable if using auto reloader in Flask
#
#  print
#  print "Reloading..."
#  print
#  fabric.contrib.files.sed('/home/Workspace/5works/src/settings.py', 'DEBUG = True', 'DEBUG = False')
#  fabric.api.run("supervisorctl -c /home/Workspace/5works/src/config/web.conf shutdown")
#  fabric.api.run("supervisord -c /home/Workspace/5works/src/config/web.conf")
