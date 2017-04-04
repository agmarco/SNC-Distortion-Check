from django.conf.urls import url, include

from . import views
from . import api

urlpatterns = [
    url(r'^api/', include([
        url(r'^validate-serial/$', api.ValidateSerial.as_view(), name='validate_serial'),
    ])),

    url(r'^$', views.landing, name='landing'),
    url(r'^configuration/$', views.Configuration.as_view(), name='configuration'),
    url(r'^machine-sequences/$', views.machine_sequences, name='machine_sequences'),
    url(r'^machine-sequences/(?P<pk>\d+)/$', views.MachineSequenceDetail.as_view(), name='machine_sequence_detail'),
    url(r'^upload-scan/$', views.UploadScan.as_view(), name='upload_scan'),
    url(r'^upload-scan/(?P<pk>\d+)/error/$', views.UploadScanErrors.as_view(), name='upload_scan_errors'),

    url(r'^phantoms/', include([
        url(r'^add/$', views.CreatePhantom.as_view(), name='create_phantom'),
        url(r'^(?P<phantom_pk>\d+)/edit/$', views.UpdatePhantom.as_view(), name='update_phantom'),
        url(r'^(?P<phantom_pk>\d+)/delete/$', views.DeletePhantom.as_view(), name='delete_phantom'),

        url(r'^(?P<phantom_pk>\d+)/gold-standards/', include([
            url(r'^upload-ct/$', views.UploadCT.as_view(), name='upload_ct'),
            url(r'^upload-raw/$', views.UploadRaw.as_view(), name='upload_raw'),
            url(r'^(?P<gold_standard_pk>\d+)/delete/$', views.DeleteGoldStandard.as_view(), name='delete_gold_standard'),
            url(r'^(?P<gold_standard_pk>\d+)/activate/$', views.activate_gold_standard, name='activate_gold_standard'),
            url(r'^(?P<gold_standard_pk>\d+)/csv/$', views.gold_standard_csv, name='gold_standard_csv'),
        ])),
    ])),

    url(r'^machines/', include([
        url(r'^add/$', views.CreateMachine.as_view(), name='create_machine'),
        url(r'^(?P<pk>\d+)/edit/$', views.UpdateMachine.as_view(), name='update_machine'),
        url(r'^(?P<pk>\d+)/delete/$', views.DeleteMachine.as_view(), name='delete_machine'),
    ])),

    url(r'^sequences/', include([
        url(r'^add/$', views.CreateSequence.as_view(), name='create_sequence'),
        url(r'^(?P<pk>\d+)/edit/$', views.UpdateSequence.as_view(), name='update_sequence'),
        url(r'^(?P<pk>\d+)/delete/$', views.DeleteSequence.as_view(), name='delete_sequence'),
    ])),

    url(r'^users/', include([
        url(r'^add/$', views.CreateUser.as_view(), name='create_user'),
        url(r'^(?P<pk>\d+)/delete/$', views.DeleteUser.as_view(), name='delete_user'),
    ])),
]
