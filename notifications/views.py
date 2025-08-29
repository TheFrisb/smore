from rest_framework import serializers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserNotification


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = ["id", "title", "message", "is_read", "created_at"]
        read_only_fields = ["id", "title", "message", "created_at"]


class ListNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all notifications for the authenticated user."""
        notifications = UserNotification.objects.filter(user=request.user)
        serializer = UserNotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Mark a specific notification as read."""
        try:
            notification = UserNotification.objects.get(pk=pk, user=request.user)
        except UserNotification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND
            )

        notification.is_read = True
        notification.save()
        serializer = UserNotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        """Mark all notifications for the authenticated user as read."""
        updated_count = UserNotification.objects.filter(user=request.user).update(
            is_read=True
        )
        return Response(
            {"status": "success", "updated_count": updated_count},
            status=status.HTTP_200_OK,
        )
