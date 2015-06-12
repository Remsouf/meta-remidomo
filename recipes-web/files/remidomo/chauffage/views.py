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
    config = __get_config()
    if config is not None:
        names = config.get_sensor_names()
    else:
        names = list()

    sensor_data = []
    for sensor_name in names:
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
    week_data = []

    config = __get_config()
    for index, day in enumerate(config.get_day_names()):
        if config is None:
            schedule = None
        else:
            schedule = config.get_schedule(index)
        week_data.append({'name': day,
                          'schedule' : schedule})

    context = { 'days': week_data,
                'iterator': itertools.count()}
    return render(request, 'program.html', context)

def program_post(request):
    config = __get_config()
    if config is None:
        # Not having a config file is acceptable here
        config = Config(logging.getLogger('django'))

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

        return HttpResponse(json.dumps(dict(status='updated')), content_type='application/json')
    else:
        return HttpResponse(json.dumps(dict(status='Not Ajax')), content_type='application/json')

def graph(request, dataset_name):
    local_tz = dateutil.tz.tzlocal()
    local_offset = local_tz.utcoffset(datetime.datetime.now(local_tz))
    local_offset_hours = local_offset.total_seconds() / 3600

    if dataset_name == 'all':
        config = __get_config()
        if config is not None:
            names = config.get_sensor_names()
        else:
            names = list()
    else:
        names = list()
        names.append(dataset_name)

    context = { 'names': names,
                'dataset_name': dataset_name,
                'time_offset': local_offset_hours }
    return render(request, 'graph.html', context)

def config(request):
    config = __get_config()
    if config is None:
        # Not having a config file is acceptable here
        config = Config(logging.getLogger('django'))

    context = { 'rfxport': config.get_rfxlan_port(),
                'sensors': config.get_sensors(),
                'pos_hysteresis': config.get_hysteresis_over(),
                'neg_hysteresis': config.get_hysteresis_under(),
                'ref_sensor': config.get_heating_sensor_name(),
              }
    return render(request, 'config.html', context)

def config_post(request):
    config = __get_config()
    if config is None:
        # Not having a config file is acceptable here
        config = Config(logging.getLogger('django'))

    if request.is_ajax():
        json_sensors = request.POST.get('sensors', None)
        config.clear_sensors()
        if json_sensors is not None:
            try:
                sensors = json.loads(json_sensors)
                for sensor in sensors:
                    config.add_sensor(sensor['name'], sensor['addr'])

                    if sensor['is_ref']:
                        config.set_heating_sensor_name(sensor['name'])

            except ValueError:
                return HttpResponse(json.dumps(dict(status='Donnees capteurs invalides: %s' % sensors)), content_type='application/json')

        port = request.POST.get('rfxport', None)
        if port is not None:
            config.set_rfxlan_port(port)

        hysteresis_over = request.POST.get('pos_hysteresis', None)
        if hysteresis_over is not None:
            config.set_hysteresis_over(hysteresis_over)

        hysteresis_under = request.POST.get('neg_hysteresis', None)
        if hysteresis_under is not None:
            config.set_hysteresis_under(hysteresis_under)

        # Once done, save config file
        config.save(CONFIG_FILE)

        return HttpResponse(json.dumps(dict(status='updated')), content_type='application/json')
    else:
        return HttpResponse(json.dumps(dict(status='Not Ajax')), content_type='application/json')

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

def __get_config():
    config = Config(logging.getLogger('django'))
    try:
        config.read_file(CONFIG_FILE)
        return config
    except IOError:
        return None

"""
Return graph data in JSON format
"""
def data(request, name):
    config = __get_config()
    if config is not None:
        names = config.get_sensor_names()
    else:
        names = list()

    js_cols = [{'label':'dates', 'type':'datetime'}]

    if name == 'all':
        rows = Mesure.objects.order_by('timestamp')
        for sensor_name in names:
            js_cols.append({'label': sensor_name.capitalize(), 'type': 'number'})

        # We need to generate a timeline which 'merges' data for all sensors
        js_rows = []
        current_values = [None] * len(names)
        for row in rows:
            # Remember value for this sensor
            # If sensor is mentioned in DB but not in config, skip
            if row.name not in names:
                continue

            index = names.index(row.name)
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
