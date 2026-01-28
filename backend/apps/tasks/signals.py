from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.profiles.models import PlayerStats
from apps.tasks.models import TaskLog


# Signal for DO action
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


# Signal for UNDO action
@receiver(post_delete, sender=TaskLog)
def handle_task_undo(sender, instance, **kwargs):
    """
    Triggered when a TaskLog is deleted (Task undone).
    Revokes XP/Stats from the user's profile.
    """
    with transaction.atomic():
        # Edge case: If the Task itself was deleted, we might lose access to profile.
        # But usually 'undoing' a checkbox just deletes the Log, not the Task.
        try:
            task = instance.task
            profile = task.profile
        except Exception:
            # If task or profile is gone, nothing to revert
            return

        # --- 1. Revert Profile XP (Level Down) ---
        xp_to_remove = instance.xp_earned
        profile.xp_current -= xp_to_remove

        # Handle Level Down if XP goes negative
        while profile.xp_current < 0:
            if profile.level <= 1:
                profile.level = 1
                profile.xp_current = 0
                break

            # Drop a level
            profile.level -= 1
            # Add the capacity of the *lower* level to the negative balance
            # (e.g., -10 XP + 50 XP Max = 40 XP in the lower level)
            profile.xp_current += profile.xp_required

        profile.save()

        # --- 2. Revert Stats ---
        stats = profile.stats
        # Note: Uses current task stats. If task changed stats between check/uncheck,
        # this might be slightly inaccurate, but it's the best proxy we have.
        rewards = task.xp_distribution

        for stat_key, xp_amount in rewards.items():
            revoke_stat_xp(stats, stat_key, xp_amount)

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


# Helper for Revoking XP
def revoke_stat_xp(stats: PlayerStats, stat_key: str, amount: int):
    """
    Helper to remove XP from a specific stat and handle de-leveling.
    """
    prefix = stat_key.lower()
    level_field = f"{prefix}_level"
    xp_field = f"{prefix}_xp"

    if not hasattr(stats, level_field) or not hasattr(stats, xp_field):
        return

    current_level = getattr(stats, level_field)
    current_xp = getattr(stats, xp_field)

    current_xp -= amount

    # Handle De-Leveling
    while current_xp < 0:
        if current_level <= 1:
            current_level = 1
            current_xp = 0
            break

        current_level -= 1
        # Get requirement of the *new* (lower) level to add back
        req_xp = stats.get_xp_required(current_level)
        current_xp += req_xp

    setattr(stats, level_field, current_level)
    setattr(stats, xp_field, current_xp)
