

from django.db import models
from django.conf import settings


class Ticket(models.Model):
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("WAITING_ON_CONTACT", "Waiting on Contact"),
        ("WAITING_ON_US", "Waiting on Us"),
        ("CLOSED", "Closed"),
    ]

    SOURCE_CHOICES = [
        ("CHAT", "Chat"),
        ("EMAIL", "Email"),
        ("PHONE", "Phone"),
        ("WEB", "Web"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]

    ticket_name = models.CharField(max_length=255)

    description = models.TextField(
        blank=True,
        null=True
    )

    ticket_status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="NEW"
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="WEB"
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="MEDIUM"
    )

    # Multiple Ticket Owners
    ticket_owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="owned_tickets"
    )

    associated_deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "tickets"
        ordering = ["-created_date"]

    def __str__(self):
        return self.ticket_name
