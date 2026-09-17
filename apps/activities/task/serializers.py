
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from rest_framework import serializers

from .models import Task

from apps.activities.activity.models import Activity
from apps.leads.models import Lead

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):

    # ========================================
    # INPUT FIELDS
    # ========================================

    sender_id = serializers.IntegerField(
        write_only=True,
        required=False
    )

    module = serializers.CharField(
        write_only=True,
        required=False
    )

    module_id = serializers.IntegerField(
        write_only=True,
        required=False
    )

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    # ========================================
    # RESPONSE FIELDS
    # ========================================

    created_by = serializers.SerializerMethodField()

    lead = serializers.SerializerMethodField()

    class Meta:

        model = Task

        fields = [
            "id",

            # Input
            "sender_id",
            "module",
            "module_id",

            # Response
            "created_by",
            "lead",

            # Task
            "task_name",
            "due_date",
            "time",
            "task_type",
            "priority",
            "assigned_to",
            "note",

            # Timestamps
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "lead",
            "created_at",
            "updated_at",
        ]

    # ========================================
    # CREATED BY
    # ========================================

    def get_created_by(self, obj):

        if not obj.activity:
            return None

        user = obj.activity.created_by

        if not user:
            return None

        return {
            "id": user.id,
            "name": (
                user.get_full_name()
                or user.email
            )
        }

    # ========================================
    # LEAD / RELATED CRM OBJECT
    # ========================================

    def get_lead(self, obj):

        if not obj.activity:
            return None

        related_object = obj.activity.content_object

        if not related_object:
            return None

        content_type = obj.activity.content_type

        if not content_type:
            return None

        model_name = content_type.model

        # ----------------------------------------
        # LEAD
        # ----------------------------------------

        if model_name == "lead":

            return {
                "id": related_object.id,
                "name": (
                    f"{related_object.first_name} "
                    f"{related_object.last_name}"
                ).strip()
            }

        # ----------------------------------------
        # DEAL
        # ----------------------------------------

        if model_name == "deal":

            lead = getattr(
                related_object,
                "associated_lead",
                None
            )

            if lead:

                return {
                    "id": lead.id,
                    "name": (
                        f"{lead.first_name} "
                        f"{lead.last_name}"
                    ).strip()
                }

            return {
                "id": related_object.id,
                "name": getattr(
                    related_object,
                    "deal_name",
                    str(related_object)
                )
            }

        # ----------------------------------------
        # COMPANY
        # ----------------------------------------

        if model_name == "company":

            return {
                "id": related_object.id,
                "name": getattr(
                    related_object,
                    "name",
                    str(related_object)
                )
            }

        # ----------------------------------------
        # TICKET
        # ----------------------------------------

        if model_name == "ticket":

            return {
                "id": related_object.id,
                "name": getattr(
                    related_object,
                    "name",
                    str(related_object)
                )
            }

        return None

    # ========================================
    # VALIDATION
    # ========================================

    def validate(self, attrs):

        module = attrs.pop(
            "module",
            None
        )

        module_id = attrs.pop(
            "module_id",
            None
        )

        sender_id = attrs.pop(
            "sender_id",
            None
        )

        # ========================================
        # SENDER
        # ========================================

        sender = None

        if sender_id is not None:

            try:

                sender = User.objects.get(
                    id=sender_id
                )

            except User.DoesNotExist:

                raise serializers.ValidationError({
                    "sender_id":
                        "Sender does not exist."
                })

        # ========================================
        # UPDATE WITHOUT MODULE
        # ========================================

        if module is None and module_id is None:

            if sender is not None:
                attrs["_sender"] = sender

            return attrs

        # ========================================
        # MODULE + MODULE ID
        # ========================================

        if module is None or module_id is None:

            raise serializers.ValidationError({
                "module":
                    "Both module and module_id are required."
            })

        module = str(module).lower().strip()

        MODULE_MAP = {

            "lead": (
                "leads",
                "lead"
            ),

            "deal": (
                "deals",
                "deal"
            ),

            "company": (
                "companies",
                "company"
            ),

            "ticket": (
                "tickets",
                "ticket"
            ),
        }

        if module not in MODULE_MAP:

            raise serializers.ValidationError({
                "module":
                    "Invalid module. Allowed modules: "
                    "lead, deal, company, ticket."
            })

        app_label, model_name = MODULE_MAP[module]

        # ========================================
        # CONTENT TYPE
        # ========================================

        try:

            content_type = ContentType.objects.get(
                app_label=app_label,
                model=model_name
            )

        except ContentType.DoesNotExist:

            raise serializers.ValidationError({
                "module":
                    f"{module} module does not exist."
            })

        # ========================================
        # CHECK CRM OBJECT
        # ========================================

        model_class = content_type.model_class()

        if model_class is None:

            raise serializers.ValidationError({
                "module":
                    f"Unable to find model for {module}."
            })

        related_object = model_class.objects.filter(
            id=module_id
        ).first()

        if related_object is None:

            raise serializers.ValidationError({
                "module_id":
                    f"{module} with id {module_id} does not exist."
            })

        # ========================================
        # LEAD ASSIGNED-TO VALIDATION
        # ========================================
        #
        # Lead Contact Owners are multiple users.
        #
        # Task Assigned To remains SINGLE user.
        #
        # Therefore:
        #
        # Lead Contact Owners:
        #     Sajij
        #     Riya
        #     Hisham
        #
        # Task Assigned To can be:
        #     Sajij OR Riya OR Hisham
        #
        # But not another user.
        # ========================================

        if module == "lead":

            assigned_user = attrs.get(
                "assigned_to"
            )

            if assigned_user is not None:

                is_contact_owner = (
                    related_object.contact_owners.filter(
                        id=assigned_user.id
                    ).exists()
                )

                if not is_contact_owner:

                    raise serializers.ValidationError({
                        "assigned_to":
                            "Assigned user must be one "
                            "of the lead's contact owners."
                    })

        # ========================================
        # STORE INTERNAL VALUES
        # ========================================

        attrs["_content_type"] = content_type

        attrs["_object_id"] = module_id

        if sender is not None:
            attrs["_sender"] = sender

        return attrs

    # ========================================
    # CREATE
    # ========================================

    @transaction.atomic
    def create(self, validated_data):

        sender = validated_data.pop(
            "_sender",
            None
        )

        content_type = validated_data.pop(
            "_content_type",
            None
        )

        object_id = validated_data.pop(
            "_object_id",
            None
        )

        request = self.context.get(
            "request"
        )

        # ========================================
        # CURRENT USER
        # ========================================

        if sender is None:

            if (
                request
                and request.user.is_authenticated
            ):

                sender = request.user

            else:

                raise serializers.ValidationError({
                    "sender_id":
                        "Authenticated user is required."
                })

        # ========================================
        # MODULE REQUIRED
        # ========================================

        if content_type is None or object_id is None:

            raise serializers.ValidationError({
                "module":
                    "Both module and module_id are required."
            })

        # ========================================
        # CREATE ACTIVITY
        # ========================================

        activity = Activity.objects.create(
            activity_type="task",
            created_by=sender,
            content_type=content_type,
            object_id=object_id
        )

        # ========================================
        # CREATE TASK
        # ========================================

        task = Task.objects.create(
            activity=activity,
            **validated_data
        )

        return task

    # ========================================
    # UPDATE
    # ========================================

    @transaction.atomic
    def update(self, instance, validated_data):

        validated_data.pop(
            "_sender",
            None
        )

        content_type = validated_data.pop(
            "_content_type",
            None
        )

        object_id = validated_data.pop(
            "_object_id",
            None
        )

        # ========================================
        # UPDATE TASK
        # ========================================

        for attr, value in validated_data.items():

            setattr(
                instance,
                attr,
                value
            )

        instance.save()

        # ========================================
        # UPDATE ACTIVITY
        # ========================================

        if instance.activity:

            if content_type is not None:

                instance.activity.content_type = (
                    content_type
                )

            if object_id is not None:

                instance.activity.object_id = (
                    object_id
                )

            instance.activity.save()

        return instance

    # ========================================
    # RESPONSE
    # ========================================

    def to_representation(self, instance):

        data = super().to_representation(
            instance
        )

        # ========================================
        # MODULE
        # ========================================

        if (
            instance.activity
            and instance.activity.content_type
        ):

            data["module"] = (
                instance.activity.content_type.model
            )

        else:

            data["module"] = None

        # ========================================
        # MODULE ID
        # ========================================

        if (
            instance.activity
            and instance.activity.object_id
        ):

            data["module_id"] = (
                instance.activity.object_id
            )

        else:

            data["module_id"] = None

        # ========================================
        # ASSIGNED USER
        # ========================================

        if instance.assigned_to:

            data["assigned_to"] = {

                "id": instance.assigned_to.id,

                "name": (
                    instance.assigned_to.get_full_name()
                    or instance.assigned_to.email
                )
            }

        else:

            data["assigned_to"] = None

        # ========================================
        # REMOVE INPUT ONLY FIELD
        # ========================================

        data.pop(
            "sender_id",
            None
        )

        return data

