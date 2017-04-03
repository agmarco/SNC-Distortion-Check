from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Phantom, GoldenFiducials, Fiducials


@receiver(post_save, sender=Phantom, dispatch_uid='phantom_post_save')
def phantom_post_save(sender, instance, created, **kwargs):
    if created:

        # create a golden fiducials object that points to the phantom model's CAD fiducials
        GoldenFiducials.objects.create(
            phantom=instance,
            fiducials=Fiducials.objects.create(fiducials=instance.model.cad_fiducials.fiducials),
            type=GoldenFiducials.CAD,
            is_active=True,
        )
