from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import PlayerProfile, PlayerStats


# --- Signals ---
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # 1. Create the Profile
        PlayerProfile.objects.create(user=instance)

        # 2. Create Default "Owj" Attributes (Optional starter pack) - Solo Leveling Inspired
        default_stats = [
            ("Physic", "Physical and Health Status"),
            ("Discipline", "Consistency, Routine adherence, and Focus"),
            ("Intellect", "Education, Knowledge, and Wisdom"),
            ("Creativity", "Startups, Brand, Music, Art"),
            ("Charisma", "Critical hit chance"),
        ]

        for stat_name, desc in default_stats:
            PlayerStats.objects.create(
                user=instance, name=stat_name, value=10, description=desc
            )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
