
from rest_framework import serializers

from .models import Email


class EmailSerializer(serializers.ModelSerializer):

    sender_name = serializers.SerializerMethodField()
    sender_email = serializers.SerializerMethodField()

    recipient_name = serializers.SerializerMethodField()
    recipient_email = serializers.SerializerMethodField()

    date = serializers.SerializerMethodField()

    module = serializers.SerializerMethodField()
    module_id = serializers.SerializerMethodField()

    class Meta:

        model = Email

        fields = [
            "id",

            "sender_name",
            "sender_email",

            "recipient_name",
            "recipient_email",

            "module",
            "module_id",

            "cc",
            "bcc",

            "subject",
            "body",

            "date",
            "sent_at",

            "status",
            "error_message",
        ]

        read_only_fields = [
            "id",

            "sender_name",
            "sender_email",

            "recipient_name",
            "recipient_email",

            "module",
            "module_id",

            "date",
            "sent_at",

            "status",
            "error_message",
        ]

    # ==========================================
    # Sender
    # ==========================================

    def get_sender_name(self, obj):

        user = obj.activity.created_by

        if not user:
            return None

        return (
            user.get_full_name()
            or user.email
        )

    def get_sender_email(self, obj):

        user = obj.activity.created_by

        if not user:
            return None

        return user.email

    # ==========================================
    # Recipient
    # ==========================================

    def _get_first_recipient(self, obj):

        recipients = obj.to_recipients

        if not recipients:
            return None

        # If recipients are stored as a list
        if isinstance(recipients, list):

            if len(recipients) == 0:
                return None

            return recipients[0]

        # If recipient is stored as a plain string
        if isinstance(recipients, str):
            return recipients

        return None

    def get_recipient_name(self, obj):

        recipient = self._get_first_recipient(obj)

        if not recipient:
            return None

        # Example:
        # {"name": "John Smith", "email": "john.smith@gmail.com"}
        if isinstance(recipient, dict):
            return recipient.get("name")

        # Example:
        # "john.smith@gmail.com"
        if isinstance(recipient, str):

            if "@" in recipient:
                return recipient.split("@")[0]

            return recipient

        return None

    def get_recipient_email(self, obj):

        recipient = self._get_first_recipient(obj)

        if not recipient:
            return None

        # Dictionary format
        if isinstance(recipient, dict):
            return recipient.get("email")

        # Plain email format
        if isinstance(recipient, str):
            return recipient

        return None

    # ==========================================
    # Date
    # ==========================================

    def get_date(self, obj):

        if not obj.activity:
            return None

        return obj.activity.created_at

    # ==========================================
    # Module
    # ==========================================

    def get_module(self, obj):

        activity = obj.activity

        if not activity or not activity.content_type:
            return None

        model_name = activity.content_type.model

        return model_name.lower()

    # ==========================================
    # Module ID
    # ==========================================

    def get_module_id(self, obj):

        activity = obj.activity

        if not activity:
            return None

        return activity.object_id