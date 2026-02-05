from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.gate.models import DailyEntry


@receiver(post_save, sender=DailyEntry)
@receiver(post_delete, sender=DailyEntry)
def invalidate_index_cache(sender, instance, **kwargs):
    """
    Clears the main dashboard cache whenever a Daily Entry is created or updated.
    This ensures changes to Sleep, Diary, or Quotes are reflected immediately.
    """
    user_id = instance.user.id
    today = timezone.now().date()

    cache_key = f"gate_index_context_{user_id}_{today}"
    cache.delete(cache_key)
