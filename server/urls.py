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
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

admin.site.site_header = 'CIRS Distortion Check Admin'

uidb64_pattern = r'[0-9A-Za-z_\-]+'
token_pattern = r'[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20}'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
    url(r'^password-reset/$', auth_views.PasswordResetView.as_view(), name='password_reset'),
    url(r'^password-reset/done/$', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^password-reset/confirm/(?P<uidb64>' + uidb64_pattern + r')/(?P<token>' + token_pattern + r')/$',
        auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^password-reset/complete/$', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    url(r'^', include('server.common.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    import debug_toolbar

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
