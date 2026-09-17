from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from rest_framework import serializers

from .models import Call
from ..activity.models import Activity


User = get_user_model()


# ============================================================
# MODULE → CONTENT TYPE MAP
# ============================================================

MODULE_MAP = {
    "lead": ("leads", "lead"),
    "company": ("companies", "company"),
    "deal": ("deals", "deal"),
    "ticket": ("tickets", "ticket"),
}


class CallSerializer(serializers.ModelSerializer):

    # ========================================================
    # INPUT FIELDS
    # ========================================================

    module = serializers.CharField(
        write_only=True,
        required=False,
    )

    module_id = serializers.IntegerField(
        write_only=True,
        required=False,
    )

    sender_id = serializers.IntegerField(
        write_only=True,
        required=False,
    )

    # ========================================================
    # OUTPUT FIELDS
    # ========================================================

    created_by = serializers.SerializerMethodField(
        read_only=True,
    )

    connected = serializers.SerializerMethodField(
        read_only=True,
    )

    # ========================================================
    # META
    # ========================================================

    class Meta:
        model = Call

        fields = [
            # ------------------------------------------------
            # Basic
            # ------------------------------------------------

            "id",

            # ------------------------------------------------
            # User
            # ------------------------------------------------

            "created_by",

            # ------------------------------------------------
            # Activity connection
            # ------------------------------------------------

            "module",
            "module_id",
            "sender_id",

            # ------------------------------------------------
            # Call information
            # ------------------------------------------------

            "call_outcome",

            # ------------------------------------------------
            # Twilio information
            # ------------------------------------------------

            "twilio_call_sid",
            "user_twilio_call_sid",
            "customer_twilio_call_sid",
            "twilio_status",
            "duration",

            # ------------------------------------------------
            # Date / Time / Note
            # ------------------------------------------------

            "date",
            "time",
            "note",

            # ------------------------------------------------
            # Connected CRM record
            # ------------------------------------------------

            "connected",

            # ------------------------------------------------
            # Timestamps
            # ------------------------------------------------

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",

            "created_by",
            "connected",

            "twilio_call_sid",
            "user_twilio_call_sid",
            "customer_twilio_call_sid",
            "twilio_status",
            "duration",

            "created_at",
            "updated_at",
        ]

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(self, attrs):

        # ====================================================
        # UPDATE / PATCH
        #
        # Example:
        # PATCH /activities/call/10/
        #
        # {
        #     "call_outcome": "connected"
        # }
        #
        # For PATCH we do NOT require module/sender again.
        # ====================================================

        if self.instance is not None:

            duration = attrs.get("duration")

            if duration is not None and duration < 0:
                raise serializers.ValidationError({
                    "duration": "Duration cannot be negative."
                })

            return attrs

        # ====================================================
        # CREATE
        # ====================================================

        # ----------------------------------------------------
        # Module
        # ----------------------------------------------------

        module = attrs.get("module")

        if not module:
            raise serializers.ValidationError({
                "module": "Module is required."
            })

        module = module.strip().lower()

        attrs["module"] = module

        # ----------------------------------------------------
        # Validate module
        # ----------------------------------------------------

        if module not in MODULE_MAP:
            raise serializers.ValidationError({
                "module": (
                    "Invalid module. Allowed values: "
                    "lead, company, deal, ticket."
                )
            })

        # ----------------------------------------------------
        # Module ID
        # ----------------------------------------------------

        module_id = attrs.get("module_id")

        if not module_id:
            raise serializers.ValidationError({
                "module_id": "Module ID is required."
            })

        # ----------------------------------------------------
        # ContentType
        # ----------------------------------------------------

        app_label, model_name = MODULE_MAP[module]

        try:

            content_type = ContentType.objects.get(
                app_label=app_label,
                model=model_name,
            )

        except ContentType.DoesNotExist:

            raise serializers.ValidationError({
                "module": (
                    f"Content type for '{module}' "
                    "does not exist."
                )
            })

        # ----------------------------------------------------
        # Model class
        # ----------------------------------------------------

        model_class = content_type.model_class()

        if not model_class:

            raise serializers.ValidationError({
                "module": (
                    f"Model for '{module}' "
                    "could not be found."
                )
            })

        # ----------------------------------------------------
        # CRM record exists
        # ----------------------------------------------------

        if not model_class.objects.filter(
            pk=module_id
        ).exists():

            raise serializers.ValidationError({
                "module_id": (
                    f"{module.title()} with ID "
                    f"{module_id} does not exist."
                )
            })

        # ----------------------------------------------------
        # Sender
        # ----------------------------------------------------

        sender_id = attrs.get("sender_id")

        if not sender_id:

            raise serializers.ValidationError({
                "sender_id": "Sender ID is required."
            })

        if not User.objects.filter(
            pk=sender_id
        ).exists():

            raise serializers.ValidationError({
                "sender_id": (
                    f"User with id {sender_id} "
                    "does not exist."
                )
            })

        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        duration = attrs.get("duration")

        if duration is not None and duration < 0:

            raise serializers.ValidationError({
                "duration": (
                    "Duration cannot be negative."
                )
            })

        return attrs

    # ========================================================
    # CREATE
    # ========================================================

    @transaction.atomic
    def create(self, validated_data):

        module = validated_data.pop("module")
        module_id = validated_data.pop("module_id")
        sender_id = validated_data.pop("sender_id")

        # ----------------------------------------------------
        # ContentType
        # ----------------------------------------------------

        app_label, model_name = MODULE_MAP[module]

        content_type = ContentType.objects.get(
            app_label=app_label,
            model=model_name,
        )

        # ----------------------------------------------------
        # Activity
        # ----------------------------------------------------

        activity = Activity.objects.create(
            activity_type="call",
            created_by_id=sender_id,
            content_type=content_type,
            object_id=module_id,
        )

        # ----------------------------------------------------
        # Call
        # ----------------------------------------------------

        call = Call.objects.create(
            activity=activity,
            connected_content_type=content_type,
            connected_object_id=module_id,
            **validated_data,
        )

        return call

    # ========================================================
    # UPDATE
    # ========================================================

    def update(self, instance, validated_data):

        # ----------------------------------------------------
        # These belong to the original call relationship.
        # They should not be changed during Outcome PATCH.
        # ----------------------------------------------------

        validated_data.pop("module", None)
        validated_data.pop("module_id", None)
        validated_data.pop("sender_id", None)

        return super().update(
            instance,
            validated_data,
        )

    # ========================================================
    # CREATED BY
    # ========================================================

    def get_created_by(self, obj):

        if not obj.activity:
            return None

        user = obj.activity.created_by

        if not user:
            return None

        full_name = user.get_full_name()

        return {
            "id": user.id,
            "name": (
                full_name
                or user.email
                or "Unknown"
            ),
        }

    # ========================================================
    # CONNECTED RECORD
    # ========================================================

    def get_connected(self, obj):

        connected_object = obj.connected

        if not connected_object:
            return None

        name = None

        # ----------------------------------------------------
        # Lead
        # ----------------------------------------------------

        if hasattr(
            connected_object,
            "first_name"
        ):

            first_name = getattr(
                connected_object,
                "first_name",
                ""
            )

            last_name = getattr(
                connected_object,
                "last_name",
                ""
            )

            name = (
                f"{first_name} {last_name}"
            ).strip()

            if not name:

                name = getattr(
                    connected_object,
                    "email",
                    None
                )

        # ----------------------------------------------------
        # Company
        # ----------------------------------------------------

        elif hasattr(
            connected_object,
            "company_name"
        ):

            name = connected_object.company_name

        # ----------------------------------------------------
        # Deal
        # ----------------------------------------------------

        elif hasattr(
            connected_object,
            "deal_name"
        ):

            name = connected_object.deal_name

        # ----------------------------------------------------
        # Ticket
        # ----------------------------------------------------

        elif hasattr(
            connected_object,
            "subject"
        ):

            name = connected_object.subject

        elif hasattr(
            connected_object,
            "ticket_name"
        ):

            name = connected_object.ticket_name

        # ----------------------------------------------------
        # Generic name
        # ----------------------------------------------------

        elif hasattr(
            connected_object,
            "name"
        ):

            name = connected_object.name

        # ----------------------------------------------------
        # Final response
        # ----------------------------------------------------

        return {
            "id": connected_object.id,
            "name": name or str(connected_object),
        }