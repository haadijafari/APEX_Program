from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.profiles.models import PlayerProfile, PlayerStats
from apps.tasks.models import Task


@receiver(pre_save, sender=Task)
def handle_task_completion(sender, instance, **kwargs):
    """
    Checks if a task was just marked as completed.
    If so, award XP to the Profile and the specific Stats.
    """
    if instance.pk:
        try:
            old_instance = Task.objects.get(pk=instance.pk)
            was_completed = old_instance.is_completed
        except Task.DoesNotExist:
            was_completed = False
    else:
        was_completed = False

    # Check if it transitioned from Not Completed -> Completed
    if instance.is_completed and not was_completed:
        # 1. Set Timestamp
        instance.completed_at = timezone.now()

        # 2. Award Rewards
        profile = instance.profile
        process_task_rewards(profile, instance)


def process_task_rewards(profile: PlayerProfile, task: Task):
    """
    Distributes XP to the Profile and Stats.
    """
    # --- 1. General XP (Level Up Logic) ---
    xp_gain = task.xp_reward
    profile.xp_current += xp_gain

    # Check for Level Up
    while profile.xp_current >= profile.xp_required:
        profile.xp_current -= profile.xp_required
        profile.level += 1
        # TODO: Send a "Level Up!" notification here

    profile.save()

    # --- 2. Stat XP (Attribute Growth) ---
    # task.stat_rewards looks like: {'INT': 100, 'WIL': 50}
    stats = profile.stats
    rewards = task.stat_rewards or {}

    for stat_key, xp_amount in rewards.items():
        award_stat_xp(stats, stat_key, xp_amount)

    stats.save()


def award_stat_xp(stats: PlayerStats, stat_key: str, amount: int):
    """
    Generic function to add XP to a specific stat (STR, INT, etc)
    and handle stat leveling.
    """
    # Map 'INT' -> ('int_level', 'int_xp')
    prefix = stat_key.lower()  # str, int, cha...
    level_field = f"{prefix}_level"
    xp_field = f"{prefix}_xp"

    if not hasattr(stats, level_field) or not hasattr(stats, xp_field):
        return  # Invalid stat key in JSON

    # Get current values
    current_level = getattr(stats, level_field)
    current_xp = getattr(stats, xp_field)

    # Add XP
    current_xp += amount

    # Calculate Required XP for NEXT level
    # Formula: ceil(100 * (1.06^L) * L / 100) * 100
    # We use the method we defined in PlayerStats model
    required_xp = stats.get_xp_required(current_level)

    # Check for Level Up
    while current_xp >= required_xp:
        current_xp -= required_xp
        current_level += 1
        required_xp = stats.get_xp_required(current_level)

    # Save back
    setattr(stats, level_field, current_level)
    setattr(stats, xp_field, current_xp)


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
