from rest_framework.routers import DefaultRouter
from .views import TaskViewSet
from .views import TaskViewSet, ProjectTaskListCreateView
from django.urls import path

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="tasks")

urlpatterns = [

    path(
        "projects/<int:project_id>/tasks/",
        ProjectTaskListCreateView.as_view(),
        name="project-tasks",
    ),
]

urlpatterns += router.urls
