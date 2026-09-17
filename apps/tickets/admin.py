from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):

    list_display = (
        "ticket_name",
        "associated_deal",
        "ticket_status",
        "priority",
        "source",
        "display_ticket_owners",
        "created_date",
    )

    list_filter = (
        "ticket_owners",
        "ticket_status",
        "source",
        "priority",
        "created_date",
    )

    search_fields = (
        "ticket_name",
        "description",
        "ticket_owners__first_name",
        "ticket_owners__last_name",
        "ticket_owners__email",
        "associated_deal__deal_name",
    )

    filter_horizontal = (
        "ticket_owners",
    )

    def display_ticket_owners(self, obj):
        owners = obj.ticket_owners.all()

        return ", ".join(
            (
                f"{owner.first_name} {owner.last_name}"
            ).strip()
            or owner.email
            for owner in owners
        )

    display_ticket_owners.short_description = "Ticket Owners"

