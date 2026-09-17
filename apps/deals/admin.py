# from django.contrib import admin

# from .models import Deal


# @admin.register(Deal)
# class DealAdmin(admin.ModelAdmin):

#     list_display = [
#         "id",
#         "deal_name",
#         "lead_name",
#         "deal_stage",
#         "close_date",
#         "deal_owner",
#         "amount",
#     ]

#     list_filter = [
#         "deal_owner",
#         "deal_stage",
#         "close_date",
#         "created_date",
#     ]

#     search_fields = [
#         "deal_name",
#         "associated_lead__first_name",
#         "associated_lead__last_name",
#         "associated_lead__email",
#     ]

#     def lead_name(self, obj):
#         return (
#             f"{obj.associated_lead.first_name} "
#             f"{obj.associated_lead.last_name}"
#         ).strip()

#     lead_name.short_description = "Lead"




from django.contrib import admin

from .models import Deal


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "deal_name",
        "deal_stage",
        "associated_lead",
        "amount",
        "display_deal_owners",
        "close_date",
        "priority",
        "created_date",
    ]

    list_filter = [
        "deal_owners",
        "deal_stage",
        "priority",
        "close_date",
    ]

    search_fields = [
        "deal_name",
        "associated_lead__first_name",
        "associated_lead__last_name",
        "associated_lead__email",
        "deal_owners__first_name",
        "deal_owners__last_name",
        "deal_owners__email",
    ]

    filter_horizontal = [
        "deal_owners",
    ]

    def display_deal_owners(self, obj):
        owners = obj.deal_owners.all()

        return ", ".join(
            (
                f"{owner.first_name} "
                f"{owner.last_name}"
            ).strip()
            or owner.email
            for owner in owners
        )

    display_deal_owners.short_description = "Deal Owners"

