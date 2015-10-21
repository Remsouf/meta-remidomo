from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import views

urlpatterns = patterns('',
    url(r'^$', views.status, name='status'),

    url(r'^about/', views.about, name='about'),
    url(r'^logs/', views.logs, name='logs'),
    url(r'^admin/', include(admin.site.urls)),

    url(r'status/', views.status, name='status'),
    url(r'^override/post', views.override_post, name='override-edit'),
    url(r'^override/clear', views.override_clear, name='override-clear'),
    url(r'^program/post', views.program_post, name='programmation-edit'),
    url(r'^program/', views.program, name='programmation'),
    url(r'^graph/data/([a-z]+)/([a-z]+)', views.data, name='data'),
    url(r'^graph/([a-z]+)/([a-z]+)', views.graph, name='graphe'),
    url(r'^config/post', views.config_post, name='configuration-edit'),
    url(r'^config/', views.config, name='configuration'),
)

