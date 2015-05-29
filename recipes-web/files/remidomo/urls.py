from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

import views

urlpatterns = patterns('',
    url(r'^chauffage/', include('remidomo.chauffage.urls')),
    url(r'^about/', views.about, name='about'),
    url(r'^admin/', include(admin.site.urls)),

    # Map / to chauffage for now
    url(r'^$', RedirectView.as_view(url='chauffage/', permanent=False), name='index'),
)

