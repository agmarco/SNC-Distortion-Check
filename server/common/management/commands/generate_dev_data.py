from django.core.management.base import BaseCommand, CommandError

from server.common.factories import UserFactory, GroupFactory


class Command(BaseCommand):
    help = 'Load some test data into the database.'

    def handle(self, *args, **options):
        medical_physicists = GroupFactory.create(name='medical_physicists')
        therapists = GroupFactory.create(name='therapists')

        admin = UserFactory.create(
            username="admin",
            is_staff=True,
            is_superuser=True
        )

        medical_physicist = UserFactory.create(
            username="medical_physicist",
            groups=[medical_physicists],
        )

        therapist = UserFactory.create(
            username="therapist",
            groups=[therapists],
        )
