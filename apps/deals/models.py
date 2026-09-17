

from django.conf import settings
from django.db import models

from apps.leads.models import Lead


class Deal(models.Model):

    DEAL_STAGE_CHOICES = [
        ("Contract Sent", "Contract Sent"),
        ("Appointment Scheduled", "Appointment Scheduled"),
        ("Presentation Scheduled", "Presentation Scheduled"),
        ("Qualified to Buy", "Qualified to Buy"),
        ("Closed Won", "Closed Won"),
        ("Closed Lost", "Closed Lost"),
        ("Decision Maker Bought In", "Decision Maker Bought In"),
    ]

    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
    ]

    deal_name = models.CharField(
        max_length=200
    )

    deal_stage = models.CharField(
        max_length=50,
        choices=DEAL_STAGE_CHOICES
    )

    # Corresponding Lead
    associated_lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="associated_deals"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # Multiple Deal Owners
    deal_owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="owned_deals"
    )

    close_date = models.DateField()

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.deal_name


