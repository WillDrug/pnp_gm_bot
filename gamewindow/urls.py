from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^', views.index, name='index', kwargs={'parm1': 'test'}),
]