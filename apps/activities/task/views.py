
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .models import Task
from .serializers import TaskSerializer

from apps.notifications.models import Notification


User = get_user_model()


# ========================================
# LIST + CREATE TASK
# ========================================

class TaskListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    # ====================================
    # GET ALL TASKS
    # ====================================

    def get(self, request):

        tasks = (
            Task.objects
            .select_related(
                "activity",
                "activity__created_by",
                "activity__content_type",
                "assigned_to",
            )
            .all()
            .order_by("-created_at")
        )

        serializer = TaskSerializer(
            tasks,
            many=True,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # ====================================
    # POST CREATE TASK
    # ====================================

    def post(self, request):

        serializer = TaskSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        task = serializer.save()

        Notification.objects.create(
            user=request.user,
            title="New Task Added",
            message=f"Task {task.task_name} has been created.",
        )

        return Response(
            TaskSerializer(
                task,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


# ========================================
# TASK OPTIONS
# ========================================

class TaskOptionsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # ====================================
        # TASK TYPES
        # ====================================

        task_types = [
            {
                "value": value,
                "label": label,
            }
            for value, label in Task.TASK_TYPE_CHOICES
        ]

        # ====================================
        # PRIORITIES
        # ====================================

        priorities = [
            {
                "value": value,
                "label": label,
            }
            for value, label in Task.PRIORITY_CHOICES
        ]

        # ====================================
        # USERS
        # ====================================

        module = request.query_params.get("module")
        module_id = request.query_params.get("module_id")

        users = User.objects.filter(
            is_active=True
        )

        # ------------------------------------
        # LEAD TASK
        # ------------------------------------
        #
        # If Task is being created for a Lead,
        # only that Lead's contact owners should
        # appear in Assigned To.
        #
        # Example:
        #
        # /task/options/?module=lead&module_id=39
        #
        # ------------------------------------

        if module == "lead" and module_id:

            try:
                from apps.leads.models import Lead

                lead = (
                    Lead.objects
                    .prefetch_related("contact_owners")
                    .get(pk=module_id)
                )

                users = lead.contact_owners.filter(
                    is_active=True
                ).order_by(
                    "first_name",
                    "last_name",
                )

            except Lead.DoesNotExist:

                users = User.objects.none()

        else:

            users = users.order_by(
                "first_name",
                "last_name",
            )

        assigned_users = [
            {
                "id": user.id,
                "name": (
                    user.get_full_name()
                    or user.email
                ),
            }
            for user in users
        ]

        return Response(
            {
                "task_types": task_types,
                "priorities": priorities,
                "assigned_users": assigned_users,
            },
            status=status.HTTP_200_OK,
        )


# ========================================
# TASK DETAIL
# ========================================

class TaskDetailView(APIView):

    permission_classes = [IsAuthenticated]

    # ====================================
    # GET OBJECT
    # ====================================

    def get_object(self, pk):

        try:

            return (
                Task.objects
                .select_related(
                    "activity",
                    "activity__created_by",
                    "activity__content_type",
                    "assigned_to",
                )
                .get(pk=pk)
            )

        except Task.DoesNotExist:

            return None

    # ====================================
    # GET ONE TASK
    # ====================================

    def get(self, request, pk):

        task = self.get_object(pk)

        if task is None:

            return Response(
                {
                    "detail": "Task not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TaskSerializer(
            task,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # ====================================
    # PUT
    # ====================================

    def put(self, request, pk):

        task = self.get_object(pk)

        if task is None:

            return Response(
                {
                    "detail": "Task not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TaskSerializer(
            task,
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        task = serializer.save()

        Notification.objects.create(
            user=request.user,
            title="Task Updated",
            message=f"Task {task.task_name} has been updated.",
        )

        return Response(
            TaskSerializer(
                task,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

    # ====================================
    # PATCH
    # ====================================

    def patch(self, request, pk):

        task = self.get_object(pk)

        if task is None:

            return Response(
                {
                    "detail": "Task not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TaskSerializer(
            task,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        task = serializer.save()

        Notification.objects.create(
            user=request.user,
            title="Task Updated",
            message=f"Task {task.task_name} has been updated.",
        )

        return Response(
            TaskSerializer(
                task,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

    # ====================================
    # DELETE
    # ====================================

    def delete(self, request, pk):

        task = self.get_object(pk)

        if task is None:

            return Response(
                {
                    "detail": "Task not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        task_name = task.task_name

        task.delete()

        Notification.objects.create(
            user=request.user,
            title="Task Deleted",
            message=f"Task {task_name} has been deleted.",
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

