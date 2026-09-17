from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Deal
from apps.notifications.models import Notification

from .serializers import (
    DealCreateSerializer,
    DealListSerializer,
)


# =========================================================
# HELPER
# =========================================================

def is_admin(user):
    return (
        getattr(user, "role", "") == "Admin"
        or user.is_staff
    )


# =========================================================
# DEAL LIST + CREATE
# =========================================================

class DealListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    # -----------------------------------------------------
    # GET - LIST DEALS
    # -----------------------------------------------------

    def get(self, request):

        if is_admin(request.user):

            # Admin -> all deals
            deals = (
                Deal.objects
                .select_related(
                    "associated_lead",
                )
                .prefetch_related(
                    "deal_owners",
                )
                .all()
            )

        else:

            # User -> deals where the user is one of
            # the selected Deal Owners
            deals = (
                Deal.objects
                .select_related(
                    "associated_lead",
                )
                .prefetch_related(
                    "deal_owners",
                )
                .filter(
                    deal_owners=request.user
                )
                .distinct()
            )

        serializer = DealListSerializer(
            deals,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # -----------------------------------------------------
    # POST - CREATE DEAL
    # -----------------------------------------------------

    def post(self, request):

        serializer = DealCreateSerializer(
            data=request.data
        )

        if serializer.is_valid():

            # Deal Owners are supplied from the frontend
            #
            # Example:
            # {
            #     "deal_owners": [1, 5, 8]
            # }
            #
            # The serializer handles the ManyToMany
            # relationship.

            deal = serializer.save()

            # ------------------------------------------------
            # NOTIFICATION
            # ------------------------------------------------

            Notification.objects.create(
                user=request.user,
                title="New Deal Added",
                message=(
                    f"New deal {deal.deal_name} "
                    f"has been added."
                ),
            )

            # ------------------------------------------------
            # RESPONSE
            # ------------------------------------------------

            response_deal = (
                Deal.objects
                .select_related(
                    "associated_lead",
                )
                .prefetch_related(
                    "deal_owners",
                )
                .get(
                    pk=deal.pk
                )
            )

            response_serializer = DealListSerializer(
                response_deal
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# DEAL DETAIL + UPDATE + DELETE
# =========================================================

class DealDetailView(APIView):

    permission_classes = [IsAuthenticated]

    # -----------------------------------------------------
    # GET - GET ONE DEAL
    # -----------------------------------------------------

    def get(self, request, pk):

        if is_admin(request.user):

            # Admin -> any deal
            try:

                deal = (
                    Deal.objects
                    .select_related(
                        "associated_lead",
                    )
                    .prefetch_related(
                        "deal_owners",
                    )
                    .get(
                        pk=pk
                    )
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:

            # User -> only deals where the user
            # is one of the Deal Owners
            try:

                deal = (
                    Deal.objects
                    .select_related(
                        "associated_lead",
                    )
                    .prefetch_related(
                        "deal_owners",
                    )
                    .get(
                        pk=pk,
                        deal_owners=request.user
                    )
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        serializer = DealListSerializer(
            deal
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # -----------------------------------------------------
    # PUT - COMPLETE UPDATE
    # -----------------------------------------------------

    def put(self, request, pk):

        if is_admin(request.user):

            # Admin -> can update any deal
            try:

                deal = (
                    Deal.objects
                    .select_related(
                        "associated_lead",
                    )
                    .prefetch_related(
                        "deal_owners",
                    )
                    .get(
                        pk=pk
                    )
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:

            # User -> can update only a deal where
            # the user is one of the Deal Owners
            try:

                deal = (
                    Deal.objects
                    .select_related(
                        "associated_lead",
                    )
                    .prefetch_related(
                        "deal_owners",
                    )
                    .get(
                        pk=pk,
                        deal_owners=request.user
                    )
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        # -------------------------------------------------
        # OLD STAGE
        # -------------------------------------------------

        old_stage = deal.deal_stage

        # -------------------------------------------------
        # SERIALIZER
        # -------------------------------------------------

        serializer = DealCreateSerializer(
            deal,
            data=request.data
        )

        if serializer.is_valid():

            deal = serializer.save()

            # ------------------------------------------------
            # STAGE CHANGE NOTIFICATION
            # ------------------------------------------------

            if old_stage != deal.deal_stage:

                if deal.deal_stage == "Closed Won":

                    Notification.objects.create(
                        user=request.user,
                        title="Deal Won",
                        message=(
                            f"Deal {deal.deal_name} "
                            f"has been marked as Closed Won."
                        ),
                    )

                elif deal.deal_stage == "Closed Lost":

                    Notification.objects.create(
                        user=request.user,
                        title="Deal Lost",
                        message=(
                            f"Deal {deal.deal_name} "
                            f"has been marked as Closed Lost."
                        ),
                    )

                else:

                    Notification.objects.create(
                        user=request.user,
                        title="Deal Stage Changed",
                        message=(
                            f"Deal {deal.deal_name} moved "
                            f"from {old_stage} "
                            f"to {deal.deal_stage}."
                        ),
                    )

            else:

                # ------------------------------------------------
                # NORMAL UPDATE NOTIFICATION
                # ------------------------------------------------

                Notification.objects.create(
                    user=request.user,
                    title="Deal Updated",
                    message=(
                        f"Deal {deal.deal_name} "
                        f"has been updated."
                    ),
                )

            # ------------------------------------------------
            # REFRESH DEAL WITH OWNERS
            # ------------------------------------------------

            response_deal = (
                Deal.objects
                .select_related(
                    "associated_lead",
                )
                .prefetch_related(
                    "deal_owners",
                )
                .get(
                    pk=deal.pk
                )
            )

            response_serializer = DealListSerializer(
                response_deal
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # PATCH - PARTIAL UPDATE
    # -----------------------------------------------------

    def patch(self, request, pk):

        if is_admin(request.user):

            # Admin -> can update any deal
            try:

                deal = (
                    Deal.objects
                    .select_related(
                        "associated_lead",
                    )
                    .prefetch_related(
                        "deal_owners",
                    )
                    .get(
                        pk=pk
                    )
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:

            # User -> can update only a deal where
            # the user is one of the Deal Owners
            try:

                deal = (
                    Deal.objects
                    .select_related(
                        "associated_lead",
                    )
                    .prefetch_related(
                        "deal_owners",
                    )
                    .get(
                        pk=pk,
                        deal_owners=request.user
                    )
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        # -------------------------------------------------
        # OLD STAGE
        # -------------------------------------------------

        old_stage = deal.deal_stage

        # -------------------------------------------------
        # SERIALIZER
        # -------------------------------------------------

        serializer = DealCreateSerializer(
            deal,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            deal = serializer.save()

            # ------------------------------------------------
            # STAGE CHANGE NOTIFICATION
            # ------------------------------------------------

            if old_stage != deal.deal_stage:

                if deal.deal_stage == "Closed Won":

                    Notification.objects.create(
                        user=request.user,
                        title="Deal Won",
                        message=(
                            f"Deal {deal.deal_name} "
                            f"has been marked as Closed Won."
                        ),
                    )

                elif deal.deal_stage == "Closed Lost":

                    Notification.objects.create(
                        user=request.user,
                        title="Deal Lost",
                        message=(
                            f"Deal {deal.deal_name} "
                            f"has been marked as Closed Lost."
                        ),
                    )

                else:

                    Notification.objects.create(
                        user=request.user,
                        title="Deal Stage Changed",
                        message=(
                            f"Deal {deal.deal_name} moved "
                            f"from {old_stage} "
                            f"to {deal.deal_stage}."
                        ),
                    )

            else:

                # ------------------------------------------------
                # NORMAL UPDATE NOTIFICATION
                # ------------------------------------------------

                Notification.objects.create(
                    user=request.user,
                    title="Deal Updated",
                    message=(
                        f"Deal {deal.deal_name} "
                        f"has been updated."
                    ),
                )

            # ------------------------------------------------
            # REFRESH DEAL WITH OWNERS
            # ------------------------------------------------

            response_deal = (
                Deal.objects
                .select_related(
                    "associated_lead",
                )
                .prefetch_related(
                    "deal_owners",
                )
                .get(
                    pk=deal.pk
                )
            )

            response_serializer = DealListSerializer(
                response_deal
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # DELETE - DELETE DEAL
    # -----------------------------------------------------

    def delete(self, request, pk):

        if is_admin(request.user):

            # Admin -> can delete any deal
            try:

                deal = Deal.objects.get(
                    pk=pk
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:

            # User -> can delete only a deal where
            # the user is one of the Deal Owners
            try:

                deal = Deal.objects.get(
                    pk=pk,
                    deal_owners=request.user
                )

            except Deal.DoesNotExist:

                return Response(
                    {
                        "detail": "Deal not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        # -------------------------------------------------
        # SAVE NAME BEFORE DELETE
        # -------------------------------------------------

        deal_name = deal.deal_name

        # -------------------------------------------------
        # DELETE
        # -------------------------------------------------

        deal.delete()

        # -------------------------------------------------
        # NOTIFICATION
        # -------------------------------------------------

        Notification.objects.create(
            user=request.user,
            title="Deal Deleted",
            message=(
                f"Deal {deal_name} "
                f"has been deleted."
            ),
        )

        return Response(
            {
                "message": "Deal deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )


# =========================================================
# DEAL STAGE DROPDOWN
# =========================================================

class DealStageListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        stages = [
            {
                "value": value,
                "label": label,
            }
            for value, label in Deal.DEAL_STAGE_CHOICES
        ]

        return Response(
            stages,
            status=status.HTTP_200_OK
        )

