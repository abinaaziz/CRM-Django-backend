
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.contrib.contenttypes.models import ContentType

from .models import Activity
from .serializers import ActivitySerializer

from apps.activities.call.models import Call
from apps.activities.call.serializers import CallSerializer


# =====================================================
# MODULE → CONTENT TYPE
# =====================================================

MODULE_CONTENT_TYPES = {
    "lead": ("leads", "lead"),
    "deal": ("deals", "deal"),
    "company": ("companies", "company"),
    "ticket": ("tickets", "ticket"),
}


# =====================================================
# GET CONTENT TYPE
# =====================================================

def get_content_type(module):

    module = str(module).strip().lower()

    if module not in MODULE_CONTENT_TYPES:
        return None

    app_label, model = MODULE_CONTENT_TYPES[module]

    try:
        return ContentType.objects.get(
            app_label=app_label,
            model=model,
        )

    except ContentType.DoesNotExist:
        return None


# =====================================================
# GET ALL ACTIVITIES FOR A MODULE RECORD
#
# GET /api/activities/activity/lead/4/
# GET /api/activities/activity/deal/4/
# =====================================================

class ActivityTimelineView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, module, module_id):

        content_type = get_content_type(module)

        if not content_type:

            return Response(
                {
                    "error": "Invalid module."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        activities = (
            Activity.objects
            .filter(
                content_type=content_type,
                object_id=module_id,
            )
            .select_related(
                "created_by",
                "content_type",
            )
            .order_by("-created_at")
        )

        serializer = ActivitySerializer(
            activities,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# =====================================================
# GET ACTIVITIES OF ONE TYPE
#
# GET /api/activities/activity/lead/5/call/
# GET /api/activities/activity/company/5/call/
# GET /api/activities/activity/deal/5/call/
# GET /api/activities/activity/ticket/5/call/
# =====================================================

class ActivityTypeDetailView(APIView):

    permission_classes = [IsAuthenticated]

    VALID_ACTIVITY_TYPES = [
        "note",
        "call",
        "task",
        "meeting",
        "email",
    ]

    def get(
        self,
        request,
        module,
        module_id,
        activity_type,
    ):

        # =================================================
        # NORMALIZE VALUES
        # =================================================

        module = str(module).strip().lower()
        activity_type = str(activity_type).strip().lower()

        print("")
        print("=================================================")
        print("ACTIVITY TYPE DETAIL VIEW")
        print("=================================================")
        print("MODULE:", module)
        print("MODULE ID:", module_id)
        print("ACTIVITY TYPE:", activity_type)
        print("=================================================")

        # =================================================
        # VALIDATE ACTIVITY TYPE
        # =================================================

        if activity_type not in self.VALID_ACTIVITY_TYPES:

            return Response(
                {
                    "error": "Invalid activity type."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # FIND CONTENT TYPE
        # =================================================

        content_type = get_content_type(module)

        if not content_type:

            return Response(
                {
                    "error": "Invalid module."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # GET ACTIVITIES
        # =================================================

        activities = (
            Activity.objects
            .filter(
                content_type=content_type,
                object_id=module_id,
                activity_type=activity_type,
            )
            .select_related(
                "created_by",
                "content_type",
            )
            .order_by("-created_at")
        )

        # =================================================
        # CALL ACTIVITIES
        # =================================================

        if activity_type == "call":

            calls = (
                Call.objects
                .filter(
                    activity__in=activities,
                )
                .select_related(
                    "activity",
                    "activity__created_by",
                    "activity__content_type",
                    "connected_content_type",
                )
                .order_by("-created_at")
            )

            print("CALL COUNT:", calls.count())

            serializer = CallSerializer(
                calls,
                many=True,
                context={
                    "request": request,
                },
            )

            serialized_data = serializer.data

            print("")
            print("SERIALIZED CALL DATA")
            print("=================================================")

            if serialized_data:
                print(serialized_data[0])
            else:
                print("NO CALL DATA")

            print("=================================================")
            print("")

            return Response(
                {
                    "module": module,
                    "module_id": module_id,
                    "activity_type": activity_type,
                    "activities": serialized_data,
                },
                status=status.HTTP_200_OK,
            )

        # =================================================
        # OTHER ACTIVITY TYPES
        # =================================================

        serializer = ActivitySerializer(
            activities,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "module": module,
                "module_id": module_id,
                "activity_type": activity_type,
                "activities": serializer.data,
            },
            status=status.HTTP_200_OK,
        )