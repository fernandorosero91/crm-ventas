from django.db import models
from django.conf import settings

from core.models import BaseModel


class Notification(BaseModel):
    """
    In-app notification for a user.

    Stores a message directed at a specific recipient with an optional
    deep-link and a type that categorises the notification.
    """

    NOTIFICATION_TYPE_CHOICES = [
        ('reminder', 'Recordatorio'),
        ('follow_up', 'Seguimiento'),
        ('stage_change', 'Cambio de etapa'),
        ('inactivity', 'Inactividad'),
        ('system', 'Sistema'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinatario',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Título',
    )
    message = models.TextField(
        verbose_name='Mensaje',
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Leída',
    )
    link = models.URLField(
        blank=True,
        verbose_name='Enlace',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='system',
        verbose_name='Tipo',
    )

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.recipient} – {self.title}"


class EmailLog(BaseModel):
    """
    Audit log for every outbound email attempt.

    Tracks delivery status, retry count, and any error messages so that
    failed emails can be retried and diagnosed.
    """

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
    ]

    recipient_email = models.EmailField(
        verbose_name='Correo destinatario',
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='Asunto',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado',
    )
    retry_count = models.IntegerField(
        default=0,
        verbose_name='Intentos',
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Enviado en',
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de error',
    )

    class Meta:
        verbose_name = 'Registro de correo'
        verbose_name_plural = 'Registros de correo'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.recipient_email} – {self.subject} ({self.get_status_display()})"
