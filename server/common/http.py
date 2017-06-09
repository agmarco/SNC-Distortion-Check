import csv

from django.http import HttpResponse


class CsvResponse(HttpResponse):
    def __init__(self, ndarray, filename="array.csv", *args, **kwargs):
        kwargs.setdefault('content_type', 'text/csv')
        super(CsvResponse, self).__init__(*args, **kwargs)
        self['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(self)
        for row in ndarray.T:
            writer.writerow(row)


class ZipResponse(HttpResponse):
    def __init__(self, zipfile, filename="archive.zip", *args, **kwargs):
        kwargs.setdefault('content_type', 'application/zip')
        super(ZipResponse, self).__init__(zipfile.getvalue(), *args, **kwargs)
        self['Content-Disposition'] = f'attachment; filename="{filename}"'
