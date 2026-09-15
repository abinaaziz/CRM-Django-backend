# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated

# from .models import Call
# from .serializers import CallSerializer


# class CallListCreateView(APIView):

#     permission_classes = [
#         IsAuthenticated
#     ]

#     # =================================================
#     # GET ALL CALLS
#     # =================================================

#     def get(self, request):

#         calls = (
#             Call.objects
#             .select_related(
#                 "activity",
#                 "activity__created_by",
#                 "activity__content_type",
#                 "connected_content_type",
#             )
#             .order_by("-created_at")
#         )

#         serializer = CallSerializer(
#             calls,
#             many=True,
#             context={
#                 "request": request
#             }
#         )

#         return Response(
#             serializer.data,
#             status=status.HTTP_200_OK
#         )

#     # =================================================
#     # CREATE CALL
#     # =================================================

#     def post(self, request):

#         serializer = CallSerializer(
#             data=request.data,
#             context={
#                 "request": request
#             }
#         )

#         if serializer.is_valid():

#             call = serializer.save()

#             response_serializer = CallSerializer(
#                 call,
#                 context={
#                     "request": request
#                 }
#             )

#             return Response(
#                 response_serializer.data,
#                 status=status.HTTP_201_CREATED
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )


# class CallDetailView(APIView):

#     permission_classes = [
#         IsAuthenticated
#     ]

#     # =================================================
#     # GET CALL OBJECT
#     # =================================================

#     def get_object(self, pk):

#         try:

#             return (
#                 Call.objects
#                 .select_related(
#                     "activity",
#                     "activity__created_by",
#                     "activity__content_type",
#                     "connected_content_type",
#                 )
#                 .get(pk=pk)
#             )

#         except Call.DoesNotExist:

#             return None

#     # =================================================
#     # GET SINGLE CALL
#     # =================================================

#     def get(self, request, pk):

#         call = self.get_object(pk)

#         if not call:

#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CallSerializer(
#             call,
#             context={
#                 "request": request
#             }
#         )

#         return Response(
#             serializer.data,
#             status=status.HTTP_200_OK
#         )

#     # =================================================
#     # PUT
#     # =================================================

#     def put(
#         self,
#         request,
#         pk
#     ):

#         call = self.get_object(pk)

#         if not call:

#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CallSerializer(
#             call,
#             data=request.data,
#             context={
#                 "request": request
#             }
#         )

#         if serializer.is_valid():

#             serializer.save()

#             response_serializer = CallSerializer(
#                 call,
#                 context={
#                     "request": request
#                 }
#             )

#             return Response(
#                 response_serializer.data,
#                 status=status.HTTP_200_OK
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     # =================================================
#     # PATCH
#     # =================================================

#     def patch(
#         self,
#         request,
#         pk
#     ):

#         call = self.get_object(pk)

#         if not call:

#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CallSerializer(
#             call,
#             data=request.data,
#             partial=True,
#             context={
#                 "request": request
#             }
#         )

#         if serializer.is_valid():

#             serializer.save()

#             response_serializer = CallSerializer(
#                 call,
#                 context={
#                     "request": request
#                 }
#             )

#             return Response(
#                 response_serializer.data,
#                 status=status.HTTP_200_OK
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     # =================================================
#     # DELETE
#     # =================================================

#     def delete(
#         self,
#         request,
#         pk
#     ):

#         call = self.get_object(pk)

#         if not call:

#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         call.delete()

#         return Response(
#             {
#                 "detail": "Call deleted successfully."
#             },
#             status=status.HTTP_204_NO_CONTENT
#         )















# from django.conf import settings
# from django.contrib.contenttypes.models import ContentType
# from django.http import HttpResponse

# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.response import Response
# from rest_framework import status

# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse, Dial

# from .models import Call
# from .serializers import CallSerializer


# MODULE_MAP = {
#     "lead": ("leads", "lead"),
#     "company": ("companies", "company"),
#     "deal": ("deals", "deal"),
#     "ticket": ("tickets", "ticket"),
# }


# # ============================================================
# # GET ALL CALLS
# # POST CREATE CALL
# # ============================================================

# class CallListCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         calls = Call.objects.select_related(
#             "activity",
#             "activity__created_by",
#             "connected_content_type",
#         ).order_by("-created_at")

#         serializer = CallSerializer(
#             calls,
#             many=True,
#         )

#         return Response(serializer.data)

#     def post(self, request):
#         serializer = CallSerializer(
#             data=request.data
#         )

