from django.conf.urls import url, include

from . import views
from . import api
from ..urls import uidb64_pattern, token_pattern

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^register/done/$', views.RegisterDoneView.as_view(), name='register_done'),
    url(r'^create-password/(?P<uidb64>' + uidb64_pattern + r')/(?P<token>' + token_pattern + r')/$',
        views.CreatePasswordView.as_view(), name='create_password'),
    url(r'^create-password/complete/$', views.CreatePasswordCompleteView.as_view(), name='create_password_complete'),

    url(r'^terms-of-use/$', views.TermsOfUseView.as_view(), name='terms_of_use'),
    url(r'^privacy-policy/$', views.PrivacyPolicyView.as_view(), name='privacy_policy'),

    url(r'^$', views.LandingView.as_view(), name='landing'),
    url(r'^configuration/$', views.ConfigurationView.as_view(), name='configuration'),
    url(r'^account/$', views.AccountView.as_view(), name='account'),
    url(r'^machine-sequences/(?P<pk>\d+)/$', views.MachineSequenceDetailView.as_view(), name='machine_sequence_detail'),

    url(r'^api/', include([
        url(r'^validate-serial/$', api.ValidateSerialView.as_view(), name='validate_serial'),
        url(r'^update-tolerance/$', api.UpdateToleranceView.as_view(), name='update_tolerance'),
        url(r'^poll-scans/$', api.PollScansView.as_view(), name='poll_scans'),
        url(r'^poll-ct/$', api.PollCtView.as_view(), name='poll_ct'),
        url(r'^sign-s3/$', api.SignS3View.as_view(), name='sign_s3'),
        url(r'^upload-as-dev/$', api.UploadAsDev.as_view(), name='upload_as_dev'),
    ])),

    url(r'^scans/', include([
        url(r'^add/$', views.UploadScanView.as_view(), name='upload_scan'),
        url(r'^(?P<pk>\d+)/delete/$', views.DeleteScanView.as_view(), name='delete_scan'),
        url(r'^(?P<pk>\d+)/errors/$', views.ScanErrorsView.as_view(), name='scan_errors'),
        url(r'^(?P<pk>\d+)/dicom-overlay/$', views.DicomOverlayView.as_view(), name='dicom_overlay'),
        url(r'^(?P<pk>\d+)/dicom-overlay/success/$', views.DicomOverlaySuccessView.as_view(), name='dicom_overlay_success'),
        url(r'^(?P<pk>\d+)/refresh/$', views.refresh_scan_view, name='refresh_scan'),
    ])),

    url(r'^phantoms/', include([
        url(r'^add/$', views.CreatePhantomView.as_view(), name='create_phantom'),
        url(r'^(?P<phantom_pk>\d+)/edit/$', views.UpdatePhantomView.as_view(), name='update_phantom'),
        url(r'^(?P<phantom_pk>\d+)/delete/$', views.DeletePhantomView.as_view(), name='delete_phantom'),

        url(r'^(?P<phantom_pk>\d+)/gold-standards/', include([
            url(r'^upload-ct/$', views.UploadCtView.as_view(), name='upload_ct'),
            url(r'^upload-raw/$', views.UploadRawView.as_view(), name='upload_raw'),
            url(r'^(?P<gold_standard_pk>\d+)/delete/$', views.DeleteGoldStandardView.as_view(), name='delete_gold_standard'),
            url(r'^(?P<gold_standard_pk>\d+)/activate/$', views.ActivateGoldStandardView.as_view(), name='activate_gold_standard'),
            url(r'^(?P<gold_standard_pk>\d+)/csv/$', views.GoldStandardCsvView.as_view(), name='gold_standard_csv'),
            url(r'^(?P<gold_standard_pk>\d+)/errors/$', views.GoldStandardErrorsView.as_view(), name='gold_standard_errors'),
        ])),
    ])),

    url(r'^machines/', include([
        url(r'^add/$', views.CreateMachineView.as_view(), name='create_machine'),
        url(r'^(?P<pk>\d+)/edit/$', views.UpdateMachineView.as_view(), name='update_machine'),
        url(r'^(?P<pk>\d+)/delete/$', views.DeleteMachineView.as_view(), name='delete_machine'),
    ])),

    url(r'^sequences/', include([
        url(r'^add/$', views.CreateSequenceView.as_view(), name='create_sequence'),
        url(r'^(?P<pk>\d+)/edit/$', views.UpdateSequenceView.as_view(), name='update_sequence'),
        url(r'^(?P<pk>\d+)/delete/$', views.DeleteSequenceView.as_view(), name='delete_sequence'),
    ])),

    url(r'^users/', include([
        url(r'^add/$', views.CreateUserView.as_view(), name='create_user'),
        url(r'^(?P<pk>\d+)/delete/$', views.DeleteUserView.as_view(), name='delete_user'),
    ])),

    url(r'^fake-server-error/$', views.fake_server_error, name='fake_server_error'),
]
