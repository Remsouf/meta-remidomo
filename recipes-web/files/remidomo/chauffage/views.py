import datetime
import logging
import os
import dateutil.tz, dateutil.parser
import json
import sys

from django.http import HttpResponse
from django.shortcuts import render
import itertools
import signal
from models import Mesure

sys.path.append('../../recipes-service/files')
sys.path.append('/usr/lib/remidomo/service')
from config import Config
from orders import Order

# TODO: Read those from config... (but when ?)
SENSORS = ('terrasse', 'salon')

CONFIG_FILE = '/etc/remidomo.xml'
SERVICE_PID_FILE = '/var/run/remidomo.pid'

def __elapsed_time(timestamp):
    delta = datetime.datetime.now(timestamp.tzinfo) - timestamp

    if delta.total_seconds() < 30:
        return "A l'instant"
    elif delta.total_seconds() < 60:
        return 'Il y a %ds' % delta.total_seconds()
    elif delta.total_seconds() < 60*60:
        return 'Il y a %dmin' % (delta.total_seconds() / 60)
    elif delta.total_seconds() < 24*60*60:
        return 'Il y a %dh' % (delta.total_seconds() / (60*60))
    else:
        return 'Il y a %dj' % delta.days

def status(request):
    sensor_data = []
    for sensor_name in SENSORS:
        rows = Mesure.objects.filter(name=sensor_name).order_by('-timestamp')
        if rows is None or len(rows) == 0:
            current_temp = '?'
            since_when = ''
        else:
            current_temp = rows[0].value
            since_when = __elapsed_time(rows[0].timestamp)
        sensor_data.append({'name': sensor_name.capitalize(),
                            'temp': current_temp,
                            'since_when': since_when})

    context = {'data': sensor_data}
    return render(request, 'status.html', context)

def program(request):
    config = Config(logging.getLogger('django'))

    week_data = []

    try:
        config.read_file(CONFIG_FILE)

        for index, day in enumerate(config.get_day_names()):
            week_data.append({'name': day,
                              'schedule' : config.get_schedule(index)})
    except IOError:
        for day in config.get_day_names():
            week_data.append({'name': day,
                              'schedule' : None})

    context = { 'days': week_data,
                'iterator': itertools.count()}
    return render(request, 'program.html', context)

def program_post(request):
    config = Config(logging.getLogger('django'))
    config.read_file(CONFIG_FILE)

    if request.is_ajax():
        json_items = request.POST.get('items', None)
        if json_items is None:
            return HttpResponse(json.dumps(dict(status='Pas de calendrier')), content_type='application/json')

        try:
            items = json.loads(json_items)
        except ValueError:
            return HttpResponse(json.dumps(dict(status='Donnees invalides: %s' % items)), content_type='application/json')

        config.clear_schedules()
        for time_range in items:
            day_index = time_range['group'] - 1
            start_time = dateutil.parser.parse(time_range['start']).time()
            end_time = dateutil.parser.parse(time_range['end']).time()
            value = float(time_range['content'])

            order = Order(start_time, end_time, value)
            config.add_order(day_index, order)

        # Once done, save config file and restart service
        config.save(CONFIG_FILE)
        service_pid = __get_service_pid()
        if service_pid is None:
            return HttpResponse(json.dumps(dict(status='Service down')), content_type='application/json')

        logging.getLogger('django').info('Sending SIGHUP to pid %d' % service_pid)
        try:
            os.kill(service_pid, signal.SIGHUP)
        except OSError, e:
            logging.getLogger('django').error('Failed reloading service configuration : %s' % e.strerror)
            return HttpResponse(json.dumps(dict(status='Service PID not consistent')), content_type='application/json')

        return HttpResponse(json.dumps(dict(status='updated')), content_type='application/json')
    else:
        return HttpResponse(json.dumps(dict(status='Not Ajax')), content_type='application/json')

def graph(request, dataset_name):
    local_tz = dateutil.tz.tzlocal()
    local_offset = local_tz.utcoffset(datetime.datetime.now(local_tz))
    local_offset_hours = local_offset.total_seconds() / 3600

    if dataset_name == 'all':
        names = SENSORS
    else:
        names = list()
        names.append(dataset_name)

    context = { 'names': names,
                'dataset_name': dataset_name,
                'time_offset': local_offset_hours }
    return render(request, 'graph.html', context)

def __python_date_to_js(timestamp):
    return 'Date(%d,%d,%d,%d,%d,%d)' % (timestamp.year,
                                        timestamp.month,
                                        timestamp.day,
                                        timestamp.hour,
                                        timestamp.minute,
                                        timestamp.second)

def __get_service_pid():
    try:
        with open(SERVICE_PID_FILE, 'r') as f:
            lines = f.readlines()
            pid = int(lines[0].strip())
            return pid
    except IOError, e:
        logging.getLogger('django').error('Failed to get service PID : %s', e.strerror)
        return None

"""
Return graph data in JSON format
"""
def data(request, name):

    js_cols = [{'label':'dates', 'type':'datetime'}]

    if name == 'all':
        rows = Mesure.objects.order_by('timestamp')
        for sensor_name in SENSORS:
            js_cols.append({'label': sensor_name.capitalize(), 'type': 'number'})

        # We need to generate a timeline which 'merges' data for all sensors
        js_rows = []
        current_values = [None] * len(SENSORS)
        for row in rows:
            # Remember value for this sensor
            index = SENSORS.index(row.name)
            current_values[index] = row.value

            # Values known for all sensors ? Then go ahead
            if None not in current_values:
                data_array = [{'v': __python_date_to_js(row.timestamp)}]
                for value in current_values:
                    data_array.append({'v': value})
                js_rows.append({'c': data_array})

    else:
        rows = Mesure.objects.filter(name=name).order_by('timestamp')
        js_cols.append({'label': name.capitalize(), 'type': 'number'})

        js_rows = []
        for row in rows:
            couple = {'c': [{'v': __python_date_to_js(row.timestamp)}, {'v': row.value}]}
            js_rows.append(couple)

    js_data = {'cols': js_cols, 'rows': js_rows}
    return HttpResponse(json.dumps(js_data), content_type="application/json")
