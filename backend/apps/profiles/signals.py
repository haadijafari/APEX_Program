from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import PlayerProfile, PlayerStats


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # 1. Create the Profile
        profile = PlayerProfile.objects.create(user=instance)
        # 2. Create the PlayerStats
        PlayerStats.objects.create(profile=profile)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
