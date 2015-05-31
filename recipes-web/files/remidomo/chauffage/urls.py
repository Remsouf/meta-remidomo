from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$', views.status, name='status'),
    url(r'status/', views.status, name='status'),
    url(r'^program/', views.programmation, name='programmation'),
)

