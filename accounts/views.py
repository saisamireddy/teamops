from django.shortcuts import render

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import (UserSerializer, RegisterSerializer,UserProfileSerializer,UpdateProfileSerializer,ChangePasswordSerializer,)
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
User = get_user_model()


class UserViewSet(ReadOnlyModelViewSet):
    """
    Read-only user list for assigning project members.
    No create/update/delete here.
    """

    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"detail": "Incorrect old password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"detail": "Password updated successfully"})


