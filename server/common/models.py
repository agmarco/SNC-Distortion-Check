from django.db import models


class Scan(models.Model):
    dicom_archive = models.FileField(upload_to='scan_dicom')
