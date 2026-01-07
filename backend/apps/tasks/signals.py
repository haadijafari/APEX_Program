from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import PlayerStats

# Correct imports based on your new structure
from apps.tasks.models import TaskLog


@receiver(post_save, sender=TaskLog)
def handle_task_completion(sender, instance, created, **kwargs):
    """
    Triggered when a TaskLog is created (Task completed).
    Distributes XP/Stats to the user's profile.
    """
    if not created:
        return

    # Use atomic transaction to ensure Profile and Stats update together
    with transaction.atomic():
        task = instance.task
        profile = task.profile

        # --- 1. Snapshot the Rewards ---
        # We save the XP earned at this moment into the log for history
        xp_earned = task.xp_reward
        instance.xp_earned = xp_earned
        instance.save(update_fields=["xp_earned"])

        # --- 2. Update Profile (Level Up) ---
        profile.xp_current += xp_earned

        # Level Up Logic
        while profile.xp_current >= profile.xp_required:
            profile.xp_current -= profile.xp_required
            profile.level += 1
            # TODO: Add Notification logic here

        profile.save()

        # --- 3. Update Stats (Attribute Growth) ---
        # Uses the new 'xp_distribution' property: {'STR': 45, 'INT': 30}
        stats = profile.stats
        rewards = task.xp_distribution

        for stat_key, xp_amount in rewards.items():
            award_stat_xp(stats, stat_key, xp_amount)

        stats.save()


def award_stat_xp(stats: PlayerStats, stat_key: str, amount: int):
    """
    Helper to add XP to a specific stat (STR, INT, etc) and handle leveling.
    """
    prefix = stat_key.lower()  # STR -> str
    level_field = f"{prefix}_level"
    xp_field = f"{prefix}_xp"

    if not hasattr(stats, level_field) or not hasattr(stats, xp_field):
        return

    current_level = getattr(stats, level_field)
    current_xp = getattr(stats, xp_field)

    current_xp += amount

    # Calculate Required XP for NEXT level using the model's method
    required_xp = stats.get_xp_required(current_level)

    while current_xp >= required_xp:
        current_xp -= required_xp
        current_level += 1
        required_xp = stats.get_xp_required(current_level)

    setattr(stats, level_field, current_level)
    setattr(stats, xp_field, current_xp)
