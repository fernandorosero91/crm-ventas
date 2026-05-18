"""
Notification and email services for the CRM system.

Provides functions for creating in-app notifications, sending emails with
retry logic, and checking for pending follow-up and inactivity reminders.
"""
import logging
import time
from datetime import date, timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from notifications.models import Notification, EmailLog

logger = logging.getLogger(__name__)


def create_notification(
    recipient,
    title: str,
    message: str,
    notification_type: str = 'system',
    link: str = '',
) -> Notification:
    """
    Create and return an in-app Notification for the given recipient.

    Args:
        recipient: A CustomUser instance who will receive the notification.
        title: Short title for the notification.
        message: Full notification message body.
        notification_type: One of the NOTIFICATION_TYPE_CHOICES values
                           ('reminder', 'follow_up', 'stage_change',
                            'inactivity', 'system'). Defaults to 'system'.
        link: Optional URL the notification links to. Defaults to ''.

    Returns:
        The newly created Notification instance.
    """
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    logger.info(
        "Notification created for user '%s': %s",
        recipient.username,
        title,
    )
    return notification


def send_email_with_retry(
    recipient_email: str,
    subject: str,
    body: str,
    max_retries: int = 3,
) -> EmailLog:
    """
    Send an email and log the attempt, retrying on failure with exponential backoff.

    Creates an EmailLog record with status='pending', then attempts to send
    the email using Django's send_mail. On success the log is updated to
    status='sent'. On failure the retry_count is incremented and the next
    attempt is delayed by 2^retry_count seconds. After max_retries exhausted
    the log is set to status='failed' with the last error message stored.

    Args:
        recipient_email: Destination email address.
        subject: Email subject line.
        body: Plain-text email body.
        max_retries: Maximum number of send attempts. Defaults to 3.

    Returns:
        The EmailLog instance reflecting the final send status.
    """
    email_log = EmailLog.objects.create(
        recipient_email=recipient_email,
        subject=subject,
        status='pending',
    )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@crm.local')
    last_error = ''

    for attempt in range(1, max_retries + 1):
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            # Success — update log and return immediately
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save(update_fields=['status', 'sent_at', 'updated_at'])
            logger.info(
                "Email sent to '%s' (subject: %s) on attempt %d",
                recipient_email,
                subject,
                attempt,
            )
            return email_log

        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            email_log.retry_count = attempt
            email_log.save(update_fields=['retry_count', 'updated_at'])
            logger.warning(
                "Email to '%s' failed on attempt %d/%d: %s",
                recipient_email,
                attempt,
                max_retries,
                last_error,
            )

            if attempt < max_retries:
                # Exponential backoff: wait 2^attempt seconds before next retry
                wait_seconds = 2 ** attempt
                logger.debug(
                    "Waiting %d seconds before retry %d for '%s'",
                    wait_seconds,
                    attempt + 1,
                    recipient_email,
                )
                time.sleep(wait_seconds)

    # All retries exhausted
    email_log.status = 'failed'
    email_log.error_message = last_error
    email_log.save(update_fields=['status', 'error_message', 'updated_at'])
    logger.error(
        "Email to '%s' (subject: %s) failed after %d attempts: %s",
        recipient_email,
        subject,
        max_retries,
        last_error,
    )
    return email_log


def check_pending_reminders() -> int:
    """
    Find overdue follow-ups and notify their creators.

    Queries all active FollowUp records whose next_action_date is today or
    in the past. For each one, creates an in-app notification for the
    follow-up's created_by user and sends a reminder email.

    Returns:
        The number of reminders processed.
    """
    from ventas.models import FollowUp  # local import to avoid circular deps

    today = date.today()
    overdue_follow_ups = FollowUp.objects.filter(
        next_action_date__lte=today,
        is_active=True,
    ).select_related('created_by', 'opportunity', 'client')

    count = 0
    for follow_up in overdue_follow_ups:
        user = follow_up.created_by
        if user is None:
            continue

        # Build a human-readable entity label for the notification
        if follow_up.opportunity:
            entity_label = str(follow_up.opportunity)
        elif follow_up.client:
            entity_label = str(follow_up.client)
        else:
            entity_label = 'Sin entidad'

        title = 'Recordatorio de seguimiento pendiente'
        message = (
            f'Tienes un seguimiento pendiente para {entity_label}. '
            f'Fecha de acción: {follow_up.next_action_date}.'
        )

        create_notification(
            recipient=user,
            title=title,
            message=message,
            notification_type='reminder',
        )

        if user.email:
            send_email_with_retry(
                recipient_email=user.email,
                subject=title,
                body=message,
            )

        count += 1
        logger.info(
            "Reminder processed for follow-up id=%d (user: %s)",
            follow_up.pk,
            user.username,
        )

    logger.info("check_pending_reminders: %d reminders processed.", count)
    return count


def check_inactivity_reminders() -> int:
    """
    Detect stale opportunities and notify their assigned vendedores.

    Finds all active Opportunity records that are not in a closed stage and
    have had no FollowUp activity in the last 7 days (configurable via
    settings.INACTIVITY_REMINDER_DAYS). For each such opportunity, creates
    an inactivity notification for the assigned_vendedor and sends an email.

    Returns:
        The number of inactivity reminders processed.
    """
    from ventas.models import Opportunity, FollowUp  # local import

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
        # Check whether there is any follow-up within the inactivity window
        recent_follow_up_exists = FollowUp.objects.filter(
            opportunity=opportunity,
            is_active=True,
            date__gte=cutoff_date,
        ).exists()

        if recent_follow_up_exists:
            continue

        vendedor = opportunity.assigned_vendedor
        if vendedor is None:
            continue

        title = 'Oportunidad sin actividad reciente'
        message = (
            f'La oportunidad "{opportunity.title}" (cliente: {opportunity.client}) '
            f'no ha tenido seguimiento en los últimos {inactivity_days} días. '
            'Por favor, registra una actividad para mantener el pipeline actualizado.'
        )

        create_notification(
            recipient=vendedor,
            title=title,
            message=message,
            notification_type='inactivity',
        )

        if vendedor.email:
            send_email_with_retry(
                recipient_email=vendedor.email,
                subject=title,
                body=message,
            )

        count += 1
        logger.info(
            "Inactivity reminder processed for opportunity id=%d (vendedor: %s)",
            opportunity.pk,
            vendedor.username,
        )

    logger.info("check_inactivity_reminders: %d reminders processed.", count)
    return count
