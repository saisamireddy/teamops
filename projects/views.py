from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(ReadOnlyModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return (
            Project.objects
            .filter(
                Q(owner=user) | Q(members=user),
                is_archived=False
            )
            .distinct()
        )
