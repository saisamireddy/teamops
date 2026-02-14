from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth import user_logged_in

# REST Framework imports
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

# SimpleJWT imports
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer, AdminUserSerializer,
)

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


# --- NEW CUSTOM LOGIN VIEW (With Role Data) ---
class CustomLoginView(TokenObtainPairView):
    """
    Custom Login View that:
    1. Triggers 'user_logged_in' signal (for Audit Logs).
    2. Returns User Profile data + Role (for Frontend Dashboards).
    """

    def post(self, request, *args, **kwargs):
        # 1. Standard SimpleJWT validation
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise e

        # 2. Get the User object and fire Audit Signal
        user = serializer.user
        user_logged_in.send(sender=user.__class__, request=request, user=user)

        # 3. Construct Custom Response (Tokens + User Data)
        response_data = serializer.validated_data  # Contains 'access' and 'refresh'

        # Add user profile data (Role, Name, Avatar) to response
        response_data["user"] = UserProfileSerializer(user).data

        return Response(response_data, status=status.HTTP_200_OK)


# --- NEW ADMIN USER MANAGEMENT VIEW ---
class AdminUserViewSet(ModelViewSet):
    """
    Full CRUD for Users. RESTRICTED to Admins only.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    # 1. SUSPEND USER
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response({"error": "You cannot suspend yourself."}, status=400)

        user.is_active = not user.is_active
        user.save()
        return Response({"status": "success", "is_active": user.is_active})

    # 2. RESET PASSWORD
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get("password")

        if not new_password:
            return Response({"error": "Password is required"}, status=400)

        user.set_password(new_password)
        user.save()


        return Response({"status": "success", "message": "Password has been reset."})