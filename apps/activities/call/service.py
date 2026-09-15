from django.conf import settings
from twilio.rest import Client


def get_twilio_client():
    return Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )


def start_user_call(user_phone, webhook_url):
    """
    First leg:
    Twilio calls the CRM user.
    """

    client = get_twilio_client()

    return client.calls.create(
        to=user_phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=webhook_url,
        method="POST",
    )


def connect_customer(customer_phone):
    """
    Second leg:
    After CRM user answers,
    connect the customer.
    """

    from twilio.twiml.voice_response import VoiceResponse, Dial

    response = VoiceResponse()

    dial = Dial()

    dial.number(customer_phone)

    response.append(dial)

    return str(response)