#         if serializer.is_valid():
#             call = serializer.save()

#             return Response(
#                 CallSerializer(call).data,
#                 status=status.HTTP_201_CREATED,
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )


# # ============================================================
# # START TWILIO TRIAL CALL
# # ============================================================

# class StartCallView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         module = request.data.get("module")
#         module_id = request.data.get("module_id")

#         print("\n================================")
#         print("START TWILIO TRIAL CALL")
#         print("================================")
#         print("Module:", module)
#         print("Module ID:", module_id)

#         # ----------------------------------------------------
#         # Validate module
#         # ----------------------------------------------------

#         if module not in MODULE_MAP:
#             return Response(
#                 {
#                     "detail": "Invalid module."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         if not module_id:
#             return Response(
#                 {
#                     "detail": "module_id is required."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # ----------------------------------------------------
#         # Get module object
#         # ----------------------------------------------------

#         app_label, model_name = MODULE_MAP[module]

#         try:
#             content_type = ContentType.objects.get(
#                 app_label=app_label,
#                 model=model_name,
#             )

#             model_class = content_type.model_class()

#             obj = model_class.objects.get(
#                 pk=module_id
#             )

#         except ContentType.DoesNotExist:
#             return Response(
#                 {
#                     "detail": "Module configuration not found."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         except model_class.DoesNotExist:
#             return Response(
#                 {
#                     "detail": f"{module.title()} not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         # ----------------------------------------------------
#         # Get customer phone
#         # ----------------------------------------------------

#         customer_phone = None

#         for field in [
#             "phone_number",
#             "phone",
#             "mobile_number",
#             "mobile",
#         ]:
#             value = getattr(obj, field, None)

#             if value:
#                 customer_phone = str(value)
#                 break

#         print("Customer phone:", customer_phone)

#         if not customer_phone:
#             return Response(
#                 {
#                     "detail": "Customer phone number not found."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # ----------------------------------------------------
#         # Twilio settings
#         # ----------------------------------------------------

#         account_sid = settings.TWILIO_ACCOUNT_SID
#         auth_token = settings.TWILIO_AUTH_TOKEN
#         twilio_phone = settings.TWILIO_PHONE_NUMBER

#         if not account_sid:
#             return Response(
#                 {
#                     "detail": "TWILIO_ACCOUNT_SID is not configured."
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )

#         if not auth_token:
#             return Response(
#                 {
#                     "detail": "TWILIO_AUTH_TOKEN is not configured."
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )

#         if not twilio_phone:
#             return Response(
#                 {
#                     "detail": "TWILIO_PHONE_NUMBER is not configured."
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )

#         # ----------------------------------------------------
#         # TRIAL TEST
#         #
#         # Do NOT use your ngrok webhook here.
#         # ----------------------------------------------------

#         trial_webhook_url = (
#             "https://webhooks.twilio.com/v1/Voice/Template/"
#             "voice_text_to_speech"
#         )

#         try:
#             client = Client(
#                 account_sid,
#                 auth_token,
#             )

#             call = client.calls.create(
#                 to=customer_phone,
#                 from_=twilio_phone,
#                 url=trial_webhook_url,
#             )

#             print("\n================================")
#             print("TWILIO TRIAL CALL CREATED")
#             print("================================")
#             print("Call SID:", call.sid)
#             print("Status:", call.status)
#             print("To:", customer_phone)
#             print("From:", twilio_phone)
#             print("================================\n")

#             return Response(
#                 {
#                     "success": True,
#                     "message": "Twilio trial call started.",
#                     "call_sid": call.sid,
#                     "status": call.status,
#                     "to": customer_phone,
#                     "from": twilio_phone,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except Exception as e:
#             print("\n================================================")
#             print("TWILIO TRIAL CALL ERROR")
#             print("================================================")
#             print(str(e))
#             print("================================================\n")

#             return Response(
#                 {
#                     "success": False,
#                     "detail": "Twilio trial call could not be started.",
#                     "error": str(e),
#                 },
#                 status=status.HTTP_502_BAD_GATEWAY,
#             )


# # ============================================================
# # TWILIO VOICE WEBHOOK
# #
# # This is kept because your existing URL still uses it.
# # It will be used later for the CRM-user -> customer bridge.
# # ============================================================

# class TwilioVoiceWebhookView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         response = VoiceResponse()

#         response.say(
#             "Connecting you to the customer."
#         )

#         # This endpoint is currently kept for the future
#         # custom Twilio bridge implementation.

