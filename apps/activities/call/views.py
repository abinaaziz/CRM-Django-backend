import logging

from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpResponse

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial

from .models import Call
from .serializers import CallSerializer
from apps.activities.activity.models import Activity


logger = logging.getLogger(__name__)


# ============================================================
# MODULE MAP
# ============================================================

MODULE_MAP = {
    "lead": ("leads", "lead"),
    "company": ("companies", "company"),
    "deal": ("deals", "deal"),
    "ticket": ("tickets", "ticket"),
}


# ============================================================
# TERMINAL TWILIO STATUSES
# ============================================================

TERMINAL_STATUSES = {
    "completed",
    "busy",
    "failed",
    "no-answer",
    "canceled",
}


# ============================================================
# TIMEZONE
# ============================================================

UAE_TIMEZONE = ZoneInfo("Asia/Dubai")


# ============================================================
# TWILIO TRIAL VOICE TEMPLATE
# ============================================================

TRIAL_VOICE_TEMPLATE = (
    "https://webhooks.twilio.com/"
    "v1/Voice/Template/"
    "voice_text_to_speech"
)


# ============================================================
# CALL OUTCOME HELPER
# ============================================================

def get_call_outcome(call_status):
    """
    Convert Twilio CallStatus into CRM call outcome.
    """

    if not call_status:
        return "other"

    status_value = str(
        call_status
    ).lower().strip()

    mapping = {
        "completed": "connected",
        "answered": "connected",
        "in-progress": "connected",
        "busy": "busy",
        "no-answer": "no_answer",
        "failed": "other",
        "canceled": "other",
        "ringing": "other",
        "queued": "other",
        "initiated": "other",
    }

    return mapping.get(
        status_value,
        "other",
    )


# ============================================================
# PHONE NORMALIZATION
# ============================================================

def normalize_phone(phone):

    if not phone:
        return None

    phone = str(
        phone
    ).strip()

    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    return phone


# ============================================================
# E.164 VALIDATION
# ============================================================

def is_valid_e164(phone):

    if not phone:
        return False

    phone = str(
        phone
    ).strip()

    if not phone.startswith("+"):
        return False

    digits = phone[1:]

    if not digits.isdigit():
        return False

    if len(digits) < 8 or len(digits) > 15:
        return False

    return True


# ============================================================
# GET PHONE FROM OBJECT
# ============================================================

def get_phone_from_object(obj):

    if not obj:
        return None

    phone_fields = [
        "phone_number",
        "phone",
        "mobile_number",
        "mobile",
        "contact_phone",
        "customer_phone",
    ]

    for field_name in phone_fields:

        phone = getattr(
            obj,
            field_name,
            None,
        )

        if phone:

            normalized = normalize_phone(
                phone
            )

            if normalized:
                return normalized

    return None


# ============================================================
# GET CUSTOMER PHONE
# ============================================================

def get_customer_phone(obj):
    """
    Priority:

    Lead:
        Lead phone

    Company:
        Company phone

    Deal:
        Deal phone
        -> Associated Lead phone

    Ticket:
        Ticket phone
        -> Associated Deal phone
        -> Associated Lead phone
    """

    if not obj:
        return None

    # --------------------------------------------------------
    # 1. DIRECT OBJECT PHONE
    # --------------------------------------------------------

    direct_phone = get_phone_from_object(
        obj
    )

    if direct_phone:
        return direct_phone

    # --------------------------------------------------------
    # 2. DIRECT ASSOCIATED LEAD
    # --------------------------------------------------------

    associated_lead = getattr(
        obj,
        "associated_lead",
        None,
    )

    if associated_lead:

        lead_phone = get_phone_from_object(
            associated_lead
        )

        if lead_phone:
            return lead_phone

    # --------------------------------------------------------
    # 3. OBJECT -> DEAL
    # --------------------------------------------------------

    deal = getattr(
        obj,
        "deal",
        None,
    )

    if not deal:

        deal = getattr(
            obj,
            "associated_deal",
            None,
        )

    if deal:

        # ----------------------------------------------------
        # DEAL DIRECT PHONE
        # ----------------------------------------------------

        deal_phone = get_phone_from_object(
            deal
        )

        if deal_phone:
            return deal_phone

        # ----------------------------------------------------
        # DEAL -> LEAD
        # ----------------------------------------------------

        deal_lead = getattr(
            deal,
            "associated_lead",
            None,
        )

        if deal_lead:

            lead_phone = get_phone_from_object(
                deal_lead
            )

            if lead_phone:
                return lead_phone

    return None


