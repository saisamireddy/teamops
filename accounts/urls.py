from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RegisterView
from django.urls import path

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
]

urlpatterns += router.urls
