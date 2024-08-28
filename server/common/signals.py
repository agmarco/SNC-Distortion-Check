from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Phantom, GoldenFiducials, Fiducials, Machine, Sequence


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


@receiver(post_save, sender=Machine, dispatch_uid='machine_post_save')
def machine_post_save(sender, instance, created, **kwargs):
    if instance.deleted:
        instance.machinesequencepair_set.update(deleted=True)


@receiver(post_save, sender=Sequence, dispatch_uid='sequence_post_save')
def sequence_post_save(sender, instance, created, **kwargs):
    if instance.deleted:
        instance.machinesequencepair_set.update(deleted=True)
