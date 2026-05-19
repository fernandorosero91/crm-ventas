"""
Client models for the CRM system.
Defines Client and ClientStatusHistory models.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError

from core.models import BaseModel
from core.utils import validate_email_format, validate_phone_format


def _email_format_validator(value):
    """Django validator wrapper for validate_email_format."""
    if not validate_email_format(value):
        raise ValidationError(
            'Ingrese una dirección de correo electrónico válida (formato RFC 5322).'
        )


def _phone_format_validator(value):
    """Django validator wrapper for validate_phone_format."""
    if not validate_phone_format(value):
        raise ValidationError(
            'El teléfono solo puede contener dígitos, espacios, guiones, '
            'paréntesis y el símbolo +. Mínimo 7 caracteres.'
        )


class Client(BaseModel):
    """
    Represents a client/company in the CRM system.

    Inherits created_at, updated_at, is_active and ActiveManager from BaseModel.
    """
    company_name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        verbose_name='Empresa',
    )
    contact_name = models.CharField(
        max_length=150,
        validators=[MinLengthValidator(2)],
        verbose_name='Nombre de contacto',
    )
    email = models.EmailField(
        unique=True,
        validators=[_email_format_validator],
        verbose_name='Correo electrónico',
    )
    phone = models.CharField(
        max_length=20,
        validators=[_phone_format_validator],
        verbose_name='Teléfono',
    )
    address = models.TextField(
        blank=True,
        verbose_name='Dirección',
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Industria',
    )
    assigned_vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_clients',
        verbose_name='Vendedor asignado',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clients',
        verbose_name='Creado por',
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['assigned_vendedor', 'is_active']),
            models.Index(fields=['company_name']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.company_name} ({self.contact_name})"


class ClientStatusHistory(models.Model):
    """
    Audit record tracking status changes (active/inactive) for a Client.

    Does NOT inherit from BaseModel — it is a plain audit/history record.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Cliente',
    )
    previous_status = models.BooleanField(
        verbose_name='Estado anterior',
        help_text='True = activo, False = inactivo',
    )
    new_status = models.BooleanField(
        verbose_name='Nuevo estado',
        help_text='True = activo, False = inactivo',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Modificado por',
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de cambio',
    )
    reason = models.TextField(
        blank=True,
        verbose_name='Motivo',
    )

    class Meta:
        verbose_name = 'Historial de estado'
        verbose_name_plural = 'Historial de estados'
        ordering = ['-changed_at']

    def __str__(self):
        return f"Status change for {self.client} at {self.changed_at}"
