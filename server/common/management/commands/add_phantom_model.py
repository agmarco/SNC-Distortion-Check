from django.core.management.base import BaseCommand

from server.common import factories
from process.file_io import load_points


class Command(BaseCommand):
    help = 'This script is used to add a new phantom model to the database'

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('model_number')
        parser.add_argument('points_path')

    def handle(self, name, model_number, points_path, **options):
        cad_fiducials_603A = load_points(points_path)['points']
        factories.PhantomModelFactory(
            name=name,
            model_number=model_number,
            cad_fiducials__fiducials=cad_fiducials_603A,
        )