#         return HttpResponse(
#             str(response),
#             content_type="text/xml",
#         )

#     def get(self, request):
#         return self.post(request)


# # ============================================================
# # GET / UPDATE / DELETE SINGLE CALL
# # ============================================================

# class CallDetailView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get_object(self, pk):
#         try:
#             return Call.objects.select_related(
#                 "activity",
#                 "activity__created_by",
#                 "connected_content_type",
#             ).get(pk=pk)

#         except Call.DoesNotExist:
#             return None

#     def get(self, request, pk):
#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = CallSerializer(call)

#         return Response(serializer.data)

#     def put(self, request, pk):
#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = CallSerializer(
#             call,
#             data=request.data,
#         )

#         if serializer.is_valid():
#             serializer.save()

#             return Response(
#                 serializer.data
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     def patch(self, request, pk):
#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = CallSerializer(
#             call,
#             data=request.data,
#             partial=True,
#         )

#         if serializer.is_valid():
#             serializer.save()

#             return Response(
#                 serializer.data
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     def delete(self, request, pk):
#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {
#                     "detail": "Call not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         call.delete()

#         return Response(
#             {
#                 "message": "Call deleted successfully."
#             },
#             status=status.HTTP_204_NO_CONTENT,
#         )





# from django.conf import settings
# from django.contrib.contenttypes.models import ContentType
# from django.http import HttpResponse

# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.response import Response
# from rest_framework import status

# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse, Dial

# from .models import Call
# from .serializers import CallSerializer


# MODULE_MAP = {
#     "lead": ("leads", "lead"),
#     "company": ("companies", "company"),
#     "deal": ("deals", "deal"),
#     "ticket": ("tickets", "ticket"),
# }


# class CallListCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         calls = Call.objects.select_related(
#             "activity",
#             "activity__created_by",
#             "connected_content_type",
#         ).order_by("-created_at")

#         serializer = CallSerializer(calls, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = CallSerializer(data=request.data)

#         if serializer.is_valid():
#             call = serializer.save()

#             return Response(
#                 CallSerializer(call).data,
#                 status=status.HTTP_201_CREATED,
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )


# class StartCallView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         module = request.data.get("module")
#         module_id = request.data.get("module_id")

#         print("\n================================")
#         print("START SERVER SIDE TWILIO CALL")
#         print("================================")
#         print("Module:", module)
#         print("Module ID:", module_id)

#         # -----------------------------------------
#         # VALIDATE MODULE
#         # -----------------------------------------
#         if module not in MODULE_MAP:
#             return Response(
#                 {"detail": "Invalid module."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         if not module_id:
#             return Response(
#                 {"detail": "module_id is required."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # -----------------------------------------
#         # GET CUSTOMER / LEAD OBJECT
#         # -----------------------------------------
#         app_label, model_name = MODULE_MAP[module]

#         try:
#             content_type = ContentType.objects.get(
#                 app_label=app_label,
#                 model=model_name,
#             )

#             model_class = content_type.model_class()

#             obj = model_class.objects.get(pk=module_id)

#         except ContentType.DoesNotExist:
#             return Response(
#                 {"detail": "Module configuration not found."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         except model_class.DoesNotExist:
#             return Response(
#                 {
#                     "detail": f"{module.title()} not found."
#                 },
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         # -----------------------------------------
#         # GET CUSTOMER PHONE
#         # -----------------------------------------
#         customer_phone = None

#         for field in [
#             "phone_number",
#             "phone",
#             "mobile_number",
#             "mobile",
#         ]:
#             value = getattr(obj, field, None)

#             if value:
#                 customer_phone = str(value)
#                 break

#         print("Customer phone:", customer_phone)

#         if not customer_phone:
#             return Response(
#                 {
#                     "detail": "Customer phone number not found."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # -----------------------------------------
#         # GET LOGGED-IN CRM USER PHONE
#         # -----------------------------------------
#         user_phone = getattr(
#             request.user,
#             "phone_number",
#             None,
#         )

#         print("CRM user:", request.user)
#         print("CRM user phone:", user_phone)

#         if not user_phone:
#             return Response(
#                 {
#                     "detail": "CRM user's phone number not found."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # -----------------------------------------
#         # TWILIO SETTINGS
#         # -----------------------------------------
#         account_sid = settings.TWILIO_ACCOUNT_SID
#         auth_token = settings.TWILIO_AUTH_TOKEN
#         twilio_phone = settings.TWILIO_PHONE_NUMBER
#         webhook_base_url = (
#             settings.TWILIO_VOICE_WEBHOOK_BASE_URL
#         )

