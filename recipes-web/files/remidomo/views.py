import os
from subprocess import PIPE, Popen
from django.shortcuts import render
import logging
import re


def get_own_version():
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(os.path.dirname(__file__), '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

def get_service_version():
    try:
        output = Popen(["remidomo.py", "--version"], stdout=PIPE).communicate()[0]
        return output
    except OSError:
        logging.getLogger('django').error('Failed to get service version')
        return '?'

def about(request):
    context = { 'service_version': get_service_version(),
                'web_version': get_own_version() }
    return render(request, 'about.html', context)