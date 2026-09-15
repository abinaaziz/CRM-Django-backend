


from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Meeting
from .serializers import (
    MeetingSerializer,
    MeetingResponseSerializer,
)


# =============================================================
# GET ALL MEETINGS
# POST CREATE MEETING
# =============================================================

class MeetingListCreateView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    # =========================================================
    # GET ALL MEETINGS
    # =========================================================

    def get(self, request):

        meetings = (
            Meeting.objects
            .select_related(
                "owner",
                "activity",
                "activity__content_type",
            )
            .prefetch_related(
                "attendees"
            )
            .all()
            .order_by("-id")
        )

        serializer = MeetingResponseSerializer(
            meetings,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # =========================================================
    # POST - CREATE MEETING
    # =========================================================

    def post(self, request):

        print("\n=================================")
        print("CREATE MEETING")
        print("REQUEST DATA:", request.data)
        print("LOGGED USER:", request.user)
        print("LOGGED USER ID:", request.user.id)
        print("=================================\n")

        data = request.data.copy()

        # Logged-in user becomes sender
        data["sender_id"] = request.user.id

        serializer = MeetingSerializer(
            data=data
        )

        if not serializer.is_valid():

            print("\n=================================")
            print("MEETING VALIDATION ERROR")
            print(serializer.errors)
            print("=================================\n")

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        meeting = serializer.save()

        response_serializer = MeetingResponseSerializer(
            meeting
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

class MeetingModuleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, module, module_id):

        meetings = (
            Meeting.objects
            .select_related(
                "owner",
                "activity",
                "activity__content_type",
            )
            .prefetch_related("attendees")
            .filter(
                activity__activity_type="meeting",
                activity__content_type__model=module,
                activity__object_id=module_id,
            )
            .order_by("-id")
        )

        serializer = MeetingResponseSerializer(
            meetings,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

# =============================================================
# GET MEETINGS FOR ONE DEAL
#
# /api/activities/meeting/deal/2/
# =============================================================

class DealMeetingListView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, deal_id):

        print("\n=================================")
        print("FETCH DEAL MEETINGS")
        print("DEAL ID:", deal_id)
        print("=================================\n")

        # meetings = (
        #     Meeting.objects
        #     .select_related(
        #         "owner",
        #         "activity",
        #         "activity__content_type",
        #     )
        #     .prefetch_related(
        #         "attendees"
        #     )
        #     .filter(
        #         activity__content_type__model="deal",
        #         activity__object_id=deal_id,
        #     )
        #     .order_by("-id")
        # )

        meetings = (
            Meeting.objects
           .select_related(
                "owner",
                "activity",
                "activity__content_type",
            )
            .prefetch_related(
                "attendees"
            )
            .filter(
                activity__activity_type="meeting",
                activity__content_type__model="deal",
                activity__object_id=deal_id,
            )
            .order_by("-id")
)

        serializer = MeetingResponseSerializer(
            meetings,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# =============================================================
# GET MEETINGS FOR ONE TICKET
#
# /api/activities/meeting/ticket/5/
# =============================================================

class TicketMeetingListView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, ticket_id):

        print("\n=================================")
        print("FETCH TICKET MEETINGS")
        print("TICKET ID:", ticket_id)
        print("=================================\n")

        meetings = (
            Meeting.objects
            .select_related(
                "owner",
                "activity",
                "activity__content_type",
            )
            .prefetch_related(
                "attendees"
            )
            .filter(
                activity__content_type__model="ticket",
                activity__object_id=ticket_id,
            )
            .order_by("-id")
        )

        serializer = MeetingResponseSerializer(
            meetings,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# =============================================================
# SINGLE MEETING
#
# GET    /api/activities/meeting/1/
# PUT    /api/activities/meeting/1/
# PATCH  /api/activities/meeting/1/
# DELETE /api/activities/meeting/1/
# =============================================================

class MeetingDetailView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    # =========================================================
    # GET SINGLE MEETING
    # =========================================================

    def get(self, request, pk):

        meeting = get_object_or_404(
            Meeting,
            pk=pk
        )

        serializer = MeetingResponseSerializer(
            meeting
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # =========================================================
    # PUT
    # =========================================================

    def put(self, request, pk):

        meeting = get_object_or_404(
            Meeting,
            pk=pk
        )

        data = request.data.copy()

        # Logged-in user
        data["sender_id"] = request.user.id

        serializer = MeetingSerializer(
            meeting,
            data=data
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        meeting = serializer.save()

        response_serializer = MeetingResponseSerializer(
            meeting
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )

    # =========================================================
    # PATCH
    # =========================================================

    def patch(self, request, pk):

        meeting = get_object_or_404(
            Meeting,
            pk=pk
        )

        data = request.data.copy()

        # Logged-in user
        data["sender_id"] = request.user.id

        serializer = MeetingSerializer(
            meeting,
            data=data,
            partial=True
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        meeting = serializer.save()

        response_serializer = MeetingResponseSerializer(
            meeting
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )

    # =========================================================
    # DELETE
    # =========================================================

    def delete(self, request, pk):

        meeting = get_object_or_404(
            Meeting,
            pk=pk
        )

        meeting.delete()

        return Response(
            {
                "message": "Meeting deleted successfully."
            },
            status=status.HTTP_200_OK
        )