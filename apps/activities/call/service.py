from django.conf import settings

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial


# =========================================================
# TWILIO CLIENT
# =========================================================

def get_twilio_client():
    return Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )


# =========================================================
# DIRECT CALL
# =========================================================

def start_direct_call(customer_phone):
    """
    Direct Call.

    CRM
      ↓
    Twilio
      ↓
    Customer

    The CRM user is NOT called.
    """

    if not customer_phone:
        raise ValueError("Customer phone number is required.")

    client = get_twilio_client()

    response = VoiceResponse()

    # Message played to the customer when the call is answered.
    response.say(
        "This call is from your CRM.",
        voice="alice",
    )

    return client.calls.create(
        to=customer_phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        twiml=str(response),
    )


# =========================================================
# BRIDGE CALL - FIRST LEG
# =========================================================

def start_user_call(user_phone, webhook_url):
    """
    First leg of Bridge Call.

    Twilio calls the CRM user first.

    CRM
      ↓
    Twilio
      ↓
    CRM User
    """

    if not user_phone:
        raise ValueError("CRM user phone number is required.")

    if not webhook_url:
        raise ValueError("Bridge webhook URL is required.")

    client = get_twilio_client()

    return client.calls.create(
        to=user_phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=webhook_url,
        method="POST",
    )


# =========================================================
# BRIDGE CALL - SECOND LEG
# =========================================================

def connect_customer(customer_phone):
    """
    Second leg of Bridge Call.

    CRM User answers first.
    Then Twilio connects the customer.

    CRM User
        ↕
      Twilio
        ↕
    Customer
    """

    if not customer_phone:
        raise ValueError("Customer phone number is required.")

    response = VoiceResponse()

    dial = Dial(
        caller_id=settings.TWILIO_PHONE_NUMBER
    )

    dial.number(customer_phone)

    response.append(dial)

    return str(response)