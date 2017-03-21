"""cirs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from server.common import views

admin.site.site_header = 'CIRS Distortion Check Admin'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^configuration/$', views.configuration, name='configuration'),

    url(r'^phantoms/add/$', views.CreatePhantom.as_view(), name='create_phantom'),
    url(r'^phantoms/edit/(?P<pk>\d+)/$', views.UpdatePhantom.as_view(), name='update_phantom'),
    url(r'^phantoms/delete/(?P<pk>\d+)/$', views.DeletePhantom.as_view(), name='delete_phantom'),

    url(r'^machines/add/$', views.CreateMachine.as_view(), name='create_machine'),
    url(r'^machines/edit/(?P<pk>\d+)/$', views.UpdateMachine.as_view(), name='update_machine'),
    url(r'^machines/delete/(?P<pk>\d+)/$', views.DeleteMachine.as_view(), name='delete_machine'),

    url(r'^sequences/add/$', views.CreateSequence.as_view(), name='create_sequence'),
    url(r'^sequences/edit/(?P<pk>\d+)/$', views.UpdateSequence.as_view(), name='update_sequence'),
    url(r'^sequences/delete/(?P<pk>\d+)/$', views.DeleteSequence.as_view(), name='delete_sequence'),

    url(r'^users/add/$', views.create_user, name='create_user'),
    url(r'^users/edit/(\d+)/$', views.update_user, name='update_user'),
    url(r'^users/delete/(\d+)/$', views.delete_user, name='delete_user'),

    url(r'^$', views.upload_file),
]
