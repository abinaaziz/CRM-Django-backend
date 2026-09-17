from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Ticket

from apps.notifications.models import Notification

from .serializers import (
    TicketSerializer,
    TicketListSerializer,
    UpdateTicketSerializer,
)


# =====================================================
# TICKET LIST AND CREATE
# =====================================================

class TicketListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        tickets = (
            Ticket.objects
            .select_related("associated_deal")
            .prefetch_related("ticket_owners")
            .all()
            .order_by("-id")
        )

        serializer = TicketListSerializer(
            tickets,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = TicketSerializer(
            data=request.data
        )

        if serializer.is_valid():
            ticket = serializer.save()

            Notification.objects.create(
                user=request.user,
                title="New Ticket Added",
                message=(
                    f"New ticket {ticket.ticket_name} "
                    f"has been added."
                ),
            )

            return Response(
                {
                    "message": "Ticket created successfully.",
                    "data": TicketListSerializer(ticket).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =====================================================
# TICKET DETAIL / UPDATE / DELETE
# =====================================================

class TicketDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_ticket(self, pk):
        return get_object_or_404(
            Ticket.objects
            .select_related("associated_deal")
            .prefetch_related("ticket_owners"),
            pk=pk
        )

    # =================================================
    # GET TICKET
    # =================================================

    def get(self, request, pk):

        ticket = self.get_ticket(pk)

        serializer = TicketListSerializer(ticket)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # =================================================
    # UPDATE TICKET
    # =================================================

    def put(self, request, pk):

        ticket = self.get_ticket(pk)

        old_status = ticket.ticket_status

        serializer = UpdateTicketSerializer(
            ticket,
            data=request.data
        )

        if serializer.is_valid():

            ticket = serializer.save()

            if old_status != ticket.ticket_status:

                Notification.objects.create(
                    user=request.user,
                    title="Ticket Status Changed",
                    message=(
                        f"Ticket {ticket.ticket_name} moved "
                        f"from {old_status} to "
                        f"{ticket.ticket_status}."
                    ),
                )

            else:

                Notification.objects.create(
                    user=request.user,
                    title="Ticket Updated",
                    message=(
                        f"Ticket {ticket.ticket_name} "
                        f"has been updated."
                    ),
                )

            # Reload M2M relationship for response
            ticket = self.get_ticket(pk)

            return Response(
                {
                    "message": "Ticket updated successfully.",
                    "data": TicketListSerializer(ticket).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # PATCH TICKET
    # =================================================

    def patch(self, request, pk):

        ticket = self.get_ticket(pk)

        old_status = ticket.ticket_status

        serializer = UpdateTicketSerializer(
            ticket,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            ticket = serializer.save()

            if old_status != ticket.ticket_status:

                Notification.objects.create(
                    user=request.user,
                    title="Ticket Status Changed",
                    message=(
                        f"Ticket {ticket.ticket_name} moved "
                        f"from {old_status} to "
                        f"{ticket.ticket_status}."
                    ),
                )

            else:

                Notification.objects.create(
                    user=request.user,
                    title="Ticket Updated",
                    message=(
                        f"Ticket {ticket.ticket_name} "
                        f"has been updated."
                    ),
                )

            # Reload M2M relationship for response
            ticket = self.get_ticket(pk)

            return Response(
                {
                    "message": "Ticket updated successfully.",
                    "data": TicketListSerializer(ticket).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # DELETE TICKET
    # =================================================

    def delete(self, request, pk):

        ticket = get_object_or_404(
            Ticket,
            pk=pk
        )

        ticket_name = ticket.ticket_name

        ticket.delete()

        Notification.objects.create(
            user=request.user,
            title="Ticket Deleted",
            message=(
                f"Ticket {ticket_name} "
                f"has been deleted."
            ),
        )

        return Response(
            {
                "message": "Ticket deleted successfully."
            },
            status=status.HTTP_200_OK
        )

