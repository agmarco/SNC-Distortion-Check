from django.core.management.base import BaseCommand, CommandError

from server.common.factories import UserFactory, GroupFactory, InstitutionFactory


class Command(BaseCommand):
    help = 'Load some test data into the database.'

    def handle(self, *args, **options):
        medical_physicists = GroupFactory.create(name='medical_physicists')
        therapists = GroupFactory.create(name='therapists')

        admin = UserFactory.create(
            username="admin",
            email="admin@cirs.com",
            first_name="admin",
            last_name="cirs",
            is_staff=True,
            is_superuser=True
        )

        john_hopkins = InstitutionFactory.create(name='John Hopkins')

        medical_physicist = UserFactory.create(
            username="medical_physicist",
            first_name="Mary",
            last_name="Jane",
            email="mary.jane@johnhopkins.edu",
            institution=john_hopkins,
            groups=[medical_physicists],
        )

        therapist = UserFactory.create(
            username="therapist",
            first_name="John",
            last_name="Doe",
            email="john.doe@johnhopkins.edu",
            institution=john_hopkins,
            groups=[therapists],
        )
