from django.contrib import admin
from models import Mesure


class MesureAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'address', 'value', 'timestamp']

admin.site.register(Mesure, MesureAdmin)
