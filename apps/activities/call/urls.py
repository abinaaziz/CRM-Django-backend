from django.urls import path

from .views import (
    CallListCreateView,
    CallDetailView,
    StartCallView,
    StartDirectCallView,
    ConnectCustomerView,
    DialStatusView,
    SyncCallView,
)


urlpatterns = [

    # =========================================================
    # GET ALL CALLS
    # POST NORMAL CALL
    # =========================================================

    path(
        "",
        CallListCreateView.as_view(),
        name="call-list-create",
    ),

    # =========================================================
    # DIRECT CALL
    #
    # POST
    # /api/activities/call/direct/
    # =========================================================

    path(
        "direct/",
        StartDirectCallView.as_view(),
        name="call-direct",
    ),

    # =========================================================
    # BRIDGE CALL
    #
    # POST
    # /api/activities/call/bridge/
    # =========================================================

    path(
        "bridge/",
        StartCallView.as_view(),
        name="call-bridge",
    ),

    # =========================================================
    # OLD BRIDGE ENDPOINT
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
    # TWILIO -> CONNECT CUSTOMER
    # =========================================================

    path(
        "connect-customer/",
        ConnectCustomerView.as_view(),
        name="connect-customer",
    ),

    # =========================================================
    # TWILIO -> DIAL STATUS
    # =========================================================

    path(
        "dial-status/",
        DialStatusView.as_view(),
        name="dial-status",
    ),

    # =========================================================
    # SYNC CALL
    # =========================================================

    path(
        "<int:pk>/sync/",
        SyncCallView.as_view(),
        name="call-sync",
    ),

    # =========================================================
    # CALL DETAIL
    # =========================================================

    path(
        "<int:pk>/",
        CallDetailView.as_view(),
        name="call-detail",
    ),
]