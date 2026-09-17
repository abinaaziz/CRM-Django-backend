

from rest_framework import serializers

from .models import Deal


# ============================================================
# CREATE / UPDATE DEAL SERIALIZER
# ============================================================

class DealCreateSerializer(serializers.ModelSerializer):

    # Lead display name
    lead_name = serializers.SerializerMethodField()

    # Lead phone number
    lead_phone = serializers.SerializerMethodField()

    class Meta:
        model = Deal

        fields = [
            "id",
            "deal_name",
            "deal_stage",
            "associated_lead",
            "lead_name",
            "lead_phone",
            "amount",
            "deal_owners",
            "close_date",
            "priority",
            "created_date",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_date",
            "updated_at",
            "lead_name",
            "lead_phone",
        ]

    # ========================================================
    # LEAD NAME
    # ========================================================

    def get_lead_name(self, obj):

        if not obj.associated_lead:
            return ""

        return (
            f"{obj.associated_lead.first_name} "
            f"{obj.associated_lead.last_name}"
        ).strip()

    # ========================================================
    # LEAD PHONE
    # ========================================================

    def get_lead_phone(self, obj):

        if not obj.associated_lead:
            return ""

        return obj.associated_lead.phone_number or ""

    # ========================================================
    # CREATE DEAL + CONVERT LEAD
    # ========================================================

    def create(self, validated_data):

        # ----------------------------------------------------
        # Get the selected Lead
        # ----------------------------------------------------

        lead = validated_data["associated_lead"]

        # ----------------------------------------------------
        # PREVENT DOUBLE CONVERSION
        # ----------------------------------------------------

        if lead.lead_status == "Converted":

            raise serializers.ValidationError({
                "associated_lead": "This lead is already converted."
            })

        # ----------------------------------------------------
        # Get selected Deal Owners
        #
        # ManyToMany fields cannot be passed directly into
        # Deal.objects.create().
        # ----------------------------------------------------

        deal_owners = validated_data.pop(
            "deal_owners",
            []
        )

        # ----------------------------------------------------
        # CREATE DEAL
        # ----------------------------------------------------

        deal = Deal.objects.create(
            **validated_data
        )

        # ----------------------------------------------------
        # SAVE MULTIPLE DEAL OWNERS
        # ----------------------------------------------------

        deal.deal_owners.set(
            deal_owners
        )

        # ----------------------------------------------------
        # CONVERT LEAD
        #
        # IMPORTANT:
        # Lead status is ALWAYS "Converted".
        #
        # It does NOT become:
        # Qualified to Buy
        # Contract Sent
        # Closed Won
        # etc.
        # ----------------------------------------------------

        lead.lead_status = "Converted"

        lead.save(
            update_fields=["lead_status"]
        )

        return deal

    # ========================================================
    # UPDATE DEAL
    # ========================================================

    def update(self, instance, validated_data):

        # ----------------------------------------------------
        # Get Deal Owners separately
        # ----------------------------------------------------

        deal_owners = validated_data.pop(
            "deal_owners",
            None
        )

        # ----------------------------------------------------
        # UPDATE DEAL
        #
        # IMPORTANT:
        # Changing Deal stage must NOT change Lead status.
        # ----------------------------------------------------

        instance = super().update(
            instance,
            validated_data
        )

        # ----------------------------------------------------
        # UPDATE MULTIPLE DEAL OWNERS
        #
        # Only update owners when the field was actually
        # supplied in the request.
        # ----------------------------------------------------

        if deal_owners is not None:

            instance.deal_owners.set(
                deal_owners
            )

        return instance


# ============================================================
# DEAL LIST SERIALIZER
# ============================================================

class DealListSerializer(serializers.ModelSerializer):

    # Lead display name
    lead_name = serializers.SerializerMethodField()

    # Lead phone number
    lead_phone = serializers.SerializerMethodField()

    # Deal owner display names
    deal_owners = serializers.SerializerMethodField()

    # Owner IDs for Edit
    deal_owner_ids = serializers.PrimaryKeyRelatedField(
        source="deal_owners",
        many=True,
        read_only=True
    )

    class Meta:
        model = Deal

        fields = [
            "id",
            "deal_name",
            "associated_lead",
            "lead_name",
            "lead_phone",
            "deal_stage",
            "close_date",
            "deal_owners",
            "deal_owner_ids",
            "amount",
            "priority",
            "created_date",
        ]

    # ========================================================
    # LEAD NAME
    # ========================================================

    def get_lead_name(self, obj):

        if not obj.associated_lead:
            return ""

        return (
            f"{obj.associated_lead.first_name} "
            f"{obj.associated_lead.last_name}"
        ).strip()

    # ========================================================
    # LEAD PHONE
    # ========================================================

    def get_lead_phone(self, obj):

        if not obj.associated_lead:
            return ""

        return obj.associated_lead.phone_number or ""

    # ========================================================
    # OWNER NAMES
    # ========================================================

    def get_deal_owners(self, obj):

        owners = obj.deal_owners.all()

        return [
            (
                f"{owner.first_name} "
                f"{owner.last_name}"
            ).strip()
            for owner in owners
        ]