# ============================================================
# TWILIO CLIENT
# ============================================================

def get_twilio_client():

    return Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )


# ============================================================
# WEBHOOK BASE URL
# ============================================================

def get_webhook_base_url():

    webhook_base_url = getattr(
        settings,
        "TWILIO_WEBHOOK_BASE_URL",
        None,
    )

    if not webhook_base_url:
        return None

    return str(
        webhook_base_url
    ).rstrip("/")


# ============================================================
# CREATE CRM CALL RECORD
#
# IMPORTANT:
#
# Django stores DateTimeField values in UTC when USE_TZ=True.
#
# We explicitly convert created_at to Asia/Dubai before
# saving Call.date and Call.time.
#
# Example:
#
# UTC:
#     2026-09-15 21:21
#
# Dubai:
#     2026-09-16 01:21
#
# Therefore Call.date/time will correctly show UAE time.
# ============================================================

def create_call_record(
    user,
    content_type,
    object_id,
    call_mode,
):

    activity = Activity.objects.create(
        created_by=user,
        activity_type="call",
        content_type=content_type,
        object_id=object_id,
    )

    # --------------------------------------------------------
    # CONVERT UTC -> UAE TIME
    # --------------------------------------------------------

    uae_now = activity.created_at.astimezone(
        UAE_TIMEZONE
    )

    # --------------------------------------------------------
    # CREATE CRM CALL
    # --------------------------------------------------------

    crm_call = Call.objects.create(
        activity=activity,
        connected_content_type=content_type,
        connected_object_id=object_id,

        # IMPORTANT:
        # Save UAE date/time, not UTC date/time.
        date=uae_now.date(),
        time=uae_now.time(),

        call_mode=call_mode,
        call_outcome="other",
    )

    logger.info(
        "CRM Call created | "
        "call_id=%s | "
        "UTC=%s | "
        "UAE=%s",
        crm_call.id,
        activity.created_at,
        uae_now,
    )

    return activity, crm_call


# ============================================================
# CALL LIST + CREATE
# ============================================================

class CallListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = CallSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return (
            Call.objects
            .select_related(
                "activity",
                "activity__created_by",
                "connected_content_type",
            )
            .order_by(
                "-created_at"
            )
        )

    def perform_create(self, serializer):

        serializer.save(
            activity__created_by=self.request.user
        )


# ============================================================
# CALL DETAIL
# ============================================================

class CallDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = CallSerializer

    permission_classes = [
        IsAuthenticated
    ]

    queryset = (
        Call.objects
        .select_related(
            "activity",
            "activity__created_by",
            "connected_content_type",
        )
    )


# ============================================================
# START DIRECT CALL
#
# FLOW:
#
# CRM
#  ↓
# Twilio
#  ↓
# CUSTOMER
# ============================================================

