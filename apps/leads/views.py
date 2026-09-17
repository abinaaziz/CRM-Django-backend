

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.companies.models import Company
from apps.notifications.models import Notification

from .models import Lead, Product
from .serializers import (
    LeadListSerializer,
    LeadCreateSerializer,
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
# LEAD LIST + CREATE
# =========================================================

class LeadListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    # -----------------------------------------------------
    # GET - LIST LEADS
    # -----------------------------------------------------

    def get(self, request):

        # Admin -> all leads
        if is_admin(request.user):

            leads = Lead.objects.all().order_by(
                "-created_date"
            )

        # User -> only own leads
        else:

            leads = Lead.objects.filter(
                contact_owner=request.user
            ).order_by(
                "-created_date"
            )

        # -------------------------------------------------
        # FILTER BY LEAD STATUS
        # -------------------------------------------------

        lead_status = request.query_params.get(
            "lead_status",
            ""
        ).strip()

        if lead_status:
            leads = leads.filter(
                lead_status=lead_status
            )

        # -------------------------------------------------
        # SERIALIZE
        # -------------------------------------------------

        serializer = LeadListSerializer(
            leads,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # -----------------------------------------------------
    # POST - CREATE LEAD
    # -----------------------------------------------------

    def post(self, request):

        serializer = LeadCreateSerializer(
            data=request.data
        )

        if serializer.is_valid():

            # Automatically assign logged-in user
            # as contact owner
            lead = serializer.save(
                contact_owner=request.user
            )

            # -------------------------------------------------
            # NOTIFICATION
            # -------------------------------------------------

            Notification.objects.create(
                user=request.user,
                title="New Lead Added",
                message=(
                    f"New lead {lead.first_name} "
                    f"has been added."
                ),
            )

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            response_serializer = LeadListSerializer(
                lead
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
# SINGLE LEAD DETAIL + UPDATE + DELETE
# =========================================================

class LeadDetailView(APIView):

    permission_classes = [IsAuthenticated]

    # -----------------------------------------------------
    # GET OBJECT - USER-WISE ACCESS
    # -----------------------------------------------------

    def get_object(self, request, pk):

        # Admin -> any lead
        if is_admin(request.user):

            return Lead.objects.prefetch_related(
                "products"
            ).filter(
                pk=pk
            ).first()

        # User -> only own lead
        return Lead.objects.prefetch_related(
            "products"
        ).filter(
            pk=pk,
            contact_owner=request.user
        ).first()

    # -----------------------------------------------------
    # GET - GET ONE LEAD
    # -----------------------------------------------------

    def get(self, request, pk):

        lead = self.get_object(
            request,
            pk
        )

        if lead is None:
            return Response(
                {
                    "detail": "Lead not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LeadCreateSerializer(
            lead
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # -----------------------------------------------------
    # PUT - COMPLETE UPDATE
    # -----------------------------------------------------

    def put(self, request, pk):

        lead = self.get_object(
            request,
            pk
        )

        if lead is None:
            return Response(
                {
                    "detail": "Lead not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = lead.lead_status

        serializer = LeadCreateSerializer(
            lead,
            data=request.data
        )

        if serializer.is_valid():

            lead = serializer.save()

            # -------------------------------------------------
            # STATUS CHANGE NOTIFICATION
            # -------------------------------------------------

            if old_status != lead.lead_status:

                Notification.objects.create(
                    user=request.user,
                    title="Lead Status Changed",
                    message=(
                        f"Lead {lead.first_name} moved "
                        f"from {old_status} "
                        f"to {lead.lead_status}."
                    ),
                )

            else:

                Notification.objects.create(
                    user=request.user,
                    title="Lead Updated",
                    message=(
                        f"Lead {lead.first_name} "
                        f"has been updated."
                    ),
                )

            response_serializer = LeadListSerializer(
                lead
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

        lead = self.get_object(
            request,
            pk
        )

        if lead is None:
            return Response(
                {
                    "detail": "Lead not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = lead.lead_status

        serializer = LeadCreateSerializer(
            lead,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            lead = serializer.save()

            # -------------------------------------------------
            # STATUS CHANGE NOTIFICATION
            # -------------------------------------------------

            if old_status != lead.lead_status:

                Notification.objects.create(
                    user=request.user,
                    title="Lead Status Changed",
                    message=(
                        f"Lead {lead.first_name} moved "
                        f"from {old_status} "
                        f"to {lead.lead_status}."
                    ),
                )

            else:

                Notification.objects.create(
                    user=request.user,
                    title="Lead Updated",
                    message=(
                        f"Lead {lead.first_name} "
                        f"has been updated."
                    ),
                )

            response_serializer = LeadListSerializer(
                lead
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
    # DELETE - DELETE LEAD
    # -----------------------------------------------------

    def delete(self, request, pk):

        lead = self.get_object(
            request,
            pk
        )

        if lead is None:
            return Response(
                {
                    "detail": "Lead not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        lead_name = lead.first_name

        lead.delete()

        # -------------------------------------------------
        # NOTIFICATION
        # -------------------------------------------------

        Notification.objects.create(
            user=request.user,
            title="Lead Deleted",
            message=(
                f"Lead {lead_name} "
                f"has been deleted."
            ),
        )

        return Response(
            {
                "detail": "Lead deleted successfully"
            },
            status=status.HTTP_204_NO_CONTENT
        )


# =========================================================
# LEAD STATUS DROPDOWN
# =========================================================

class LeadStatusChoicesView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        statuses = [
            {
                "value": value,
                "label": label,
            }
            for value, label in Lead.STATUS_CHOICES
        ]

        return Response(
            statuses,
            status=status.HTTP_200_OK
        )


# =========================================================
# PRODUCTS DROPDOWN
# =========================================================

class ProductListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        products = Product.objects.all().order_by(
            "name"
        )

        product_options = [
            {
                "value": product.id,
                "label": product.name,
            }
            for product in products
        ]

        return Response(
            product_options,
            status=status.HTTP_200_OK
        )


# =========================================================
# COMPANY DROPDOWN
# =========================================================

class LeadCompanyListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Admin -> all companies
        if is_admin(request.user):

            companies = Company.objects.all().order_by(
                "company_name"
            )

        # User -> only own companies
        else:

            companies = Company.objects.filter(
                company_owner=request.user
            ).order_by(
                "company_name"
            )

        company_options = [
            {
                "value": company.id,
                "label": company.company_name,
            }
            for company in companies
        ]

        return Response(
            company_options,
            status=status.HTTP_200_OK
        )