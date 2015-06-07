import datetime
import dateutil.tz
import json

from django.http import HttpResponse
from django.shortcuts import render
from models import Mesure

# TODO: Read those from config... (but when ?)
SENSORS = ('terrasse', 'salon')

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

def programmation(request):
    context = {}
    return render(request, 'prog.html', context)

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
