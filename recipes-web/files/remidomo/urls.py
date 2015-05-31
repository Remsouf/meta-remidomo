from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

import views

urlpatterns = patterns('',
    url(r'^chauffage/', include('remidomo.chauffage.urls')),
    url(r'^about/', views.about, name='about'),
    url(r'^logs/', views.logs, name='logs'),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', RedirectView.as_view(url='chauffage/status', permanent=False), name='index'),
)

