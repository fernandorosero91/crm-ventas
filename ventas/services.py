"""
Business logic services for the Sales (Ventas) module.

This module provides service functions for:
- Stage transition management
- Pipeline summary calculations
- Weighted value calculations
- Role-based data scoping

Validates: Requirements 13.1-13.8, 15.1, 15.2, 16.3, 16.4
"""
from decimal import Decimal
from typing import Dict, List, Optional
from django.db.models import Sum, Count, Q, QuerySet
from django.contrib.auth import get_user_model

from .models import Opportunity, StageChange
from core.exceptions import StageTransitionError, InsufficientPermissionError

User = get_user_model()


def calculate_weighted_value(opportunity: Opportunity) -> Decimal:
    """
    Calculate the weighted value for an opportunity.
    
    Formula: estimated_value * probability / 100
    
    Args:
        opportunity: The Opportunity instance
        
    Returns:
        Decimal: The weighted value rounded to 2 decimal places
        
    Validates: Requirements 16.3, 16.4
    
    Example:
        >>> opp = Opportunity(estimated_value=Decimal('10000.00'), probability=75)
        >>> calculate_weighted_value(opp)
        Decimal('7500.00')
    """
    if opportunity.estimated_value is None or opportunity.probability is None:
        return Decimal('0.00')
    
    weighted = (opportunity.estimated_value * Decimal(opportunity.probability)) / Decimal('100')
    return weighted.quantize(Decimal('0.01'))


def get_opportunities_for_user(user: User) -> QuerySet:
    """
    Get opportunities visible to a user based on their role.
    
    Role-based data scoping:
    - Vendedor: sees only their own assigned opportunities
    - Supervisor: sees all opportunities from vendedores in their team
    - Administrator: sees all opportunities in the system
    
    Args:
        user: The CustomUser instance
        
    Returns:
        QuerySet: Filtered Opportunity queryset
        
    Validates: Requirements 15.1
    """
    if user.role == 'administrator':
        # Administrator sees all opportunities
        return Opportunity.objects.all()
    
    elif user.role == 'supervisor':
        # Supervisor sees all opportunities from their team members
        team_member_ids = user.get_team_members().values_list('id', flat=True)
        return Opportunity.objects.filter(
            Q(assigned_vendedor__in=team_member_ids) | Q(assigned_vendedor=user)
        )
    
    else:  # vendedor or any other role
        # Vendedor sees only their own opportunities
        return Opportunity.objects.filter(assigned_vendedor=user)


def get_pipeline_summary(user: User, queryset: Optional[QuerySet] = None) -> Dict:
    """
    Calculate pipeline summary statistics for opportunities.
    
    Returns count and total values per stage, plus overall totals.
    Applies role-based data scoping automatically.
    
    Args:
        user: The CustomUser instance (for role-based filtering)
        queryset: Optional pre-filtered queryset. If None, applies role-based filtering.
        
    Returns:
        Dict containing:
            - stages: List of dicts with stage info (name, display_name, count, total_value, weighted_value)
            - total_count: Total number of opportunities
            - total_estimated_value: Sum of all estimated values
            - total_weighted_value: Sum of all weighted values (estimated_value * probability / 100)
            
    Validates: Requirements 15.1, 15.2
    
    Example:
        >>> summary = get_pipeline_summary(user)
        >>> summary['total_count']
        25
        >>> summary['total_weighted_value']
        Decimal('125000.50')
        >>> summary['stages'][0]
        {
            'name': 'prospeccion',
            'display_name': 'Prospección',
            'count': 10,
            'total_value': Decimal('50000.00'),
            'weighted_value': Decimal('25000.00')
        }
    """
    # Get the base queryset with role-based filtering
    if queryset is None:
        queryset = get_opportunities_for_user(user)
    
    # Define all stages in order
    stage_definitions = [
        ('prospeccion', 'Prospección'),
        ('calificacion', 'Calificación'),
        ('propuesta', 'Propuesta'),
        ('negociacion', 'Negociación'),
        ('cierre_ganado', 'Cierre Ganado'),
        ('cierre_perdido', 'Cierre Perdido'),
    ]
    
    # Calculate summary for each stage
    stages_summary = []
    total_count = 0
    total_estimated_value = Decimal('0.00')
    total_weighted_value = Decimal('0.00')
    
    for stage_name, stage_display in stage_definitions:
        # Filter opportunities by stage
        stage_opportunities = queryset.filter(stage=stage_name)
        
        # Aggregate values for this stage
        stage_stats = stage_opportunities.aggregate(
            count=Count('id'),
            total_value=Sum('estimated_value'),
            weighted_value=Sum('weighted_value')
        )
        
        count = stage_stats['count'] or 0
        total_value = stage_stats['total_value'] or Decimal('0.00')
        weighted_value = stage_stats['weighted_value'] or Decimal('0.00')
        
        stages_summary.append({
            'name': stage_name,
            'display_name': stage_display,
            'count': count,
            'total_value': total_value,
            'weighted_value': weighted_value,
        })
        
        # Accumulate totals
        total_count += count
        total_estimated_value += total_value
        total_weighted_value += weighted_value
    
    return {
        'stages': stages_summary,
        'total_count': total_count,
        'total_estimated_value': total_estimated_value,
        'total_weighted_value': total_weighted_value,
    }


