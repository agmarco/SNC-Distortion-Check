from django.db import models


class Scan(models.Model):
    dicom_archive = models.FileField(upload_to='scan_dicom')
    processing = models.BooleanField(default=False)
    errors = models.TextField(null=True)
    result = models.TextField(null=True)
