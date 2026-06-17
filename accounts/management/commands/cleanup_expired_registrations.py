from django.core.management.base import BaseCommand
from accounts.models import PendingUserRegistration


class Command(BaseCommand):
    help = 'Delete expired pending user registrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Delete registrations older than specified days (overrides EXPIRATION_MINUTES)',
        )

    def handle(self, *args, **options):
        deleted_count, _ = PendingUserRegistration.objects.cleanup_expired()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} expired pending registration(s)'
            )
        )
