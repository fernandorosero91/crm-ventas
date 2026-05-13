"""
Management command: run_scheduler

Runs the reminder checker automatically at a configured interval.
Designed to run as a background process alongside the Django server.

Usage:
    python manage.py run_scheduler                  # Default: every 60 minutes
    python manage.py run_scheduler --interval 30    # Every 30 minutes
    python manage.py run_scheduler --interval 1440  # Once per day (1440 min)

In Docker, add this as a separate service or run it in the entrypoint.
"""
import time
import logging
from datetime import datetime

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run automatic reminder scheduler (checks reminders at regular intervals)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Interval in minutes between checks (default: 60)',
        )

    def handle(self, *args, **options):
        interval_minutes = options['interval']
        interval_seconds = interval_minutes * 60

        self.stdout.write(
            self.style.SUCCESS(
                f'Scheduler started — checking reminders every {interval_minutes} minutes.\n'
                f'Press Ctrl+C to stop.'
            )
        )

        try:
            while True:
                self._run_check()
                self.stdout.write(
                    f'  Next check in {interval_minutes} minutes...\n'
                )
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nScheduler stopped.'))

    def _run_check(self):
        """Execute the reminder checks."""
        from notifications.services import (
            check_pending_reminders,
            check_inactivity_reminders,
        )

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.stdout.write(f'\n[{now}] Running reminder check...')

        try:
            follow_up_count = check_pending_reminders()
            inactivity_count = check_inactivity_reminders()

            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✓ {follow_up_count} follow-up reminder(s), '
                    f'{inactivity_count} inactivity reminder(s) processed.'
                )
            )
        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(f'  ✗ Error: {exc}')
            )
            logger.exception('Scheduler error during reminder check')
