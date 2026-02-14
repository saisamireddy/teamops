from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from django.contrib.contenttypes.models import ContentType
from django.utils.dateparse import parse_date
from .models import AuditLog
from .serializers import AuditLogSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditLogViewSet(ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]  # Use [IsAdminUser] if you want strict access
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('actor', 'content_type')

        # --- FILTERS ---

        # 1. Filter by Model Name (e.g., ?model=task)
        model = self.request.query_params.get('model')
        object_id = self.request.query_params.get('object_id')
        if model:
            try:
                ct = ContentType.objects.get(model=model.lower())
                queryset = queryset.filter(content_type=ct)
                if object_id:
                    queryset = queryset.filter(object_id=object_id)
            except ContentType.DoesNotExist:
                return queryset.none()

        # 2. Filter by Actor (e.g., ?actor_id=5)
        actor_id = self.request.query_params.get('actor_id')
        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)

        # 3. Filter by Action (e.g., ?action=LOGIN)
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # 4. Date Range Filtering (e.g., ?start_date=2026-01-01&end_date=2026-01-31)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start:
                queryset = queryset.filter(created_at__date__gte=parsed_start)

        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end:
                queryset = queryset.filter(created_at__date__lte=parsed_end)

        return queryset