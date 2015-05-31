from django.shortcuts import render

def status(request):
    context = {'temperature_ext': 45.6,
               'ilya_ext': '25 s',
               'temperature_int': 22.2,
               'ilya_int': '25 min' }
    return render(request, 'status.html', context)

def programmation(request):
    context = {}
    return render(request, 'prog.html', context)
