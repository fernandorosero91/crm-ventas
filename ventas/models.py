"""
Sales opportunity models for the CRM system.
Defines Opportunity model with pipeline stages and weighted value calculation.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from core.models import BaseModel


class Opportunity(BaseModel):
    """
    Represents a sales opportunity in the CRM system.
    
    Inherits created_at, updated_at, is_active and ActiveManager from BaseModel.
    
    The weighted_value is automatically calculated on save as:
    weighted_value = estimated_value * probability / 100
    
    New opportunities always start at 'prospeccion' stage.
    """
    
    STAGE_CHOICES = [
        ('prospeccion', 'Prospección'),
        ('calificacion', 'Calificación'),
        ('propuesta', 'Propuesta'),
        ('negociacion', 'Negociación'),
        ('cierre_ganado', 'Cierre Ganado'),
        ('cierre_perdido', 'Cierre Perdido'),
    ]
    
    title = models.CharField(
        max_length=150,
        validators=[MinLengthValidator(3)],
        verbose_name='Título',
    )
    
    client = models.ForeignKey(
        'clientes.Client',
        on_delete=models.CASCADE,
        related_name='opportunities',
        verbose_name='Cliente',
    )
    
    estimated_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor estimado',
        help_text='Valor estimado de la oportunidad (debe ser mayor a 0)',
    )
    
    probability = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Probabilidad (%)',
        help_text='Probabilidad de cierre entre 0 y 100',
    )
    
    expected_close_date = models.DateField(
        verbose_name='Fecha esperada de cierre',
    )
    
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='prospeccion',
        verbose_name='Etapa',
    )
    
    assigned_vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_opportunities',
        verbose_name='Vendedor asignado',
    )
    
    actual_close_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha real de cierre',
        help_text='Fecha en que se cerró la oportunidad (ganada o perdida)',
    )
    
    loss_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de pérdida',
        help_text='Razón por la cual se perdió la oportunidad',
    )
    
    weighted_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False,
        verbose_name='Valor ponderado',
        help_text='Calculado automáticamente: estimated_value * probability / 100',
    )
    
    class Meta:
        verbose_name = 'Oportunidad'
        verbose_name_plural = 'Oportunidades'
        ordering = ['expected_close_date']
        indexes = [
            models.Index(fields=['assigned_vendedor', 'stage', 'is_active']),
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['expected_close_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.client.company_name}"
    
    def save(self, *args, **kwargs):
        """
        Override save to compute weighted_value automatically.
        
        weighted_value = estimated_value * probability / 100
        
        Also ensures new opportunities always start at 'prospeccion' stage.
        """
        # Ensure new opportunities start at 'prospeccion' stage
        if self.pk is None and not self.stage:
            self.stage = 'prospeccion'
        
        # Calculate weighted value
        if self.estimated_value is not None and self.probability is not None:
            self.weighted_value = (self.estimated_value * Decimal(self.probability)) / Decimal('100')
        
        super().save(*args, **kwargs)


class StageChange(models.Model):
    """
    Model for tracking stage transitions in opportunities.
    Created automatically whenever an opportunity moves between pipeline stages.
    
    This model does NOT inherit from BaseModel as it's an audit/history table
    that should never be soft-deleted or modified after creation.
    
    Fields:
        opportunity: FK to the opportunity whose stage changed
        from_stage: The previous stage value
        to_stage: The new stage value
        changed_by: FK to the user who made the change
        changed_at: Timestamp when the change occurred
    
    Validates: Requirements 13.2
    """
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='stage_changes',
        verbose_name='Oportunidad'
    )
    from_stage = models.CharField(
        max_length=20,
        verbose_name='Etapa Anterior'
    )
    to_stage = models.CharField(
        max_length=20,
        verbose_name='Nueva Etapa'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stage_changes_made',
        verbose_name='Cambiado Por'
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Cambio'
    )
    
    class Meta:
        verbose_name = 'Cambio de Etapa'
        verbose_name_plural = 'Cambios de Etapa'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['opportunity', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.opportunity} - {self.from_stage} → {self.to_stage} ({self.changed_at.strftime('%Y-%m-%d %H:%M')})"


class FollowUp(BaseModel):
    """
    Represents a follow-up interaction with a client or opportunity.
    
    Can be linked to an opportunity, a client, or both.
    Inherits created_at, updated_at, is_active and ActiveManager from BaseModel.
    """
    TYPE_CHOICES = [
        ('call', 'Llamada'),
        ('email', 'Email'),
        ('meeting', 'Reunión'),
        ('other', 'Otro'),
    ]
    
    opportunity = models.ForeignKey(
        'Opportunity',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='follow_ups',
        verbose_name='Oportunidad',
    )
    client = models.ForeignKey(
        'clientes.Client',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='follow_ups',
        verbose_name='Cliente',
    )
    follow_up_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Tipo de seguimiento',
    )
    date = models.DateTimeField(
        verbose_name='Fecha',
    )
    notes = models.TextField(
        validators=[MinLengthValidator(10)],
        verbose_name='Notas',
        help_text='Mínimo 10 caracteres',
    )
    next_action_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de próxima acción',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_follow_ups',
        verbose_name='Creado por',
    )

    class Meta:
        verbose_name = 'Seguimiento'
        verbose_name_plural = 'Seguimientos'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['opportunity', 'date']),
            models.Index(fields=['next_action_date', 'is_active']),
        ]

    def __str__(self):
        entity = self.opportunity or self.client or 'Sin entidad'
        return f"{self.get_follow_up_type_display()} - {entity} - {self.date}"

    def clean(self):
        """
        Validate that the follow-up is associated with at least one entity.
        """
        super().clean()
        if not self.opportunity and not self.client:
            raise ValidationError(
                'El seguimiento debe estar asociado al menos con un cliente o una oportunidad.'
            )
