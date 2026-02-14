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
from django.contrib.auth import user_logged_in
from rest_framework_simplejwt.views import TokenObtainPairView
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


# --- NEW CUSTOM LOGIN VIEW ---
class CustomLoginView(TokenObtainPairView):
    """
    Custom Login View that triggers the 'user_logged_in' signal.
    This allows the Audit Log system to record the login event.
    """

    def post(self, request, *args, **kwargs):
        # 1. Run standard SimpleJWT validation
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise e

        # 2. Get the User object
        user = serializer.user

        # 3. Manually fire the 'user_logged_in' signal
        user_logged_in.send(sender=user.__class__, request=request, user=user)

        # 4. Return tokens
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
