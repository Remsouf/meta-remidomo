import json
import os
from subprocess import PIPE, Popen
import datetime
import dateutil
from dateutil.parser import parse
from dateutil.tz import tzlocal
import django
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
import logging
import re
import itertools
import sys
from models import Mesure

sys.path.append('../../recipes-service/files')
sys.path.append('/usr/lib/remidomo/service')
from config import Config
from orders import Order, Override

SERVICE_LOGFILE = '/var/log/remidomo.log'
NGINX_ERROR_LOGFILE = '/var/log/nginx-error.log'
NGINX_ACCESS_LOGFILE = '/var/log/nginx-access.log'
CONFIG_FILE = '/etc/remidomo.xml'
SERVICE_PID_FILE = '/var/run/remidomo.pid'

# Enum-like strings for the DB 'type' column
DB_TYPE_TEMP = 'temp'
DB_TYPE_POWER = 'power'
DB_TYPE_HUMIDITY = 'humidity'


# Methods to retrieve version numbers
def __get_own_version():
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(os.path.dirname(__file__), '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def __get_service_version():
    try:
        output = Popen(['remidomo.py', '--version'], stdout=PIPE).communicate()[0]
        return output
    except OSError:
        logging.getLogger('django').error('Failed to get service version')
        return '?'


def __elapsed_time(timestamp):
    delta = datetime.datetime.now(timestamp.tzinfo) - timestamp

    if delta.total_seconds() < 30:
        return "A l'instant"
    elif delta.total_seconds() < 60:
        return 'Il y a %ds' % delta.total_seconds()
    elif delta.total_seconds() < 60 * 60:
        return 'Il y a %dmin' % (delta.total_seconds() / 60)
    elif delta.total_seconds() < 24 * 60 * 60:
        return 'Il y a %dh' % (delta.total_seconds() / (60 * 60))
    else:
        return 'Il y a %dj' % delta.days


def __python_date_to_js(timestamp):
    return 'Date(%d,%d,%d,%d,%d,%d)' % (timestamp.year,
                                        timestamp.month - 1,  # 0-based
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
    conf = Config(logging.getLogger('django'))
    try:
        conf.read_file(CONFIG_FILE)
        return conf
    except IOError:
        return None


# Method to retrieve log files
def __get_log(path, name):
    try:
        if os.path.getsize(path) == 0:
            return '<Journal vide>'
        with open(path, 'r') as inf:
            return inf.read()
    except IOError:
        logging.getLogger('django').error('Failed to read %s log' % name)
        return 'Impossible de lire "%s"' % path
    except OSError:
        logging.getLogger('django').error('Failed to read %s log from %s' % (name, path))
        return '<Pas de journal>'


# Views
def about(request):
    context = {'service_version': __get_service_version(),
               'web_version': __get_own_version(),
               'fwk_version': django.get_version()}
    return render(request, 'about.html', context)


def logs(request):
    context = {'service_log': __get_log(SERVICE_LOGFILE, 'service'),
               'nginx_error_log': __get_log(NGINX_ERROR_LOGFILE, 'nginx error'),
               'nginx_access_log': __get_log(NGINX_ACCESS_LOGFILE, 'nginx access')}
    return render(request, 'logs.html', context)


def status(request):
    conf = __get_config()
    if conf is not None:
        names = conf.get_temp_sensor_names()
        power_name = conf.get_power_sensors().keys()[0]
    else:
        names = list()
        power_name = ''

    # Temperature sensors
    temp_data = []
    for sensor_name in names:
        rows = Mesure.objects.filter(name=sensor_name).filter(type=DB_TYPE_TEMP).order_by('-timestamp')[:1]
        if rows is None or len(rows) == 0:
            current_temp = ''
            since_when = '?'
        else:
            current_temp = rows[0].value
            since_when = __elapsed_time(rows[0].timestamp)
        temp_data.append({'name': sensor_name.capitalize(),
                          'temp': current_temp,
                          'since_when': since_when})

    # Humidity sensors
    humidity_data = []
    for sensor_name in names:
        rows = Mesure.objects.filter(name=sensor_name).filter(type=DB_TYPE_HUMIDITY).order_by('-timestamp')[:1]
        if rows is None or len(rows) == 0:
            current_humidity = ''
            since_when = '?'
        else:
            current_humidity = rows[0].value
            since_when = __elapsed_time(rows[0].timestamp)
        humidity_data.append({'name': sensor_name.capitalize(),
                              'humidity': current_humidity,
                              'since_when': since_when})

    # Power sensor
    rows = Mesure.objects.filter(name=power_name).filter(type=DB_TYPE_POWER).order_by('-timestamp')[:1]
    if rows is None or len(rows) == 0:
        current_power = ''
        since_when = '?'
    else:
        current_power = rows[0].value
        since_when = __elapsed_time(rows[0].timestamp)

    # Override
    if conf:
        override_applied = conf.get_override_for(datetime.datetime.now()) is not None
    else:
        override_applied = False

    power_data = {'name': power_name.capitalize(),
                  'power': current_power,
                  'since_when': since_when}

    context = {'temperature': temp_data,
               'humidity': humidity_data,
               'power': power_data,
               'override_applied': override_applied}
    return render(request, 'status.html', context)


@login_required
def program(request):
    week_data = []

    conf = __get_config()
    for index, day in enumerate(conf.get_day_names()):
        if conf is None:
            schedule = None
        else:
            schedule = conf.get_schedule(index)
        week_data.append({'name': day,
                          'schedule': schedule})

    context = {'days': week_data,
               'heating_enabled': conf.is_heating_enabled(),
               'iterator': itertools.count()}
    return render(request, 'program.html', context)


@login_required
def program_post(request):
    conf = __get_config()
    if conf is None:
        # Not having a config file is acceptable here
        conf = Config(logging.getLogger('django'))

    if request.is_ajax():
        json_items = request.POST.get('items', None)
        if json_items is None:
            return HttpResponse(json.dumps(dict(status='Pas de calendrier')), content_type='application/json')

        items = None
        try:
            items = json.loads(json_items)
        except ValueError:
            return HttpResponse(json.dumps(dict(status='Donnees invalides: %s' % items)),
                                content_type='application/json')

        conf.clear_schedules()
        for time_range in items:
            day_index = time_range['group'] - 1
            start_time = parse(time_range['start']).time()
            end_time = parse(time_range['end']).time()
            value = float(time_range['content'])

            order = Order(start_time, end_time, value)
            conf.add_order(day_index, order)

        heating_enabled = request.POST.get('heating_enabled', False)
        if heating_enabled == 'true':
            conf.set_heating_enabled(True)
        else:
            conf.set_heating_enabled(False)

        # Once done, save config file and restart service
        conf.save(CONFIG_FILE)

        return HttpResponse(json.dumps(dict(status='updated')), content_type='application/json')
    else:
        return HttpResponse(json.dumps(dict(status='Not Ajax')), content_type='application/json')


@login_required
def override_post(request):
    conf = __get_config()
    if conf is None:
        # Not having a config file is acceptable here
        conf = Config(logging.getLogger('django'))

    if request.is_ajax():
        json_end_time = request.POST.get('end_time', None)
        if json_end_time is None:
            return HttpResponse(json.dumps(dict(status='Pas de date/heure')), content_type='application/json')

        try:
            end_time = json.loads(json_end_time)
        except ValueError:
            return HttpResponse(json.dumps(dict(status='Date/heure invalide : %s' % json_end_time)),
                                content_type='application/json')

        json_value = request.POST.get('value', None)
        if json_value is None:
            return HttpResponse(json.dumps(dict(status='Pas de consigne')), content_type='application/json')

        try:
            value = float(json.loads(json_value))
        except ValueError:
            return HttpResponse(json.dumps(dict(status='Consigne invalide : %s' % json_value)),
                                content_type='application/json')

        conf.clear_override()

        # Express in our local TZ and remove tzinfo -> make date naive
        begin = datetime.datetime.now()
        end = parse(end_time)
        end = end.astimezone(dateutil.tz.tzlocal()).replace(tzinfo=None)
        override = Override(begin, end, value)
        conf.set_override(override)

        # Once done, save config file and restart service
        conf.save(CONFIG_FILE)

        return HttpResponse(json.dumps(dict(status='updated')), content_type='application/json')
    else:
        return HttpResponse(json.dumps(dict(status='Not Ajax')), content_type='application/json')


@login_required
def override_clear(request):
    conf = __get_config()
    if conf is None:
        # Not having a config file is acceptable here
        conf = Config(logging.getLogger('django'))

    if request.is_ajax():
        conf.clear_override()
        conf.save(CONFIG_FILE)

        return HttpResponse(json.dumps(dict(status='cleared')), content_type='application/json')
    else:
        return HttpResponse(json.dumps(dict(status='Not Ajax')), content_type='application/json')


def graph(request, dataset_name, db_type):
    local_tz = tzlocal()
    local_offset = local_tz.utcoffset(datetime.datetime.now(local_tz))
    local_offset_hours = local_offset.total_seconds() / 3600

    conf = __get_config()

    show_setpoint = dataset_name == 'all' or conf.get_temp_sensor_id(dataset_name) is not None

    # Default range
    range_nb = 5
    range_units = 'jours'
    if dataset_name == 'all':
        if conf is not None:
            names = conf.get_temp_sensor_names()
        else:
            names = list()
    else:
        names = list()
        names.append(dataset_name)

    if db_type == DB_TYPE_TEMP:
        units = '\u00B0C'
    elif db_type == DB_TYPE_POWER:
        units = 'kW'
    elif db_type == DB_TYPE_HUMIDITY:
        units = '%'
    else:
        units = ''

    context = {'names': names,
               'dataset_name': dataset_name,
               'time_offset': local_offset_hours,
               'units': units,
               'show_setpoint': show_setpoint,
               'range_nb': range_nb,
               'range_units': range_units,
               'db_type': db_type}
    return render(request, 'graph.html', context)


def config(request):
    conf = __get_config()
    if conf is None:
        # Not having a config file is acceptable here
        conf = Config(logging.getLogger('django'))

    # Assume we have only one power sensor here
    if len(conf.get_power_sensors()) > 0:
        elec_name = conf.get_power_sensors().keys()[0]
        elec_addr = conf.get_power_sensors().values()[0]
    else:
        elec_name = ''
        elec_addr = ''

    elec = {'name': elec_name,
            'addr': elec_addr}

    context = {'rfxport': conf.get_rfxlan_port(),
               'sensors': conf.get_temp_sensors(),
               'pos_hysteresis': conf.get_hysteresis_over(),
               'neg_hysteresis': conf.get_hysteresis_under(),
               'ref_sensor': conf.get_heating_sensor_name(),
               'elec': elec}
    return render(request, 'config.html', context)


def config_post(request):
    conf = __get_config()
    if conf is None:
        # Not having a config file is acceptable here
        conf = Config(logging.getLogger('django'))

    if request.is_ajax():
        json_sensors = request.POST.get('sensors', None)
        conf.clear_temp_sensors()
        if json_sensors is not None:
            sensors = None
            try:
                sensors = json.loads(json_sensors)
                for sensor in sensors:
                    conf.add_temp_sensor(sensor['name'], sensor['addr'])

                    if sensor['is_ref']:
                        conf.set_heating_sensor_name(sensor['name'])

            except ValueError:
                return HttpResponse(json.dumps(dict(status='Donnees capteurs temperature invalides: %s' % sensors)),
                                    content_type='application/json')

        json_power = request.POST.get('elec', None)
        conf.clear_power_sensors()
        if json_power is not None:
            power = None
            try:
                power = json.loads(json_power)
                conf.add_power_sensor(power['name'], power['addr'])
            except ValueError:
                return HttpResponse(json.dumps(dict(status='Donnees capteurs energie invalides: %s' % power)),
                                    content_type='application/json')

        port = request.POST.get('rfxport', None)
        if port is not None:
            conf.set_rfxlan_port(port)

        hysteresis_over = request.POST.get('pos_hysteresis', None)
        if hysteresis_over is not None:
            conf.set_hysteresis_over(hysteresis_over)

        hysteresis_under = request.POST.get('neg_hysteresis', None)
        if hysteresis_under is not None:
            conf.set_hysteresis_under(hysteresis_under)

        # Once done, save config file
        conf.save(CONFIG_FILE)

        return HttpResponse(json.dumps(dict(status='updated')), content_type='application/json')
    else:
        return HttpResponse(json.dumps(dict(status='Not Ajax')), content_type='application/json')


def data(_, name, db_type):
    """
    Return graph data in JSON format
    """
    js_cols = [{'label': 'dates', 'type': 'datetime'}]

    conf = __get_config()
    if conf is None:
        # Not having a config file is acceptable here
        conf = Config(logging.getLogger('django'))

    # Don't show temp. setpoint if graph is energy related
    show_setpoint = name == 'all' or conf.get_temp_sensor_id(name) is not None
    if show_setpoint:
        js_cols.append({'label': 'Consigne', 'type': 'number'})

    now = datetime.datetime.now()
    order = conf.get_order_for(now)
    if order is None:
        consigne = 0
    else:
        consigne = order.get_value()

    if name == 'all':
        if conf is not None:
            names = conf.get_temp_sensor_names()
        else:
            names = list()

        rows = Mesure.objects.filter(type=db_type).order_by('timestamp')
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
                if show_setpoint:
                    data_array.append({'v': consigne})
                for value in current_values:
                    data_array.append({'v': value})
                js_rows.append({'c': data_array})

    else:

        rows = Mesure.objects.filter(name=name).filter(type=db_type).order_by('timestamp')
        js_cols.append({'label': name.capitalize(), 'type': 'number'})

        js_rows = []
        for row in rows:
            data_array = [{'v': __python_date_to_js(row.timestamp)}]
            if show_setpoint:
                data_array.append({'v': consigne})
            data_array.append({'v': row.value})
            js_rows.append({'c': data_array})

    js_data = {'cols': js_cols, 'rows': js_rows}
    return HttpResponse(json.dumps(js_data), content_type="application/json")


def login(request):
    """
    Login view
    """
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = auth.authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                print "User %s logged in successfully." % username
                auth.login(request, user)
                return HttpResponseRedirect('/status/')  # request.POST['next'])
            else:
                # An inactive account was used - no logging in !
                return render_to_response('denied.html',
                                          {'reason': 'Le compte est d&eacute;sactiv&eaccute;.'},
                                          context)
        else:
            # Bad login details were provided. So we can't log the user in.
            print "User %s not logged in, wrong credentials" % username
            return render_to_response('denied.html',
                                      {'reason': "Le nom d'utilisateur ou le mot de passe sont invalides."},
                                      context)

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('login.html', {'next': request.GET['next']}, context)


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/status/')
