import os
from subprocess import PIPE, Popen
from django.shortcuts import render
import logging
import re

SERVICE_LOGFILE = '/var/log/remidomo.log'
DJANGO_LOGFILE = ''
FASTCGI_LOGFILE = ''
NGINX_ERROR_LOGFILE = '/var/log/nginx-error.log'
NGINX_ACCESS_LOGFILE = '/var/log/nginx-access.log'

# Methods to retrieve version numbers
def get_own_version():
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(os.path.dirname(__file__), '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

def get_service_version():
    try:
        output = Popen(['remidomo.py', '--version'], stdout=PIPE).communicate()[0]
        return output
    except OSError:
        logging.getLogger('django').error('Failed to get service version')
        return '?'

# Method to retrieve log files
def get_log(path, name):
    try:
        if os.path.getsize(path) == 0:
            return '<Journal vide>'
        with open(path, 'r') as file:
            return file.read()
    except IOError:
        logging.getLogger('django').error('Failed to read %s log' % name)
        return 'Impossible de lire "%s"' % path
    except OSError:
        logging.getLogger('django').error('Failed to read %s log from %s' % (name, path))
        return '<Pas de journal>'

# Views
def about(request):
    context = { 'service_version': get_service_version(),
                'web_version': get_own_version() }
    return render(request, 'about.html', context)

def logs(request):
    context = { 'service_log': get_log(SERVICE_LOGFILE, 'service'),
                'django_log': get_log('', 'Django'),
                'nginx_error_log': get_log(NGINX_ERROR_LOGFILE, 'nginx error'),
                'nginx_access_log': get_log(NGINX_ACCESS_LOGFILE, 'nginx access')}
    return render(request, 'logs.html', context)