#         if not account_sid:
#             return Response(
#                 {
#                     "detail": "TWILIO_ACCOUNT_SID is not configured."
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )

#         if not auth_token:
#             return Response(
#                 {
#                     "detail": "TWILIO_AUTH_TOKEN is not configured."
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )

#         if not twilio_phone:
#             return Response(
#                 {
#                     "detail": "TWILIO_PHONE_NUMBER is not configured."
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )

#         if not webhook_base_url:
#             return Response(
#                 {
#                     "detail": (
#                         "TWILIO_VOICE_WEBHOOK_BASE_URL "
#                         "is not configured."
#                     )
#                 },
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )

#         # -----------------------------------------
#         # WEBHOOK URL
#         # -----------------------------------------
#         webhook_url = (
#             f"{webhook_base_url}"
#             f"/api/activities/call/twilio/voice/"
#             f"?customer_phone={customer_phone}"
#         )

#         print("Webhook URL:", webhook_url)

#         # -----------------------------------------
#         # CREATE TWILIO CALL
#         #
#         # IMPORTANT:
#         # First call CRM USER
#         # -----------------------------------------
#         try:
#             client = Client(
#                 account_sid,
#                 auth_token,
#             )

#             call = client.calls.create(
#                 to=user_phone,
#                 from_=twilio_phone,
#                 url=webhook_url,
#                 method="POST",
#             )

#             print("\n================================")
#             print("TWILIO CALL CREATED")
#             print("================================")
#             print("Call SID:", call.sid)
#             print("Status:", call.status)
#             print("CRM User:", user_phone)
#             print("Customer:", customer_phone)
#             print("================================\n")

#             return Response(
#                 {
#                     "success": True,
#                     "message": (
#                         "Call started. "
#                         "CRM user will receive the call first."
#                     ),
#                     "call_sid": call.sid,
#                     "status": call.status,
#                     "user_phone": user_phone,
#                     "customer_phone": customer_phone,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except Exception as e:

#             print("\n================================================")
#             print("TWILIO CALL ERROR")
#             print("================================================")
#             print(str(e))
#             print("================================================\n")

#             return Response(
#                 {
#                     "success": False,
#                     "detail": (
#                         "Twilio call could not be started."
#                     ),
#                     "error": str(e),
#                 },
#                 status=status.HTTP_502_BAD_GATEWAY,
#             )


# class TwilioVoiceWebhookView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):

#         customer_phone = request.query_params.get(
#             "customer_phone"
#         )

#         print("\n================================")
#         print("TWILIO WEBHOOK HIT")
#         print("================================")
#         print("Customer phone:", customer_phone)

#         response = VoiceResponse()

#         if not customer_phone:
#             response.say(
#                 "Customer phone number is missing."
#             )

#             return HttpResponse(
#                 str(response),
#                 content_type="text/xml",
#             )

#         # -----------------------------------------
#         # CONNECT CRM USER TO CUSTOMER
#         # -----------------------------------------
#         response.say(
#             "Connecting you to the customer."
#         )

#         dial = Dial(
#             timeout=30,
#             caller_id=settings.TWILIO_PHONE_NUMBER,
#         )

#         dial.number(customer_phone)

#         response.append(dial)

#         print("Dialing customer:", customer_phone)
#         print("================================\n")

#         return HttpResponse(
#             str(response),
#             content_type="text/xml",
#         )

#     def get(self, request):
#         return self.post(request)


# class CallDetailView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get_object(self, pk):

#         try:
#             return Call.objects.select_related(
#                 "activity",
#                 "activity__created_by",
#                 "connected_content_type",
#             ).get(pk=pk)

#         except Call.DoesNotExist:
#             return None

#     def get(self, request, pk):

#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {"detail": "Call not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = CallSerializer(call)

#         return Response(serializer.data)

#     def put(self, request, pk):

#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {"detail": "Call not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = CallSerializer(
#             call,
#             data=request.data,
#         )

#         if serializer.is_valid():
#             serializer.save()

#             return Response(serializer.data)

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     def patch(self, request, pk):

#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {"detail": "Call not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         serializer = CallSerializer(
#             call,
#             data=request.data,
#             partial=True,
#         )

#         if serializer.is_valid():
#             serializer.save()

#             return Response(serializer.data)

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     def delete(self, request, pk):