class StartDirectCallView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        activity = None
        crm_call = None

        try:

            # ==================================================
            # REQUEST DATA
            # ==================================================

            module = request.data.get(
                "module"
            )

            module_id = request.data.get(
                "module_id"
            )

            if not module:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Module is required."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not module_id:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Module ID is required."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            module = str(
                module
            ).lower().strip()

            # ==================================================
            # MODULE
            # ==================================================

            if module not in MODULE_MAP:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Unsupported module "
                            f"'{module}'. "
                            f"Allowed modules: "
                            f"{', '.join(MODULE_MAP.keys())}"
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            app_label, model_name = MODULE_MAP[
                module
            ]

            # ==================================================
            # CONTENT TYPE
            # ==================================================

            try:

                content_type = (
                    ContentType.objects.get(
                        app_label=app_label,
                        model=model_name,
                    )
                )

            except ContentType.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Content type not found "
                            f"for {module}."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ==================================================
            # MODEL
            # ==================================================

            crm_model = (
                content_type.model_class()
            )

            if not crm_model:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Unable to load CRM model."
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # ==================================================
            # OBJECT
            # ==================================================

            try:

                crm_object = (
                    crm_model.objects.get(
                        pk=module_id
                    )
                )

            except crm_model.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"{module.capitalize()} "
                            f"with ID {module_id} "
                            f"not found."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ==================================================
            # CUSTOMER PHONE
            # ==================================================

            customer_phone = get_customer_phone(
                crm_object
            )

            if not customer_phone:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Customer phone number "
                            "not found."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            customer_phone = normalize_phone(
                customer_phone
            )

            if not is_valid_e164(
                customer_phone
            ):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Customer phone number "
                            "must be in E.164 format."
                        ),
                        "customer_phone": customer_phone,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ==================================================
            # SETTINGS
            # ==================================================

            required_settings = [
                "TWILIO_ACCOUNT_SID",
                "TWILIO_AUTH_TOKEN",
                "TWILIO_PHONE_NUMBER",
            ]

            missing_settings = [
                setting_name
                for setting_name in required_settings
                if not getattr(
                    settings,
                    setting_name,
                    None,
                )
            ]

            if missing_settings:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Missing Twilio settings: "
                            + ", ".join(
                                missing_settings
                            )
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            twilio_phone = normalize_phone(
                settings.TWILIO_PHONE_NUMBER
            )

            if not is_valid_e164(
                twilio_phone
            ):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "TWILIO_PHONE_NUMBER "
                            "must be in E.164 format."
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # ==================================================
            # CRM RECORD
            # ==================================================

            with transaction.atomic():

                activity, crm_call = (
                    create_call_record(
                        user=request.user,
                        content_type=content_type,
                        object_id=crm_object.pk,
                        call_mode="direct",
                    )
                )

            # ==================================================
            # TWILIO
            # ==================================================

            logger.info(
                "Starting Direct Call | "
                "module=%s | "
                "module_id=%s | "
                "customer=%s",
                module,
                crm_object.pk,
                customer_phone,
            )

            try:

                client = get_twilio_client()

                twilio_call = client.calls.create(
                    to=customer_phone,
                    from_=twilio_phone,
                    url=TRIAL_VOICE_TEMPLATE,
                )

            except Exception as twilio_error:

                logger.exception(
                    "Twilio Direct Call error"
                )

                if crm_call:
                    crm_call.delete()

                if activity:
                    activity.delete()

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Unable to start "
                            "Twilio direct call."
                        ),
                        "error": str(
                            twilio_error
                        ),
                        "customer_phone": customer_phone,
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            # ==================================================
            # SAVE SID
            # ==================================================

            crm_call.customer_twilio_call_sid = (
                twilio_call.sid
            )

            crm_call.twilio_call_sid = (
                twilio_call.sid
            )

            crm_call.twilio_status = (
                getattr(
                    twilio_call,
                    "status",
                    None,
                )
                or "queued"
            )

            crm_call.save(
                update_fields=[
                    "customer_twilio_call_sid",
                    "twilio_call_sid",
                    "twilio_status",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Direct call to CRM record started"
                    ),
                    "call_id": crm_call.id,
                    "module": module,
                    "module_id": crm_object.pk,
                    "customer_phone": customer_phone,
                    "twilio_call_sid": twilio_call.sid,
                    "twilio_status": (
                        twilio_call.status
                    ),
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:

            logger.exception(
                "Unexpected error in "
                "StartDirectCallView"
            )

            return Response(
                {
                    "success": False,
                    "message": (
                        "Failed to start "
                        "direct call."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# START BRIDGE CALL
# ============================================================

class StartCallView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        activity = None
        crm_call = None

        try:

            # ==================================================
            # REQUEST
            # ==================================================

            module = request.data.get(
                "module"
            )

            module_id = request.data.get(
                "module_id"
            )

            if not module:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Module is required."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not module_id:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Module ID is required."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            module = str(
                module
            ).lower().strip()

            # ==================================================
            # MODULE
            # ==================================================

            if module not in MODULE_MAP:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Unsupported module "
                            f"'{module}'. "
                            f"Allowed modules: "
                            f"{', '.join(MODULE_MAP.keys())}"
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            app_label, model_name = MODULE_MAP[
                module
            ]

            # ==================================================
            # CONTENT TYPE
            # ==================================================

            try:

                content_type = (
                    ContentType.objects.get(
                        app_label=app_label,
                        model=model_name,
                    )
                )

            except ContentType.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Content type not found "
                            f"for {module}."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ==================================================
            # MODEL
            # ==================================================

            crm_model = (
                content_type.model_class()
            )

            if not crm_model:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Unable to load CRM model."
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # ==================================================
            # CRM OBJECT
            # ==================================================

            try:

                crm_object = (
                    crm_model.objects.get(
                        pk=module_id
                    )
                )

            except crm_model.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"{module.capitalize()} "
                            f"with ID {module_id} "
                            f"not found."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ==================================================
            # CRM USER PHONE
            # ==================================================

            crm_user = request.user

            user_phone = getattr(
                crm_user,
                "phone_number",
                None,
            )

            if not user_phone:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "CRM user does not have "
                            "a phone number."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_phone = normalize_phone(
                user_phone
            )

            # ==================================================
            # CUSTOMER PHONE
            # ==================================================

            customer_phone = get_customer_phone(
                crm_object
            )

            if not customer_phone:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Customer phone number "
                            "not found."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            customer_phone = normalize_phone(
                customer_phone
            )

            # ==================================================
            # VALIDATE PHONES
            # ==================================================

            if not is_valid_e164(
                user_phone
            ):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "CRM user phone number "
                            "must be in E.164 format."
                        ),
                        "user_phone": user_phone,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not is_valid_e164(
                customer_phone
            ):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Customer phone number "
                            "must be in E.164 format."
                        ),
                        "customer_phone": customer_phone,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ==================================================
            # SETTINGS
            # ==================================================

            required_settings = [
                "TWILIO_ACCOUNT_SID",
                "TWILIO_AUTH_TOKEN",
                "TWILIO_PHONE_NUMBER",
                "TWILIO_WEBHOOK_BASE_URL",
            ]

            missing_settings = [
                setting_name
                for setting_name in required_settings
                if not getattr(
                    settings,
                    setting_name,
                    None,
                )
            ]

            if missing_settings:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Missing Twilio settings: "
                            + ", ".join(
                                missing_settings
                            )
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            twilio_phone = normalize_phone(
                settings.TWILIO_PHONE_NUMBER
            )

            if not is_valid_e164(
                twilio_phone
            ):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "TWILIO_PHONE_NUMBER "
                            "must be in E.164 format."
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            webhook_base_url = (
                get_webhook_base_url()
            )

            # ==================================================
            # CREATE CRM CALL
            # ==================================================

            with transaction.atomic():

                activity, crm_call = (
                    create_call_record(
                        user=crm_user,
                        content_type=content_type,
                        object_id=crm_object.pk,
                        call_mode="bridge",
                    )
                )

            # ==================================================
            # USER STATUS CALLBACK
            # ==================================================

            user_status_url = (
                f"{webhook_base_url}"
                f"/api/activities/call/"
                f"bridge-user-status/"
                f"?call_id={crm_call.id}"
            )

            logger.info(
                "Starting Trial Bridge | "
                "call_id=%s | "
                "user=%s | "
                "customer=%s",
                crm_call.id,
                user_phone,
                customer_phone,
            )

            # ==================================================
            # CREATE FIRST CALL
            # ==================================================

            try:

                client = get_twilio_client()

                twilio_call = client.calls.create(
                    to=user_phone,
                    from_=twilio_phone,
                    url=TRIAL_VOICE_TEMPLATE,
                    status_callback=user_status_url,
                )

            except Exception as twilio_error:

                logger.exception(
                    "Twilio Trial Bridge user-call error"
                )

                if crm_call:
                    crm_call.delete()

                if activity:
                    activity.delete()

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Unable to call "
                            "CRM user."
                        ),
                        "error": str(
                            twilio_error
                        ),
                        "user_phone": user_phone,
                        "customer_phone": customer_phone,
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            # ==================================================
            # SAVE USER CALL SID
            # ==================================================

            crm_call.user_twilio_call_sid = (
                twilio_call.sid
            )

            crm_call.twilio_call_sid = (
                twilio_call.sid
            )

            crm_call.twilio_status = (
                getattr(
                    twilio_call,
                    "status",
                    None,
                )
                or "queued"
            )

            crm_call.save(
                update_fields=[
                    "user_twilio_call_sid",
                    "twilio_call_sid",
                    "twilio_status",
                    "updated_at",
                ]
            )

            # ==================================================
            # RESPONSE
            # ==================================================

            return Response(
                {
                    "success": True,
                    "message": (
                        "Bridge call started. "
                        "CRM user is being called."
                    ),
                    "call_id": crm_call.id,
                    "module": module,
                    "module_id": crm_object.pk,
                    "user_phone": user_phone,
                    "customer_phone": customer_phone,
                    "twilio_call_sid": (
                        twilio_call.sid
                    ),
                    "twilio_status": (
                        twilio_call.status
                    ),
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:

            logger.exception(
                "Unexpected error in "
                "StartCallView"
            )

            return Response(
                {
                    "success": False,
                    "message": (
                        "Failed to start "
                        "bridge call."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# BRIDGE USER STATUS
# ============================================================

class BridgeUserStatusView(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(self, request):

        call_id = (
            request.query_params.get(
                "call_id"
            )
            or request.POST.get(
                "call_id"
            )
        )

        call_sid = request.POST.get(
            "CallSid"
        )

        call_status = request.POST.get(
            "CallStatus"
        )

        call_duration = request.POST.get(
            "CallDuration"
        )

        logger.info(
            "Bridge user status | "
            "call_id=%s | "
            "CallSid=%s | "
            "CallStatus=%s",
            call_id,
            call_sid,
            call_status,
        )

        if not call_id:

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        try:

            crm_call = (
                Call.objects
                .select_related(
                    "connected_content_type"
                )
                .get(
                    pk=call_id
                )
            )

        except Call.DoesNotExist:

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        # ====================================================
        # SAVE USER STATUS
        # ====================================================

        if call_sid:

            crm_call.user_twilio_call_sid = (
                call_sid
            )

            if not crm_call.twilio_call_sid:

                crm_call.twilio_call_sid = (
                    call_sid
                )

        if call_status:

            crm_call.twilio_status = (
                call_status
            )

            if call_status in TERMINAL_STATUSES:

                crm_call.call_outcome = (
                    get_call_outcome(
                        call_status
                    )
                )

        if call_duration:

            try:

                crm_call.duration = int(
                    call_duration
                )

            except (
                ValueError,
                TypeError,
            ):
                pass

        crm_call.save()

        # ====================================================
        # ONLY CONTINUE AFTER USER ANSWERS
        # ====================================================

        if call_status != "in-progress":

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        # ====================================================
        # REQUIRED SETTINGS
        # ====================================================

        webhook_base_url = (
            get_webhook_base_url()
        )

        twilio_phone = normalize_phone(
            getattr(
                settings,
                "TWILIO_PHONE_NUMBER",
                None,
            )
        )

        if not webhook_base_url:

            logger.error(
                "Bridge webhook base URL missing"
            )

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        if not twilio_phone:

            logger.error(
                "Twilio phone number missing"
            )

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        # ====================================================
        # CONFERENCE URL FOR USER
        # ====================================================

        user_conference_url = (
            f"{webhook_base_url}"
            f"/api/activities/call/"
            f"bridge-conference/"
            f"?call_id={crm_call.id}"
            f"&participant=user"
        )

        # ====================================================
        # CUSTOMER PHONE
        # ====================================================

        content_type = (
            crm_call.connected_content_type
        )

        if not content_type:

            logger.error(
                "Bridge call %s has no content type",
                crm_call.id,
            )

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        crm_model = (
            content_type.model_class()
        )

        if not crm_model:

            logger.error(
                "Bridge call %s model not found",
                crm_call.id,
            )

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        try:

            crm_object = (
                crm_model.objects.get(
                    pk=crm_call.connected_object_id
                )
            )

        except crm_model.DoesNotExist:

            logger.error(
                "Bridge CRM object not found | "
                "call_id=%s",
                crm_call.id,
            )

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        customer_phone = get_customer_phone(
            crm_object
        )

        customer_phone = normalize_phone(
            customer_phone
        )

        if not is_valid_e164(
            customer_phone
        ):

            logger.error(
                "Invalid customer phone | "
                "call_id=%s | phone=%s",
                crm_call.id,
                customer_phone,
            )

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        # ====================================================
        # DUPLICATE PROTECTION
        # ====================================================

        note_marker = (
            "[BRIDGE_CUSTOMER_CALL_CREATED]"
        )

        if note_marker not in (
            crm_call.note or ""
        ):

            crm_call.note = (
                (crm_call.note or "")
                + "\n"
                + note_marker
            )

            crm_call.save(
                update_fields=[
                    "note",
                    "updated_at",
                ]
            )

            # =================================================
            # CUSTOMER STATUS CALLBACK
            # =================================================

            customer_status_url = (
                f"{webhook_base_url}"
                f"/api/activities/call/"
                f"bridge-customer-status/"
                f"?call_id={crm_call.id}"
            )

            # =================================================
            # CREATE CUSTOMER CALL
            # =================================================

            try:

                client = get_twilio_client()

                customer_call = (
                    client.calls.create(
                        to=customer_phone,
                        from_=twilio_phone,
                        url=TRIAL_VOICE_TEMPLATE,
                        status_callback=(
                            customer_status_url
                        ),
                    )
                )

            except Exception as twilio_error:

                logger.exception(
                    "Unable to create "
                    "customer Trial call | "
                    "call_id=%s",
                    crm_call.id,
                )

                crm_call.note = (
                    (crm_call.note or "")
                    + "\n"
                    + "[BRIDGE_CUSTOMER_CALL_ERROR] "
                    + str(twilio_error)
                )

                crm_call.save(
                    update_fields=[
                        "note",
                        "updated_at",
                    ]
                )

                try:

                    client.calls(
                        crm_call.user_twilio_call_sid
                    ).update(
                        url=user_conference_url,
                        method="POST",
                    )

                except Exception:

                    logger.exception(
                        "Unable to redirect "
                        "user into conference"
                    )

                return HttpResponse(
                    "",
                    content_type="text/plain",
                )

            # =================================================
            # SAVE CUSTOMER SID
            # =================================================

            crm_call.customer_twilio_call_sid = (
                customer_call.sid
            )

            crm_call.save(
                update_fields=[
                    "customer_twilio_call_sid",
                    "updated_at",
                ]
            )

            logger.info(
                "Customer Trial call created | "
                "crm_call=%s | "
                "customer_sid=%s | "
                "customer=%s",
                crm_call.id,
                customer_call.sid,
                customer_phone,
            )

        # ====================================================
        # REDIRECT USER INTO CONFERENCE
        # ====================================================

        try:

            client = get_twilio_client()

            client.calls(
                crm_call.user_twilio_call_sid
            ).update(
                url=user_conference_url,
                method="POST",
            )

            logger.info(
                "User redirected to conference | "
                "call_id=%s | "
                "user_sid=%s",
                crm_call.id,
                crm_call.user_twilio_call_sid,
            )

        except Exception as exc:

            logger.exception(
                "Unable to redirect user call "
                "to conference | "
                "call_id=%s",
                crm_call.id,
            )

            crm_call.note = (
                (crm_call.note or "")
                + "\n"
                + "[BRIDGE_USER_REDIRECT_ERROR] "
                + str(exc)
            )

            crm_call.save(
                update_fields=[
                    "note",
                    "updated_at",
                ]
            )

        return HttpResponse(
            "",
            content_type="text/plain",
        )


# ============================================================
# BRIDGE CUSTOMER STATUS
# ============================================================

class BridgeCustomerStatusView(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(self, request):

        call_id = (
            request.query_params.get(
                "call_id"
            )
            or request.POST.get(
                "call_id"
            )
        )

        call_sid = request.POST.get(
            "CallSid"
        )

        call_status = request.POST.get(
            "CallStatus"
        )

        call_duration = request.POST.get(
            "CallDuration"
        )

        logger.info(
            "Bridge customer status | "
            "call_id=%s | "
            "CallSid=%s | "
            "CallStatus=%s",
            call_id,
            call_sid,
            call_status,
        )

        if not call_id:

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        try:

            crm_call = Call.objects.get(
                pk=call_id
            )

        except Call.DoesNotExist:

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        # ====================================================
        # SAVE CUSTOMER STATUS
        # ====================================================

        if call_sid:

            crm_call.customer_twilio_call_sid = (
                call_sid
            )

        if call_status:

            crm_call.twilio_status = (
                call_status
            )

            if call_status in TERMINAL_STATUSES:

                crm_call.call_outcome = (
                    get_call_outcome(
                        call_status
                    )
                )

        if call_duration:

            try:

                crm_call.duration = int(
                    call_duration
                )

            except (
                ValueError,
                TypeError,
            ):
                pass

        crm_call.save()

        # ====================================================
        # ONLY REDIRECT WHEN CUSTOMER ANSWERS
        # ====================================================

        if call_status != "in-progress":

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        # ====================================================
        # WEBHOOK URL
        # ====================================================

        webhook_base_url = (
            get_webhook_base_url()
        )

        if not webhook_base_url:

            logger.error(
                "Webhook URL missing "
                "for customer conference"
            )

            return HttpResponse(
                "",
                content_type="text/plain",
            )

        customer_conference_url = (
            f"{webhook_base_url}"
            f"/api/activities/call/"
            f"bridge-conference/"
            f"?call_id={crm_call.id}"
            f"&participant=customer"
        )

        # ====================================================
        # REDIRECT CUSTOMER
        # ====================================================

        try:

            client = get_twilio_client()

            client.calls(
                crm_call.customer_twilio_call_sid
            ).update(
                url=customer_conference_url,
                method="POST",
            )

            logger.info(
                "Customer redirected to conference | "
                "call_id=%s | "
                "customer_sid=%s",
                crm_call.id,
                crm_call.customer_twilio_call_sid,
            )

        except Exception as exc:

            logger.exception(
                "Unable to redirect customer "
                "to conference | "
                "call_id=%s",
                crm_call.id,
            )

            crm_call.note = (
                (crm_call.note or "")
                + "\n"
                + "[BRIDGE_CUSTOMER_REDIRECT_ERROR] "
                + str(exc)
            )

            crm_call.save(
                update_fields=[
                    "note",
                    "updated_at",
                ]
            )

        return HttpResponse(
            "",
            content_type="text/plain",
        )


# ============================================================
# BRIDGE CONFERENCE
# ============================================================

class BridgeConferenceView(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(self, request):

        return self._conference_response(
            request
        )

    def get(self, request):

        return self._conference_response(
            request
        )

    def _conference_response(
        self,
        request,
    ):

        call_id = (
            request.query_params.get(
                "call_id"
            )
            or request.POST.get(
                "call_id"
            )
        )

        participant = (
            request.query_params.get(
                "participant"
            )
            or request.POST.get(
                "participant"
            )
            or "customer"
        )

        participant = str(
            participant
        ).lower().strip()

        logger.info(
            "Bridge conference request | "
            "call_id=%s | "
            "participant=%s",
            call_id,
            participant,
        )

        response = VoiceResponse()

        if participant == "user":

            dial = Dial(
                timeout=600,
            )

            dial.conference(
                "crm-bridge",
                beep=False,
                start_conference_on_enter=True,
                end_conference_on_exit=True,
                wait_url="",
            )

            response.append(
                dial
            )

        else:

            dial = Dial(
                timeout=600,
            )

            dial.conference(
                "crm-bridge",
                beep=False,
                start_conference_on_enter=False,
                end_conference_on_exit=False,
                wait_url="",
            )

            response.append(
                dial
            )

        logger.info(
            "Returning conference TwiML | "
            "call_id=%s | "
            "participant=%s | "
            "twiml=%s",
            call_id,
            participant,
            str(response),
        )

        return HttpResponse(
            str(response),
            content_type="text/xml",
        )


# ============================================================
# LEGACY CONNECT CUSTOMER
# ============================================================

class ConnectCustomerView(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(self, request):

        call_id = (
            request.query_params.get(
                "call_id"
            )
            or request.POST.get(
                "call_id"
            )
        )

        if not call_id:

            response = VoiceResponse()

            response.say(
                "Unable to connect the call."
            )

            response.hangup()

            return HttpResponse(
                str(response),
                content_type="text/xml",
            )

        webhook_base_url = (
            get_webhook_base_url()
        )

        if not webhook_base_url:

            response = VoiceResponse()

            response.say(
                "Twilio webhook URL "
                "is not configured."
            )

            response.hangup()

            return HttpResponse(
                str(response),
                content_type="text/xml",
            )

        conference_url = (
            f"{webhook_base_url}"
            f"/api/activities/call/"
            f"bridge-conference/"
            f"?call_id={call_id}"
            f"&participant=customer"
        )

        response = VoiceResponse()

        response.redirect(
            conference_url,
            method="POST",
        )

        return HttpResponse(
            str(response),
            content_type="text/xml",
        )


# ============================================================
# DIAL STATUS
# ============================================================

class DialStatusView(APIView):

    permission_classes = [
        AllowAny
    ]

    authentication_classes = []

    def post(self, request):

        try:

            call_id = (
                request.query_params.get(
                    "call_id"
                )
                or request.POST.get(
                    "call_id"
                )
            )

            leg = (
                request.query_params.get(
                    "leg"
                )
                or request.POST.get(
                    "leg"
                )
                or "customer"
            )

            leg = str(
                leg
            ).lower().strip()

            if not call_id:

                return HttpResponse(
                    str(
                        VoiceResponse()
                    ),
                    content_type="text/xml",
                )

            call_sid = request.POST.get(
                "CallSid"
            )

            call_status = request.POST.get(
                "CallStatus"
            )

            call_duration = request.POST.get(
                "CallDuration"
            )

            dial_call_sid = request.POST.get(
                "DialCallSid"
            )

            dial_call_status = request.POST.get(
                "DialCallStatus"
            )

            dial_call_duration = request.POST.get(
                "DialCallDuration"
            )

            try:

                crm_call = Call.objects.get(
                    pk=call_id
                )

            except Call.DoesNotExist:

                return HttpResponse(
                    str(
                        VoiceResponse()
                    ),
                    content_type="text/xml",
                )

            # ==================================================
            # CUSTOMER
            # ==================================================

            if leg == "customer":

                if dial_call_sid:

                    crm_call.customer_twilio_call_sid = (
                        dial_call_sid
                    )

                elif call_sid:

                    crm_call.customer_twilio_call_sid = (
                        call_sid
                    )

                customer_status = (
                    dial_call_status
                    or call_status
                )

                if customer_status:

                    crm_call.twilio_status = (
                        customer_status
                    )

                    crm_call.call_outcome = (
                        get_call_outcome(
                            customer_status
                        )
                    )

                duration = (
                    dial_call_duration
                    or call_duration
                )

                if duration:

                    try:

                        crm_call.duration = int(
                            duration
                        )

                    except (
                        ValueError,
                        TypeError,
                    ):
                        pass

            # ==================================================
            # USER
            # ==================================================

            elif leg == "user":

                if call_sid:

                    crm_call.user_twilio_call_sid = (
                        call_sid
                    )

                if call_status:

                    crm_call.twilio_status = (
                        call_status
                    )

                    if call_status in TERMINAL_STATUSES:

                        crm_call.call_outcome = (
                            get_call_outcome(
                                call_status
                            )
                        )

                if call_duration:

                    try:

                        crm_call.duration = int(
                            call_duration
                        )

                    except (
                        ValueError,
                        TypeError,
                    ):
                        pass

            # ==================================================
            # BACKWARD COMPATIBILITY
            # ==================================================

            if (
                not crm_call.twilio_call_sid
                and call_sid
            ):

                crm_call.twilio_call_sid = (
                    call_sid
                )

            crm_call.save()

            logger.info(
                "Legacy DialStatus updated | "
                "call_id=%s | "
                "leg=%s | "
                "CallSid=%s | "
                "DialCallSid=%s | "
                "CallStatus=%s | "
                "DialCallStatus=%s",
                call_id,
                leg,
                call_sid,
                dial_call_sid,
                call_status,
                dial_call_status,
            )

            return HttpResponse(
                str(
                    VoiceResponse()
                ),
                content_type="text/xml",
            )

        except Exception:

            logger.exception(
                "Unexpected error in "
                "DialStatusView"
            )

            return HttpResponse(
                str(
                    VoiceResponse()
                ),
                content_type="text/xml",
            )


# ============================================================
# SYNC CALL
# ============================================================

class SyncCallView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def _sync_call(
        self,
        request,
        pk,
    ):

        try:

            # ==================================================
            # GET CALL
            # ==================================================

            try:

                crm_call = Call.objects.get(
                    pk=pk
                )

            except Call.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Call not found."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ==================================================
            # CHOOSE SID
            # ==================================================

            twilio_sid = (
                crm_call.customer_twilio_call_sid
                or crm_call.user_twilio_call_sid
                or crm_call.twilio_call_sid
            )

            if not twilio_sid:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "No Twilio Call SID "
                            "available."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ==================================================
            # FETCH TWILIO
            # ==================================================

            client = get_twilio_client()

            twilio_call = (
                client.calls(
                    twilio_sid
                ).fetch()
            )

            # ==================================================
            # STATUS
            # ==================================================

            crm_call.twilio_status = (
                twilio_call.status
            )

            crm_call.call_outcome = (
                get_call_outcome(
                    twilio_call.status
                )
            )

            # ==================================================
            # DURATION
            # ==================================================

            if getattr(
                twilio_call,
                "duration",
                None,
            ):

                try:

                    crm_call.duration = int(
                        twilio_call.duration
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    pass

            crm_call.save()

            return Response(
                {
                    "success": True,
                    "call_id": crm_call.id,
                    "twilio_call_sid": twilio_sid,
                    "twilio_status": (
                        twilio_call.status
                    ),
                    "call_outcome": (
                        crm_call.call_outcome
                    ),
                    "duration": (
                        crm_call.duration
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            logger.exception(
                "Error syncing Twilio call"
            )

            return Response(
                {
                    "success": False,
                    "message": (
                        "Failed to sync call."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

    def get(
        self,
        request,
        pk,
    ):

        return self._sync_call(
            request,
            pk,
        )

    def post(
        self,
        request,
        pk,
    ):

        return self._sync_call(
            request,
            pk,
        )