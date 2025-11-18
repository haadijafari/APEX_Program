from django.db import models, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Routine(models.Model):
    """
    Holds a collection of routine items, e.g., "Morning Routine"
    or "Evening Routine", linked to a specific user.
    """
    
    # Link to the user who owns this routine
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='routines'
    )
    
    # The name of the routine
    name = models.CharField(
        max_length=100,
        verbose_name=_("Routine Name"),
        help_text=_("e.g., 'Morning Routine', 'Workout', 'Evening Wind-down'")
    )
    
    # Is this routine currently in use?
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Uncheck this to archive or hide this routine.")
    )
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Routine")
        verbose_name_plural = _("Routines")
        # Ensure a user cannot have two routines with the same name
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Clean up the name before saving
        if self.name:
            self.name = self.name.strip().title()
        super().save(*args, **kwargs)


class RoutineItem(models.Model):
    """
    Represents a single, user-defined item in the morning routine
    for a specific Routine.
    """
    
    # This is now a ForeignKey, because one Routine
    # will have *many* routine items.
    routine = models.ForeignKey(
        'daily.Routine', 
        on_delete=models.CASCADE, 
        related_name='routine_items' 
    )
    
    # --- Fields for the dynamic item ---
    title = models.CharField(
        max_length=255,
        blank=False, 
        null=False,
        # removed 'required=True' as it's not a valid model field option
        help_text=_("What is the routine item? (e.g., 'Brushing Teeth', 'Meditate 10 mins')")
    )
    
    description = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Any extra details about the item (optional)")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    priority = models.PositiveIntegerField(
        # We allow it to be blank, then set the default in the save() method
        null=True, 
        blank=True,
        help_text=_("Priority order (lower numbers come first). Leave blank to add to the end.")
    )
    
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Routine Item")
        verbose_name_plural = _("Routine Items")
        # Order items by priority (lowest number first), 
        # then by creation time (oldest first)
        ordering = ['priority', 'created_at']

    def __str__(self):
        # Removed the 'if self.priority == 100' as 100 is no longer the default
        return f"{self.priority} | {self.title}"

    def save(self, *args, **kwargs):
        # --- Capitalize Title ---
        if self.title:
            self.title = self.title.strip().title()

        # --- Priority Standardize ---
        # Get all other items for this routine
        qs = RoutineItem.objects.filter(routine=self.routine)
        
        if self.pk is not None:
            # This is an existing item, remove it from query
            qs = qs.exclude(pk=self.pk)

        if self.pk is None:
            # --- This is a NEW item ---
            
            # Handle "consecutive" logic (force gaps closed)
            count = qs.count()
            
            # This is the new "default" logic you asked for.
            # If priority wasn't provided (is None) or is out of bounds,
            # set it to the end of the list.
            if self.priority is None or self.priority > count:
                self.priority = count
            
            # (If priority *was* provided and is valid, the 'items_to_shift'
            # logic below will handle it)

            with transaction.atomic():
                # Handle "duplicates" (shift items down)
                # Get items with priority >= new item's priority
                # and lock them for update.
                items_to_shift = qs.filter(
                    priority__gte=self.priority
                ).select_for_update()
                
                # Shift them down by 1 in a single, safe query
                items_to_shift.update(priority=F('priority') + 1)
                
                # Now save the new item
                super().save(*args, **kwargs)
        
        else:
            # --- This is an EXISTING item ---
            try:
                # We need the old_self *before* any changes
                old_self = RoutineItem.objects.get(pk=self.pk)
            except RoutineItem.DoesNotExist:
                super().save(*args, **kwargs) # Should not happen, but safe
                return

            if old_self.priority == self.priority:
                # Priority didn't change, just save and exit
                super().save(*args, **kwargs)
                return

            # Priority *did* change. This is a "move".
            # The safest way to handle this and enforce consecutive logic
            # is to re-number *everything* for this plan.
            
            with transaction.atomic():
                # First, save the change (so self.priority is updated)
                super().save(*args, **kwargs) 
                
                # Now, renumber *all* items for this plan
                # This enforces the "consecutive" logic
                
                # Re-fetch the queryset *including* the just-saved item
                all_items = RoutineItem.objects.filter(routine=self.routine)
                items = all_items.order_by('priority', 'created_at').select_for_update()
                
                # Loop and re-save.
                for i, item in enumerate(items):
                    if item.priority != i:
                        # Use update() to avoid re-triggering this save() method
                        RoutineItem.objects.filter(pk=item.pk).update(priority=i)
