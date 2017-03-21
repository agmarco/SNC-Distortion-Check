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
    url(r'^phantoms/add/$', views.add_phantom, name='add_phantom'),
    url(r'^phantoms/edit/(\d+)/$', views.edit_phantom, name='edit_phantom'),
    url(r'^phantoms/delete/(\d+)/$', views.delete_phantom, name='delete_phantom'),
    url(r'^machines/add/$', views.add_machine, name='add_machine'),
    url(r'^machines/edit/(\d+)/$', views.edit_machine, name='edit_machine'),
    url(r'^machines/delete/(\d+)/$', views.delete_machine, name='delete_machine'),
    url(r'^sequences/add/$', views.add_sequence, name='add_sequence'),
    url(r'^sequences/edit/(\d+)/$', views.edit_sequence, name='edit_sequence'),
    url(r'^sequences/delete/(\d+)/$', views.delete_sequence, name='delete_sequence'),
    url(r'^users/add/$', views.add_user, name='add_user'),
    url(r'^users/edit/(\d+)/$', views.edit_user, name='edit_user'),
    url(r'^users/delete/(\d+)/$', views.delete_user, name='delete_user'),
    url(r'^$', views.upload_file),
]
