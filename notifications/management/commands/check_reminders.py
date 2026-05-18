"""
Management command: check_reminders

Checks pending follow-up reminders and inactivity reminders,
creates in-app notifications, and sends emails.

Designed to be called by a cron job or scheduler (e.g., daily):
    python manage.py check_reminders

Options:
    --dry-run    Log what would be done without creating notifications or sending emails.
    --verbosity  At verbosity >= 2, log each individual reminder processed.
"""

import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check pending follow-up reminders and inactivity reminders, create notifications and send emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Log what would be done without creating notifications or sending emails.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbosity = options.get('verbosity', 1)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'Dry-run mode enabled — no notifications will be created or emails sent.'
                )
            )

        try:
            if dry_run:
                follow_up_count = self._dry_run_pending_reminders(verbosity)
                inactivity_count = self._dry_run_inactivity_reminders(verbosity)
            else:
                from notifications.services import (
                    check_pending_reminders,
                    check_inactivity_reminders,
                )

                follow_up_count = check_pending_reminders()
                if verbosity >= 2:
                    self.stdout.write(
                        f'  Processed {follow_up_count} follow-up reminder(s).'
                    )

                inactivity_count = check_inactivity_reminders()
                if verbosity >= 2:
                    self.stdout.write(
                        f'  Processed {inactivity_count} inactivity reminder(s).'
                    )

            summary = (
                f'Processed {follow_up_count} follow-up reminders '
                f'and {inactivity_count} inactivity reminders'
            )
            if dry_run:
                summary += ' (dry-run, no changes made)'

            self.stdout.write(self.style.SUCCESS(summary))

        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(f'Error while checking reminders: {exc}')
            )

    # ------------------------------------------------------------------
    # Dry-run helpers — inspect what would be processed without side effects
    # ------------------------------------------------------------------

    def _dry_run_pending_reminders(self, verbosity: int) -> int:
        """
        Count overdue follow-ups that would trigger reminders without
        creating any notifications or sending any emails.
        """
        try:
            from ventas.models import FollowUp

            today = date.today()
            overdue = FollowUp.objects.filter(
                next_action_date__lte=today,
                is_active=True,
            ).select_related('created_by', 'opportunity', 'client')

            count = 0
            for follow_up in overdue:
                if follow_up.created_by is None:
                    continue
                count += 1
                if verbosity >= 2:
                    entity = (
                        follow_up.opportunity
                        or follow_up.client
                        or 'Sin entidad'
                    )
                    self.stdout.write(
                        f'  [dry-run] Would notify {follow_up.created_by.username} '
                        f'about follow-up for {entity} '
                        f'(due: {follow_up.next_action_date})'
                    )
            return count

        except Exception as exc:  # noqa: BLE001
            self.stderr.write(
                self.style.ERROR(f'  [dry-run] Error scanning follow-up reminders: {exc}')
            )
            return 0

    def _dry_run_inactivity_reminders(self, verbosity: int) -> int:
        """
        Count stale opportunities that would trigger inactivity reminders
        without creating any notifications or sending any emails.
        """
        try:
            from django.conf import settings
            from ventas.models import Opportunity, FollowUp

            inactivity_days = getattr(settings, 'INACTIVITY_REMINDER_DAYS', 7)
            cutoff_date = timezone.now() - timedelta(days=inactivity_days)
            closed_stages = ['cierre_ganado', 'cierre_perdido']

            active_opportunities = Opportunity.objects.filter(
                is_active=True,
            ).exclude(
                stage__in=closed_stages,
            ).select_related('assigned_vendedor', 'client')

            count = 0
            for opportunity in active_opportunities:
                recent_exists = FollowUp.objects.filter(
                    opportunity=opportunity,
                    is_active=True,
                    date__gte=cutoff_date,
                ).exists()

                if recent_exists or opportunity.assigned_vendedor is None:
                    continue

                count += 1
                if verbosity >= 2:
                    self.stdout.write(
                        f'  [dry-run] Would notify {opportunity.assigned_vendedor.username} '
                        f'about inactive opportunity "{opportunity.title}" '
                        f'(no activity in {inactivity_days}+ days)'
                    )
            return count

        except Exception as exc:  # noqa: BLE001
            self.stderr.write(
                self.style.ERROR(f'  [dry-run] Error scanning inactivity reminders: {exc}')
            )
            return 0
