
# # from django.db import models
# # from django.contrib.contenttypes.fields import GenericForeignKey
# # from django.contrib.contenttypes.models import ContentType

# # from apps.activities.activity.models import Activity


# # class Call(models.Model):

# #     CALL_OUTCOME_CHOICES = [
# #         ("connected", "Connected"),
# #         ("no_answer", "No Answer"),
# #         ("busy", "Busy"),
# #         ("left_voicemail", "Left Voicemail"),
# #         ("wrong_number", "Wrong Number"),
# #         ("callback_requested", "Callback Requested"),
# #         ("not_interested", "Not Interested"),
# #         ("other", "Other"),
# #     ]

# #     # Link Call to the base Activity
# #     activity = models.OneToOneField(
# #         Activity,
# #         on_delete=models.CASCADE,
# #         related_name="call"
# #     )

# #     # -------------------------------------------------
# #     # Connected CRM object
# #     # -------------------------------------------------

# #     connected_content_type = models.ForeignKey(
# #         ContentType,
# #         on_delete=models.CASCADE,
# #         related_name="connected_calls"
# #     )

# #     connected_object_id = models.PositiveBigIntegerField()

# #     connected = GenericForeignKey(
# #         "connected_content_type",
# #         "connected_object_id"
# #     )

# #     # -------------------------------------------------
# #     # Call details
# #     # -------------------------------------------------

# #     call_outcome = models.CharField(
# #         max_length=50,
# #         choices=CALL_OUTCOME_CHOICES
# #     )

# #     # Duration stored in minutes
# #     duration = models.PositiveIntegerField(
# #         null=True,
# #         blank=True
# #     )

# #     date = models.DateField()

# #     time = models.TimeField()

# #     # -------------------------------------------------
# #     # Note
# #     # -------------------------------------------------

# #     note = models.TextField(
# #         blank=True
# #     )

# #     # -------------------------------------------------
# #     # Timestamps
# #     # -------------------------------------------------

# #     created_at = models.DateTimeField(
# #         auto_now_add=True
# #     )

# #     updated_at = models.DateTimeField(
# #         auto_now=True
# #     )

# #     def __str__(self):
# #         return f"Call - {self.date} {self.time}"


 
# from django.db import models 
# from django.contrib.contenttypes.fields import GenericForeignKey 
# from django.contrib.contenttypes.models import ContentType 
 
# from apps.activities.activity.models import Activity 
 
 
# class Call(models.Model): 
 
#     CALL_OUTCOME_CHOICES = [ 
#         ("connected", "Connected"), 
#         ("no_answer", "No Answer"), 
#         ("busy", "Busy"), 
#         ("left_voicemail", "Left Voicemail"), 
#         ("wrong_number", "Wrong Number"), 
#         ("callback_requested", "Callback Requested"), 
#         ("not_interested", "Not Interested"), 
#         ("other", "Other"), 
#     ] 
 
#     # Link Call to the base Activity 
#     activity = models.OneToOneField( 
#         Activity, 
#         on_delete=models.CASCADE, 
#         related_name="call" 
#     ) 
 
#     # ------------------------------------------------- 
#     # Connected CRM object 
#     # ------------------------------------------------- 
 
#     connected_content_type = models.ForeignKey( 
#         ContentType, 
#         on_delete=models.CASCADE, 
#         related_name="connected_calls" 
#     ) 
 
#     connected_object_id = models.PositiveBigIntegerField() 
 
#     connected = GenericForeignKey( 
#         "connected_content_type", 
#         "connected_object_id" 
#     ) 
 
#     # ------------------------------------------------- 
#     # Call details 
#     # ------------------------------------------------- 
 
#     call_outcome = models.CharField( 
#         max_length=50, 
#         choices=CALL_OUTCOME_CHOICES 
#     ) 
 
#     # Duration stored in minutes 
#     duration = models.PositiveIntegerField( 
#         null=True, 
#         blank=True 
#     ) 
 
#     date = models.DateField() 
 
#     time = models.TimeField() 
 
#     # ------------------------------------------------- 
#     # Note 
#     # ------------------------------------------------- 
 
#     note = models.TextField( 
#         blank=True 
#     ) 
 
#     # ------------------------------------------------- 
#     # Timestamps 
#     # ------------------------------------------------- 
 
#     created_at = models.DateTimeField( 
#         auto_now_add=True 
#     ) 
 
#     updated_at = models.DateTimeField( 
#         auto_now=True 
#     ) 
 
#     def __str__(self): 
#         return f"Call - {self.date} {self.time}" 


# from django.db import models
# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType


# class Call(models.Model):

