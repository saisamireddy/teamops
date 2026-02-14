from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from audit.models import AuditLog


class Command(BaseCommand):
    help = 'Deletes audit logs older than the specified number of days.'

    def add_arguments(self, parser):
        # Allow passing --days argument (default 90)
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of logs to keep'
        )

    def handle(self, *args, **options):
        days = options['days']

        # Calculate the cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(f"Deleting logs older than {cutoff_date}...")

        # Direct DB delete for performance
        count, _ = AuditLog.objects.filter(created_at__lte=cutoff_date).delete()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {count} logs.")
        )