#         call = self.get_object(pk)

#         if not call:
#             return Response(
#                 {"detail": "Call not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         call.delete()

#         return Response(
#             {"message": "Call deleted successfully."},
#             status=status.HTTP_204_NO_CONTENT,
#         )


import logging

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
# CALL OUTCOME HELPER
# ============================================================

def get_call_outcome(call_status):
    """
    Convert Twilio CallStatus / DialCallStatus
    into CRM call outcome.
    """

    if not call_status:
        return "other"

    status_value = str(call_status).lower().strip()

    mapping = {
        "completed": "connected",
        "answered": "connected",
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
        "other"
    )


# ============================================================
# PHONE FORMAT HELPER
# ============================================================

def normalize_phone(phone):
    """
    Keep phone numbers in E.164 format.

    Example:
        +971508627767

    Twilio should receive the number with '+'.
    """

    if not phone:
        return None

    phone = str(phone).strip()

    # Remove accidental spaces
    phone = phone.replace(" ", "")

    return phone


# ============================================================
# CUSTOMER PHONE HELPER
# ============================================================

def get_customer_phone(obj):
    """
    Find customer phone number from:

    Lead
    Company
    Deal
    Ticket

    Deal:
        Deal -> Associated Lead

    Ticket:
        Ticket -> Deal -> Associated Lead
    """

    # --------------------------------------------------------
    # DIRECT PHONE FIELDS
    # --------------------------------------------------------

    for field_name in [
        "phone_number",
        "phone",
        "mobile_number",
        "mobile",
    ]:

        phone = getattr(
            obj,
            field_name,
            None
        )

        if phone:

            return normalize_phone(phone)

    # --------------------------------------------------------
    # DEAL -> ASSOCIATED LEAD
    # --------------------------------------------------------

    associated_lead = getattr(
        obj,
        "associated_lead",
        None
    )

    if associated_lead:

        for field_name in [
            "phone_number",
            "phone",
            "mobile_number",
            "mobile",
        ]:

            phone = getattr(
                associated_lead,
                field_name,
                None
            )

            if phone:

                return normalize_phone(phone)

    # --------------------------------------------------------
    # TICKET -> DEAL
    # --------------------------------------------------------

    deal = getattr(
        obj,
        "deal",
        None
    )

    if deal:

        # ----------------------------------------------------
        # TICKET -> DEAL DIRECT PHONE
        # ----------------------------------------------------

        for field_name in [
            "phone_number",
            "phone",
            "mobile_number",
            "mobile",
        ]:

            phone = getattr(
                deal,
                field_name,
                None
            )

            if phone:

                return normalize_phone(phone)

        # ----------------------------------------------------
        # TICKET -> DEAL -> ASSOCIATED LEAD
        # ----------------------------------------------------

        associated_lead = getattr(
            deal,
            "associated_lead",
            None
        )

        if associated_lead:

            for field_name in [
                "phone_number",
                "phone",
                "mobile_number",
                "mobile",
            ]:

                phone = getattr(
                    associated_lead,
                    field_name,
                    None
                )

                if phone:

                    return normalize_phone(phone)

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
# CALL LIST + CREATE
# ============================================================

