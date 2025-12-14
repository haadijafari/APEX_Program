from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    pass


class PlayerProfile(models.Model):
    """
    The RPG stats for the User.
    Now located inside the auths app for better cohesion.
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
        help_text=_("e.g. Assassin, Necromancer, Mage")
    )

    # --- The 6 Attributes (Hexagon Stats) ---
    strength = models.PositiveIntegerField(default=10, verbose_name="STR")
    agility = models.PositiveIntegerField(default=10, verbose_name="AGI")
    intellect = models.PositiveIntegerField(default=10, verbose_name="INT")
    vitality = models.PositiveIntegerField(default=10, verbose_name="VIT")
    perception = models.PositiveIntegerField(default=10, verbose_name="PER")
    luck = models.PositiveIntegerField(default=10, verbose_name="LUK")

    # --- Economy ---
    gold = models.PositiveIntegerField(default=0, help_text=_("Currency earned from tasks"))

    def __str__(self):
        return f"Level {self.level} | {self.user.username}"

    @property
    def xp_max(self):
        return self.level * 100

    @property
    def xp_percent(self):
        if self.xp_max == 0: return 0
        return min(100, int((self.xp_current / self.xp_max) * 100))

# --- Signals (Auto-create profile) ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PlayerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()