def advance_stage(
    opportunity: Opportunity,
    new_stage: str,
    user: User,
    actual_close_date=None,
    loss_reason: str = ''
) -> bool:
    """
    Advance an opportunity to a new stage with validation.
    
    Validates:
    - Vendedores cannot move backward in pipeline
    - Cierre Ganado requires actual_close_date
    - Cierre Perdido requires loss_reason (min 10 chars)
    - Creates StageChange audit record
    
    Args:
        opportunity: The Opportunity instance to update
        new_stage: The target stage (must be one of STAGE_CHOICES)
        user: The user making the change
        actual_close_date: Required when moving to 'cierre_ganado'
        loss_reason: Required when moving to 'cierre_perdido' (min 10 chars)
        
    Returns:
        bool: True if stage change was successful
        
    Raises:
        StageTransitionError: If the transition is invalid
        InsufficientPermissionError: If user lacks permission for the transition
        
    Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8
    """
    # Define stage order for validation
    stage_order = {
        'prospeccion': 0,
        'calificacion': 1,
        'propuesta': 2,
        'negociacion': 3,
        'cierre_ganado': 4,
        'cierre_perdido': 4,  # Terminal stages at same level
    }
    
    terminal_stages = ['cierre_ganado', 'cierre_perdido']
    current_stage = opportunity.stage
    
    # Validate new_stage is valid
    valid_stages = [choice[0] for choice in Opportunity.STAGE_CHOICES]
    if new_stage not in valid_stages:
        raise StageTransitionError(
            f"Etapa inválida: {new_stage}. Debe ser una de: {', '.join(valid_stages)}"
        )
    
    # Prevent changes to already closed opportunities (unless Supervisor/Admin)
    if current_stage in terminal_stages and user.role == 'vendedor':
        raise InsufficientPermissionError(
            "No tiene permisos para modificar oportunidades cerradas. "
            "Contacte a su supervisor."
        )
    
    # Check for backward movement
    current_order = stage_order.get(current_stage, 0)
    new_order = stage_order.get(new_stage, 0)
    
    is_backward = new_order < current_order and new_stage not in terminal_stages
    
    if is_backward and user.role == 'vendedor':
        raise InsufficientPermissionError(
            "Los vendedores no pueden retroceder etapas en el pipeline. "
            "Contacte a su supervisor si necesita hacer este cambio."
        )
    
    # Validate forward movement (no skipping stages unless going to terminal)
    if new_order > current_order + 1 and new_stage not in terminal_stages:
        raise StageTransitionError(
            "No puede saltar etapas. Debe avanzar secuencialmente o cerrar la oportunidad."
        )
    
    # Validate Cierre Ganado requirements
    if new_stage == 'cierre_ganado':
        if not actual_close_date:
            raise StageTransitionError(
                "Debe proporcionar la fecha real de cierre para marcar como 'Cierre Ganado'."
            )
        opportunity.actual_close_date = actual_close_date
    
    # Validate Cierre Perdido requirements
    if new_stage == 'cierre_perdido':
        if not loss_reason or len(loss_reason.strip()) < 10:
            raise StageTransitionError(
                "Debe proporcionar un motivo de pérdida de al menos 10 caracteres."
            )
        opportunity.loss_reason = loss_reason
        if not actual_close_date:
            # Use today's date if not provided
            from django.utils import timezone
            actual_close_date = timezone.now().date()
        opportunity.actual_close_date = actual_close_date
    
    # Clear actual_close_date if moving away from terminal stages
    if new_stage not in terminal_stages:
        opportunity.actual_close_date = None
        opportunity.loss_reason = ''
    
    # Create stage change audit record
    StageChange.objects.create(
        opportunity=opportunity,
        from_stage=current_stage,
        to_stage=new_stage,
        changed_by=user
    )
    
    # Update the opportunity stage
    opportunity.stage = new_stage
    opportunity.save()
    
    return True


def get_open_opportunities(user: User) -> QuerySet:
    """
    Get all open (non-closed) opportunities for a user.
    
    Open opportunities are those NOT in terminal stages (Cierre Ganado, Cierre Perdido).
    Applies role-based data scoping.
    
    Args:
        user: The CustomUser instance
        
    Returns:
        QuerySet: Filtered Opportunity queryset
        
    Validates: Requirements 15.1
    """
    opportunities = get_opportunities_for_user(user)
    return opportunities.exclude(
        stage__in=['cierre_ganado', 'cierre_perdido']
    )


def get_closed_opportunities(user: User) -> QuerySet:
    """
    Get all closed opportunities for a user.
    
    Closed opportunities are those in terminal stages (Cierre Ganado, Cierre Perdido).
    Applies role-based data scoping.
    
    Args:
        user: The CustomUser instance
        
    Returns:
        QuerySet: Filtered Opportunity queryset
        
    Validates: Requirements 15.1
    """
    opportunities = get_opportunities_for_user(user)
    return opportunities.filter(
        stage__in=['cierre_ganado', 'cierre_perdido']
    )
