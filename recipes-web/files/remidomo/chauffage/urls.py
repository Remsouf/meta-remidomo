from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$', views.status, name='status'),
    url(r'status/', views.status, name='status'),
    url(r'^program/post', views.program_post, name='programmation-edit'),
    url(r'^program/', views.program, name='programmation'),
    url(r'^graph/data/([a-z]+)', views.data, name='data'),
    url(r'^graph/([a-z]+)', views.graph, name='graphe'),
    url(r'^config/post', views.config_post, name='configuration-edit'),
    url(r'^config/', views.config, name='configuration'),
)