class CallListCreateView(generics.ListCreateAPIView):

    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Call.objects.select_related(
            "activity",
            "activity__created_by",
            "connected_content_type",
        ).order_by(
            "-created_at"
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
    permission_classes = [IsAuthenticated]

    queryset = Call.objects.select_related(
        "activity",
        "activity__created_by",
        "connected_content_type",
    )


# ============================================================
# START CALL
#
# FLOW:
#
# Frontend
#     ↓
# POST /activities/call/start/
#     ↓
# StartCallView
#     ↓
# Twilio calls CRM USER
#     ↓
# CRM USER answers
#     ↓
# ConnectCustomerView
#     ↓
# Twilio calls CUSTOMER
#     ↓
# CRM USER ↔ CUSTOMER
#
# ============================================================

class StartCallView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            # ==================================================
            # 1. GET REQUEST DATA
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
            # 2. VALIDATE MODULE
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

            app_label, model_name = (
                MODULE_MAP[module]
            )

            # ==================================================
            # 3. GET CONTENT TYPE
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
            # 4. GET CRM MODEL
            # ==================================================

            crm_model = (
                content_type.model_class()
            )

            if not crm_model:

                return Response(
                    {
                        "success": False,
                        "message": (
                            f"Unable to load model "
                            f"for {module}."
                        ),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # ==================================================
            # 5. GET CRM OBJECT
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
            # 6. GET CRM USER PHONE
            # ==================================================

            crm_user = request.user

            user_phone = getattr(
                crm_user,
                "phone_number",
                None
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
            # 7. GET CUSTOMER PHONE
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

            # ==================================================
            # 8. VALIDATE PHONE FORMAT
            # ==================================================

            if not user_phone.startswith("+"):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "CRM user phone number "
                            "must be in E.164 format. "
                            "Example: +971501234567"
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not customer_phone.startswith("+"):

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Customer phone number "
                            "must be in E.164 format. "
                            "Example: +971508627767"
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ==================================================
            # 9. TWILIO SETTINGS
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
                    None
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

            twilio_phone = (
                settings.TWILIO_PHONE_NUMBER
            )

            webhook_base_url = (
                settings.TWILIO_WEBHOOK_BASE_URL
                .rstrip("/")
            )

            # ==================================================
            # 10. WEBHOOK URLS
            # ==================================================

            connect_customer_url = (
                f"{webhook_base_url}"
                f"/api/activities/call/"
                f"connect-customer/"
            )

            # ==================================================
            # 11. CREATE CRM ACTIVITY + CALL
            # ==================================================

            with transaction.atomic():

                activity = Activity.objects.create(
                    created_by=crm_user,
                    activity_type="call",
                    content_type=content_type,
                    object_id=crm_object.pk,
                )

                crm_call = Call.objects.create(
                    activity=activity,
                    connected_content_type=content_type,
                    connected_object_id=crm_object.pk,
                    date=activity.created_at.date(),
                    time=activity.created_at.time(),
                    call_outcome="other",
                )

            # ==================================================
            # 12. USER CALL URL
            #
            # Twilio calls USER.
            #
            # When USER answers,
            # Twilio requests ConnectCustomerView.
            # ==================================================

            user_call_url = (
                f"{connect_customer_url}"
                f"?call_id={crm_call.id}"
            )

            # ==================================================
            # 13. USER STATUS CALLBACK
            # ==================================================

            user_status_url = (
                f"{webhook_base_url}"
                f"/api/activities/call/"
                f"dial-status/"
                f"?call_id={crm_call.id}"
                f"&leg=user"
            )

            # ==================================================
            # 14. CREATE FIRST TWILIO LEG
            #
            # USER IS CALLED FIRST
            # ==================================================

            client = get_twilio_client()

            try:

                twilio_call = client.calls.create(

                    # ------------------------------
                    # CRM USER PHONE
                    # ------------------------------

                    to=user_phone,

                    # ------------------------------
                    # TWILIO NUMBER
                    # ------------------------------

                    from_=twilio_phone,

                    # ------------------------------
                    # AFTER USER ANSWERS
                    # ------------------------------

                    url=user_call_url,
                    method="POST",

                    # ------------------------------
                    # USER LEG STATUS
                    # ------------------------------

                    status_callback=user_status_url,
                    status_callback_method="POST",
                    status_callback_event=[
                        "initiated",
                        "ringing",
                        "answered",
                        "completed",
                    ],
                )

            except Exception as twilio_error:

                logger.exception(
                    "Twilio StartCall error"
                )

                # ----------------------------------
                # REMOVE CRM CALL
                # ----------------------------------

                try:
                    crm_call.delete()
                except Exception:
                    pass

                # ----------------------------------
                # REMOVE ACTIVITY
                # ----------------------------------

                try:
                    activity.delete()
                except Exception:
                    pass

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Unable to start "
                            "Twilio call."
                        ),
                        "error": str(
                            twilio_error
                        ),
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            # ==================================================
            # 15. SAVE USER LEG SID
            # ==================================================

            crm_call.user_twilio_call_sid = (
                twilio_call.sid
            )

            # Backward compatibility
            crm_call.twilio_call_sid = (
                twilio_call.sid
            )

            crm_call.twilio_status = (
                getattr(
                    twilio_call,
                    "status",
                    "queued"
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
            # 16. RESPONSE
            # ==================================================

            return Response(
                {
                    "success": True,
                    "message": (
                        "Calling CRM user..."
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
                "Unexpected error in StartCallView"
            )

            return Response(
                {
                    "success": False,
                    "message": (
                        "Failed to start call."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# CONNECT CUSTOMER
#
# Twilio calls this URL after CRM USER answers.
#
# Then:
#
# <Dial>
#     <Number>customer</Number>
# </Dial>
#
# ============================================================

class ConnectCustomerView(APIView):

    # Twilio does not send our JWT.
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        try:

            # ==================================================
            # 1. GET CALL ID
            # ==================================================

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

            # ==================================================
            # 2. GET CRM CALL
            # ==================================================

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

                response = VoiceResponse()

                response.say(
                    "Call record not found."
                )

                response.hangup()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 3. GET CONTENT TYPE
            # ==================================================

            content_type = (
                crm_call.connected_content_type
            )

            if not content_type:

                response = VoiceResponse()

                response.say(
                    "CRM record not found."
                )

                response.hangup()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 4. GET CRM MODEL
            # ==================================================

            crm_model = (
                content_type.model_class()
            )

            if not crm_model:

                response = VoiceResponse()

                response.say(
                    "CRM model not found."
                )

                response.hangup()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 5. GET CRM OBJECT
            # ==================================================

            try:

                crm_object = (
                    crm_model.objects.get(
                        pk=crm_call.connected_object_id
                    )
                )

            except crm_model.DoesNotExist:

                response = VoiceResponse()

                response.say(
                    "CRM record not found."
                )

                response.hangup()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 6. GET CUSTOMER PHONE
            # ==================================================

            customer_phone = get_customer_phone(
                crm_object
            )

            if not customer_phone:

                response = VoiceResponse()

                response.say(
                    "Customer phone number "
                    "not found."
                )

                response.hangup()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 7. VALIDATE CUSTOMER PHONE
            # ==================================================

            if not customer_phone.startswith("+"):

                response = VoiceResponse()

                response.say(
                    "Customer phone number "
                    "is not configured correctly."
                )

                response.hangup()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 8. TWILIO SETTINGS
            # ==================================================

            twilio_phone = getattr(
                settings,
                "TWILIO_PHONE_NUMBER",
                None
            )

            webhook_base_url = getattr(
                settings,
                "TWILIO_WEBHOOK_BASE_URL",
                None
            )

            if not twilio_phone:

                response = VoiceResponse()

                response.say(
                    "Twilio phone number "
                    "is not configured."
                )

                response.hangup()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
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

            webhook_base_url = (
                webhook_base_url.rstrip("/")
            )

            # ==================================================
            # 9. CUSTOMER DIAL STATUS URL
            # ==================================================

            dial_status_url = (
                f"{webhook_base_url}"
                f"/api/activities/call/"
                f"dial-status/"
                f"?call_id={crm_call.id}"
                f"&leg=customer"
            )

            # ==================================================
            # 10. BUILD TWIML
            #
            # USER IS ALREADY ON THE CALL.
            #
            # NOW TWILIO DIALS CUSTOMER.
            # ==================================================

            response = VoiceResponse()

            dial = Dial(
                caller_id=twilio_phone,
                action=dial_status_url,
                method="POST",
                timeout=30,
            )

            dial.number(
                customer_phone,
                status_callback=dial_status_url,
                status_callback_method="POST",
                status_callback_event=[
                    "initiated",
                    "ringing",
                    "answered",
                    "completed",
                ],
            )

            response.append(
                dial
            )

            # ==================================================
            # 11. RETURN TWIML
            # ==================================================

            return HttpResponse(
                str(response),
                content_type="text/xml",
            )

        except Exception as exc:

            logger.exception(
                "Unexpected error in "
                "ConnectCustomerView"
            )

            response = VoiceResponse()

            response.say(
                "An error occurred while "
                "connecting the customer."
            )

            response.hangup()

            return HttpResponse(
                str(response),
                content_type="text/xml",
            )


# ============================================================
# DIAL STATUS
#
# Handles:
#
# USER LEG
# CUSTOMER LEG
#
# ============================================================

class DialStatusView(APIView):

    # Twilio webhook
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        try:

            # ==================================================
            # 1. GET CALL ID
            # ==================================================

            call_id = (
                request.query_params.get(
                    "call_id"
                )
                or request.POST.get(
                    "call_id"
                )
            )

            # ==================================================
            # 2. GET LEG
            # ==================================================

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

                response = VoiceResponse()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 3. TWILIO VALUES
            # ==================================================

            call_sid = request.POST.get(
                "CallSid"
            )

            call_status = request.POST.get(
                "CallStatus"
            )

            call_duration = request.POST.get(
                "CallDuration"
            )

            # ==================================================
            # 4. <DIAL> CHILD CALL VALUES
            # ==================================================

            dial_call_sid = request.POST.get(
                "DialCallSid"
            )

            dial_call_status = request.POST.get(
                "DialCallStatus"
            )

            dial_call_duration = request.POST.get(
                "DialCallDuration"
            )

            # ==================================================
            # 5. GET CRM CALL
            # ==================================================

            try:

                crm_call = Call.objects.get(
                    pk=call_id
                )

            except Call.DoesNotExist:

                response = VoiceResponse()

                return HttpResponse(
                    str(response),
                    content_type="text/xml",
                )

            # ==================================================
            # 6. CUSTOMER LEG
            # ==================================================

            if leg == "customer":

                # ----------------------------------------------
                # CUSTOMER TWILIO SID
                # ----------------------------------------------

                if dial_call_sid:

                    crm_call.customer_twilio_call_sid = (
                        dial_call_sid
                    )

                elif call_sid:

                    crm_call.customer_twilio_call_sid = (
                        call_sid
                    )

                # ----------------------------------------------
                # CUSTOMER STATUS
                # ----------------------------------------------

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

                # ----------------------------------------------
                # CUSTOMER DURATION
                # ----------------------------------------------

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
            # 7. USER LEG
            # ==================================================

            elif leg == "user":

                # ----------------------------------------------
                # USER TWILIO SID
                # ----------------------------------------------

                if call_sid:

                    crm_call.user_twilio_call_sid = (
                        call_sid
                    )

                # ----------------------------------------------
                # USER STATUS
                # ----------------------------------------------

                user_status = call_status

                if user_status:

                    crm_call.twilio_status = (
                        user_status
                    )

                    # Only set outcome from user leg
                    # when the customer leg has not
                    # completed yet.

                    if (
                        user_status
                        in TERMINAL_STATUSES
                    ):

                        crm_call.call_outcome = (
                            get_call_outcome(
                                user_status
                            )
                        )

                # ----------------------------------------------
                # USER DURATION
                # ----------------------------------------------

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
            # 8. BACKWARD COMPATIBILITY
            # ==================================================

            if (
                not crm_call.twilio_call_sid
                and call_sid
            ):

                crm_call.twilio_call_sid = (
                    call_sid
                )

            # ==================================================
            # 9. SAVE
            # ==================================================

            crm_call.save()

            logger.info(
                "Twilio call status updated | "
                "call_id=%s | "
                "leg=%s | "
                "CallSid=%s | "
                "DialCallSid=%s | "
                "CallStatus=%s | "
                "DialCallStatus=%s | "
                "duration=%s | "
                "DialCallDuration=%s",
                call_id,
                leg,
                call_sid,
                dial_call_sid,
                call_status,
                dial_call_status,
                call_duration,
                dial_call_duration,
            )

            # ==================================================
            # 10. EMPTY TWIML RESPONSE
            # ==================================================

            response = VoiceResponse()

            return HttpResponse(
                str(response),
                content_type="text/xml",
            )

        except Exception as exc:

            logger.exception(
                "Unexpected error in DialStatusView"
            )

            response = VoiceResponse()

            return HttpResponse(
                str(response),
                content_type="text/xml",
            )


# ============================================================
# SYNC CALL
#
# Frontend currently uses GET:
#
# GET /activities/call/<id>/sync/
#
# We support GET.
# POST is also supported for compatibility.
# ============================================================

class SyncCallView(APIView):

    permission_classes = [IsAuthenticated]

    def _sync_call(self, request, pk):

        try:

            # ==================================================
            # 1. GET CRM CALL
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
            # 2. FIND BEST TWILIO SID
            #
            # Customer leg is preferred because
            # it contains the actual customer call.
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
            # 3. TWILIO CLIENT
            # ==================================================

            client = get_twilio_client()

            # ==================================================
            # 4. FETCH TWILIO CALL
            # ==================================================

            twilio_call = (
                client.calls(
                    twilio_sid
                ).fetch()
            )

            # ==================================================
            # 5. UPDATE CRM
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
            # 6. UPDATE DURATION
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

            # ==================================================
            # 7. SAVE
            # ==================================================

            crm_call.save()

            # ==================================================
            # 8. RESPONSE
            # ==================================================

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

    # ========================================================
    # GET
    # ========================================================

    def get(self, request, pk):

        return self._sync_call(
            request,
            pk
        )

    # ========================================================
    # POST
    # ========================================================

    def post(self, request, pk):

        return self._sync_call(
            request,
            pk
        )