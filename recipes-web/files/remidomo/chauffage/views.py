import datetime
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
