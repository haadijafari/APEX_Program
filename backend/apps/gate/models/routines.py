from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Max
from django.utils.translation import gettext_lazy as _


class Routine(models.Model):
    """
    Holds a collection of routine items, e.g., "Morning Routine"
    or "Evening Routine", linked to a specific user.
    """

    # Link to the user who owns this routine
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routines"
    )

    # The name of the routine
    name = models.CharField(
        max_length=100,
        verbose_name=_("Routine Name"),
        help_text=_("e.g., 'Morning Routine', 'Workout', 'Evening Wind-down'"),
    )

    # Is this routine currently in use?
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Uncheck this to archive or hide this routine."),
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Routine")
        verbose_name_plural = _("Routines")
        # Ensure a user cannot have two routines with the same name
        unique_together = ["user", "name"]
        ordering = ["name"]

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
        "gate.Routine", on_delete=models.CASCADE, related_name="routine_items"
    )

    # --- Fields for the dynamic item ---
    title = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        verbose_name=_("Title"),
        help_text=_(
            "What is the routine item? (e.g., 'Brushing Teeth', 'Meditate 10 mins')"
        ),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Any extra details about the item (optional)"),
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    priority = models.PositiveIntegerField(
        # We allow it to be blank, then set the default in the save() method
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Priority"),
        help_text=_(
            "Priority order (lower numbers come first). Leave blank to add to the end."
        ),
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Routine Item")
        verbose_name_plural = _("Routine Items")
        # Order items by priority (lowest number first),
        # then by creation time (oldest first)
        ordering = ["priority", "created_at"]

    def __str__(self):
        # Removed the 'if self.priority == 100' as 100 is no longer the default
        return f"{self.priority} | {self.title}"

    def save(self, *args, **kwargs):
        # --- Capitalize Title ---
        if self.title:
            self.title = self.title.strip().title()

        # --- Priority Standardize ---
        # Start an atomic block to ensure database integrity during reordering
        with transaction.atomic():
            if self.pk is None:
                # --- CREATE NEW ITEM ---
                # Calculate priority: put it at the end if not specified
                if self.priority is None:
                    # Get the current max priority
                    max_p = RoutineItem.objects.filter(routine=self.routine).aggregate(
                        Max("priority")
                    )["priority__max"]
                    self.priority = (max_p or 0) + 1
                else:
                    # Insert in middle: Shift existing items down
                    RoutineItem.objects.filter(
                        routine=self.routine, priority__gte=self.priority
                    ).update(priority=F("priority") + 1)

            else:
                # --- UPDATE EXISTING ITEM ---
                try:
                    old_instance = RoutineItem.objects.get(pk=self.pk)
                except RoutineItem.DoesNotExist:
                    # Should not happen, but fallback
                    super().save(*args, **kwargs)
                    return

                # 1. Handle Changing Routines (e.g: Moving item from Morning to Evening)
                if old_instance.routine != self.routine:
                    # Step A: Close the gap in the OLD routine
                    RoutineItem.objects.filter(
                        routine=old_instance.routine, priority__gt=old_instance.priority
                    ).update(priority=F("priority") - 1)

                    # Step B: Handle placement in NEW routine
                    if self.priority is None:
                        # User didn't specify where, put at end
                        max_p = RoutineItem.objects.filter(
                            routine=self.routine
                        ).aggregate(Max("priority"))["priority__max"]
                        self.priority = (max_p or 0) + 1
                    else:
                        # User specified a slot, shift others down to make room
                        RoutineItem.objects.filter(
                            routine=self.routine, priority__gte=self.priority
                        ).update(priority=F("priority") + 1)

                # 2. Handle Reordering within same Routine
                elif old_instance.priority != self.priority:
                    # Fix: If user enters 'None' on edit, move to end
                    if self.priority is None:
                        max_p = RoutineItem.objects.filter(
                            routine=self.routine
                        ).aggregate(Max("priority"))["priority__max"]
                        self.priority = (max_p or 0) + 1

                    # If moving UP (e.g. 5 -> 2)
                    if self.priority < old_instance.priority:
                        RoutineItem.objects.filter(
                            routine=self.routine,
                            priority__gte=self.priority,
                            priority__lt=old_instance.priority,
                        ).update(priority=F("priority") + 1)

                    # If moving DOWN (e.g. 2 -> 5)
                    else:
                        RoutineItem.objects.filter(
                            routine=self.routine,
                            priority__gt=old_instance.priority,
                            priority__lte=self.priority,
                        ).update(priority=F("priority") - 1)

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete to close the gap left by the deleted item.
        """
        current_priority = self.priority
        current_routine = self.routine

        with transaction.atomic():
            super().delete(*args, **kwargs)
            # Shift everything below this item up by 1
            RoutineItem.objects.filter(
                routine=current_routine, priority__gt=current_priority
            ).update(priority=F("priority") - 1)
