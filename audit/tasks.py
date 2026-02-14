from celery import shared_task
from django.core.management import call_command

@shared_task
def run_audit_log_cleanup():
    """
    Periodic task to clean up old audit logs.
    Keeps logs for 90 days by default.
    """
    call_command('cleanup_logs', days=90)