

from django.urls import path

from .views import (
    CallListCreateView,
    CallDetailView,
    StartCallView,
    ConnectCustomerView,
    DialStatusView,
    SyncCallView,
)


urlpatterns = [

    # =========================================================
    # GET ALL CALLS
    # POST NORMAL CALL
    #
    # /api/activities/call/
    # =========================================================

    path(
        "",
        CallListCreateView.as_view(),
        name="call-list-create",
    ),

    # =========================================================
    # START TWILIO CALL
    #
    # POST
    # /api/activities/call/start/
    # =========================================================

    path(
        "start/",
        StartCallView.as_view(),
        name="call-start",
    ),

    # =========================================================
    # TWILIO WEBHOOK
    # USER ANSWERS → CONNECT CUSTOMER
    #
    # POST
    # /api/activities/call/connect-customer/
    # =========================================================

    path(
        "connect-customer/",
        ConnectCustomerView.as_view(),
        name="connect-customer",
    ),

    # =========================================================
    # TWILIO WEBHOOK
    # CALL STATUS CALLBACK
    #
    # POST
    # /api/activities/call/dial-status/
    # =========================================================

    path(
        "dial-status/",
        DialStatusView.as_view(),
        name="dial-status",
    ),

    # =========================================================
    # SYNC TWILIO STATUS / DURATION / OUTCOME
    #
    # GET / POST
    # /api/activities/call/<id>/sync/
    # =========================================================

    path(
        "<int:pk>/sync/",
        SyncCallView.as_view(),
        name="call-sync",
    ),

    # =========================================================
    # GET / UPDATE / DELETE CALL
    #
    # /api/activities/call/<id>/
    # =========================================================

    path(
        "<int:pk>/",
        CallDetailView.as_view(),
        name="call-detail",
    ),
]

