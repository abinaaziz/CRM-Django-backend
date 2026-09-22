
from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Ticket


User = get_user_model()


# =====================================================
# CREATE TICKET SERIALIZER
# =====================================================

class TicketSerializer(serializers.ModelSerializer):

    ticket_owners = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Ticket

        fields = (
            "id",
            "ticket_name",
            "description",
            "ticket_status",
            "source",
            "priority",
            "ticket_owners",
            "associated_deal",
            "created_date",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_date",
            "updated_at",
        )

    def create(self, validated_data):

        ticket_owners = validated_data.pop(
            "ticket_owners",
            []
        )

        ticket = Ticket.objects.create(
            **validated_data
        )

        ticket.ticket_owners.set(
            ticket_owners
        )

        return ticket

    def update(self, instance, validated_data):

        ticket_owners = validated_data.pop(
            "ticket_owners",
            None
        )

        instance = super().update(
            instance,
            validated_data
        )

        if ticket_owners is not None:

            instance.ticket_owners.set(
                ticket_owners
            )

        return instance


# =====================================================
# TICKET LIST / DETAIL SERIALIZER
# =====================================================

class TicketListSerializer(serializers.ModelSerializer):

    # -------------------------------------------------
    # DEAL NAME
    # -------------------------------------------------

    deal_name = serializers.CharField(
        source="associated_deal.deal_name",
        read_only=True
    )

    # -------------------------------------------------
    # DEAL STATUS
    # -------------------------------------------------

    deal_status = serializers.CharField(
        source="associated_deal.deal_stage",
        read_only=True
    )

    # -------------------------------------------------
    # ASSOCIATED DEAL ID
    # -------------------------------------------------

    associated_deal_id = serializers.IntegerField(
        source="associated_deal.id",
        read_only=True
    )

    # -------------------------------------------------
    # ASSOCIATED DEAL
    # Includes associated lead
    # -------------------------------------------------

    associated_deal = serializers.SerializerMethodField()

    # -------------------------------------------------
    # TICKET OWNER NAMES
    # -------------------------------------------------

    ticket_owners = serializers.SerializerMethodField()

    # -------------------------------------------------
    # TICKET OWNER IDS
    # -------------------------------------------------

    ticket_owner_ids = serializers.SerializerMethodField()

    class Meta:
        model = Ticket

        fields = (
            "id",
            "ticket_name",
            "description",

            # Existing deal information
            "deal_name",
            "deal_status",
            "associated_deal_id",

            # Nested deal -> lead information
            "associated_deal",

            "ticket_status",
            "priority",
            "source",

            # Ticket owners
            "ticket_owners",
            "ticket_owner_ids",

            "created_date",
        )

    # -------------------------------------------------
    # ASSOCIATED DEAL
    # -------------------------------------------------

    def get_associated_deal(self, obj):

        deal = obj.associated_deal

        if not deal:
            return None

        lead = deal.associated_lead

        lead_data = None

        if lead:
            lead_data = {
                "id": lead.id,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "phone_number": lead.phone_number,
            }

        return {
            "id": deal.id,
            "deal_name": deal.deal_name,
            "deal_status": deal.deal_stage,
            "associated_lead": lead_data,
        }

    # -------------------------------------------------
    # TICKET OWNER NAMES
    # -------------------------------------------------

    def get_ticket_owners(self, obj):

        owners = obj.ticket_owners.all()

        result = []

        for user in owners:

            full_name = (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip()

            if full_name:
                result.append(full_name)

            elif user.email:
                result.append(user.email)

        return result

    # -------------------------------------------------
    # TICKET OWNER IDS
    # -------------------------------------------------

    def get_ticket_owner_ids(self, obj):

        return list(
            obj.ticket_owners.values_list(
                "id",
                flat=True
            )
        )


# =====================================================
# UPDATE TICKET SERIALIZER
# =====================================================

class UpdateTicketSerializer(serializers.ModelSerializer):

    ticket_owners = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Ticket

        fields = (
            "ticket_name",
            "description",
            "ticket_status",
            "source",
            "priority",
            "ticket_owners",
            "associated_deal",
        )

    def update(self, instance, validated_data):

        ticket_owners = validated_data.pop(
            "ticket_owners",
            None
        )

        instance = super().update(
            instance,
            validated_data
        )

        if ticket_owners is not None:

            instance.ticket_owners.set(
                ticket_owners
            )

        return instance



