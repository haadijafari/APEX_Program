from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    pass


class PlayerProfile(models.Model):
    """
    Holds the 'Meta' stats: Level, Rank, Gold, Job.
    Attributes are now in a separate model.
    """
    
    class Rank(models.TextChoices):
        E_RANK = 'E', 'E-Rank'
        D_RANK = 'D', 'D-Rank'
        C_RANK = 'C', 'C-Rank'
        B_RANK = 'B', 'B-Rank'
        A_RANK = 'A', 'A-Rank'
        S_RANK = 'S', 'S-Rank'
        NATIONAL = 'SS', 'National Level'

    # Link directly to the User in this same file
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # --- Status ---
    level = models.PositiveIntegerField(default=1)
    xp_current = models.PositiveIntegerField(default=0)
    
    rank = models.CharField(
        max_length=2,
        choices=Rank.choices,
        default=Rank.E_RANK
    )
    
    job_class = models.CharField(
        max_length=50, 
        default="None",
        help_text=_("e.g. Shadow Monarch, Developer, Artist")
    )

    gold = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Level {self.level} | {self.user.username}"

    @property
    def xp_max(self):
        return self.level * 100

    @property
    def xp_percent(self):
        if self.xp_max == 0: return 0
        return min(100, int((self.xp_current / self.xp_max) * 100))


class UserAttribute(models.Model):
    """
    Dynamic stats. The user can have 'Strength', 'Python', 'Charisma', etc.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attributes'
    )
    
    name = models.CharField(max_length=50) # e.g. "Intellect"
    value = models.PositiveIntegerField(default=10)
    description = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['user', 'name'] # Can't have two "Strength" stats
        ordering = ['name']

    def __str__(self):
        return f"{self.name}: {self.value}"


# --- Signals ---
@receiver(post_save, sender=User)
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
            UserAttribute.objects.create(
                user=instance,
                name=stat_name,
                value=10,
                description=desc
            )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
