from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RegisterView, UserProfileView, ChangePasswordView, AdminUserViewSet
from django.urls import path

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"admin/users", AdminUserViewSet, basename="admin-users")
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("users/me/", UserProfileView.as_view()),
    path("users/change-password/", ChangePasswordView.as_view()),
]

urlpatterns += router.urls