#     CALL_OUTCOME_CHOICES = [
#         ("connected", "Connected"),
#         ("no_answer", "No Answer"),
#         ("busy", "Busy"),
#         ("left_voicemail", "Left Voicemail"),
#         ("wrong_number", "Wrong Number"),
#         ("callback_requested", "Callback Requested"),
#         ("not_interested", "Not Interested"),
#         ("other", "Other"),
#     ]

#     TWILIO_STATUS_CHOICES = [
#         ("queued", "Queued"),
#         ("initiated", "Initiated"),
#         ("ringing", "Ringing"),
#         ("in-progress", "In Progress"),
#         ("completed", "Completed"),
#         ("busy", "Busy"),
#         ("no-answer", "No Answer"),
#         ("canceled", "Canceled"),
#         ("failed", "Failed"),
#     ]

#     activity = models.OneToOneField(
#         "activity.Activity",
#         on_delete=models.CASCADE,
#         related_name="call",
#     )

#     connected_content_type = models.ForeignKey(
#         ContentType,
#         on_delete=models.CASCADE,
#         related_name="connected_calls",
#     )

#     connected_object_id = models.PositiveBigIntegerField()

#     connected = GenericForeignKey(
#         "connected_content_type",
#         "connected_object_id",
#     )

#     call_outcome = models.CharField(
#         max_length=50,
#         choices=CALL_OUTCOME_CHOICES,
#         default="other",
#     )

#     # ==========================================
#     # TWILIO
#     # ==========================================

#     twilio_call_sid = models.CharField(
#         max_length=100,
#         unique=True,
#         null=True,
#         blank=True,
#     )

#     twilio_status = models.CharField(
#         max_length=30,
#         choices=TWILIO_STATUS_CHOICES,
#         null=True,
#         blank=True,
#     )

#     # Duration in seconds
#     duration = models.PositiveIntegerField(
#         null=True,
#         blank=True,
#     )

#     date = models.DateField()

#     time = models.TimeField()

#     note = models.TextField(
#         blank=True,
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True,
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True,
#     )

#     def __str__(self):
#         return f"Call - {self.date} {self.time}"



from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Call(models.Model):

    CALL_OUTCOME_CHOICES = [
        ("connected", "Connected"),
        ("no_answer", "No Answer"),
        ("busy", "Busy"),
        ("left_voicemail", "Left Voicemail"),
        ("wrong_number", "Wrong Number"),
        ("callback_requested", "Callback Requested"),
        ("not_interested", "Not Interested"),
        ("other", "Other"),
    ]

    TWILIO_STATUS_CHOICES = [
        ("queued", "Queued"),
        ("initiated", "Initiated"),
        ("ringing", "Ringing"),
        ("in-progress", "In Progress"),
        ("completed", "Completed"),
        ("busy", "Busy"),
        ("no-answer", "No Answer"),
        ("canceled", "Canceled"),
        ("failed", "Failed"),
    ]

    # =========================================================
    # ACTIVITY
    # =========================================================

    activity = models.OneToOneField(
        "activity.Activity",
        on_delete=models.CASCADE,
        related_name="call",
    )

    # =========================================================
    # CONNECTED CRM RECORD
    # =========================================================

    connected_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="connected_calls",
    )

    connected_object_id = models.PositiveBigIntegerField()

    connected = GenericForeignKey(
        "connected_content_type",
        "connected_object_id",
    )

    # =========================================================
    # CALL OUTCOME
    # =========================================================

    call_outcome = models.CharField(
        max_length=50,
        choices=CALL_OUTCOME_CHOICES,
        default="other",
    )

    # =========================================================
    # TWILIO
    # =========================================================

    # ---------------------------------------------------------
    # Legacy / primary Twilio Call SID
    # ---------------------------------------------------------

    twilio_call_sid = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------
    # First leg:
    # Twilio → CRM User
    # ---------------------------------------------------------

    user_twilio_call_sid = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------
    # Second leg:
    # CRM User → Customer
    # ---------------------------------------------------------

    customer_twilio_call_sid = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    # ---------------------------------------------------------
    # Current Twilio status
    # ---------------------------------------------------------

    twilio_status = models.CharField(
        max_length=30,
        choices=TWILIO_STATUS_CHOICES,
        null=True,
        blank=True,
    )

    # =========================================================
    # DURATION
    # =========================================================

    # Duration in seconds
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # =========================================================
    # DATE / TIME
    # =========================================================

    date = models.DateField()

    time = models.TimeField()

    # =========================================================
    # NOTE
    # =========================================================

    note = models.TextField(
        blank=True,
    )

    # =========================================================
    # TIMESTAMPS
    # =========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # =========================================================
    # STRING
    # =========================================================

    def __str__(self):
        return f"Call - {self.date} {self.time}"


