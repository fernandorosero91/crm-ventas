"""
Dashboard KPI service module.
Provides functions to calculate key performance indicators with role-based data scoping.

All KPI values are recalculated from the database on each call (no caching).
Role-based scoping:
  - Vendedor: sees only own assigned data
  - Supervisor: sees data from all vendedores in their team
  - Administrator: sees all data in the system
"""
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth, Coalesce
from decimal import Decimal

from clientes.models import Client
from ventas.models import Opportunity


def _get_user_filter(user):
    """
    Returns a Q filter for role-based data scoping on assigned_vendedor field.

    Args:
        user: CustomUser instance with role attribute.

    Returns:
        Q object to filter querysets by the user's role scope.
    """
    if user.role == 'administrator':
        return Q()
    elif user.role == 'supervisor':
        team_members = user.get_team_members()
        return Q(assigned_vendedor__in=team_members) | Q(assigned_vendedor=user)
    else:
        # vendedor sees only own data
        return Q(assigned_vendedor=user)


def get_kpi_data(user):
    """
    Calculate and return all dashboard KPIs scoped by user role.

    KPIs returned:
      - total_clients: count of active clients
      - open_opportunities: count of opportunities not in cierre_ganado or cierre_perdido
      - total_revenue: sum of estimated_value for cierre_ganado opportunities
      - conversion_rate: (cierre_ganado / total closed) * 100, rounded to 1 decimal
      - average_deal_size: mean of estimated_value for cierre_ganado opportunities

    Args:
        user: CustomUser instance.

    Returns:
        dict with KPI values.

    Validates: Requirements 17.1, 17.2, 17.3, 17.4
    """
    scope_filter = _get_user_filter(user)

    # Total active clients
    total_clients = Client.objects.filter(scope_filter).count()

    # Open opportunities (not closed)
    closed_stages = ['cierre_ganado', 'cierre_perdido']
    open_opportunities = Opportunity.objects.filter(
        scope_filter
    ).exclude(
        stage__in=closed_stages
    ).count()

    # Revenue: sum of estimated_value for cierre_ganado
    won_opportunities = Opportunity.objects.filter(
        scope_filter,
        stage='cierre_ganado'
    )
    total_revenue = won_opportunities.aggregate(
        total=Coalesce(Sum('estimated_value'), Decimal('0.00'))
    )['total']

    # Conversion rate: cierre_ganado / (cierre_ganado + cierre_perdido) * 100
    won_count = won_opportunities.count()
    lost_count = Opportunity.objects.filter(
        scope_filter,
        stage='cierre_perdido'
    ).count()
    total_closed = won_count + lost_count

    if total_closed == 0:
        conversion_rate = Decimal('0.0')
        average_deal_size = Decimal('0.00')
    else:
        conversion_rate = round((won_count / total_closed) * 100, 1)
        # Average deal size: mean of estimated_value for cierre_ganado
        average_deal_size = won_opportunities.aggregate(
            avg=Coalesce(Avg('estimated_value'), Decimal('0.00'))
        )['avg']

    return {
        'total_clients': total_clients,
        'open_opportunities': open_opportunities,
        'total_revenue': total_revenue,
        'conversion_rate': conversion_rate,
        'average_deal_size': round(average_deal_size, 2),
    }


def get_monthly_revenue(user, year):
    """
    Get monthly revenue from cierre_ganado opportunities for a given year.
    Revenue is the sum of estimated_value grouped by month.

    Args:
        user: CustomUser instance for role-based scoping.
        year: Integer year to filter by.

    Returns:
        list of dicts with 'month' (1-12) and 'revenue' keys for each month.
    """
    scope_filter = _get_user_filter(user)

    monthly_data = (
        Opportunity.objects.filter(
            scope_filter,
            stage='cierre_ganado',
            actual_close_date__year=year
        )
        .annotate(month=TruncMonth('actual_close_date'))
        .values('month')
        .annotate(revenue=Sum('estimated_value'))
        .order_by('month')
    )

    # Build a full 12-month result with zeros for months without data
    revenue_by_month = {item['month'].month: item['revenue'] for item in monthly_data}
    result = []
    for month_num in range(1, 13):
        result.append({
            'month': month_num,
            'revenue': revenue_by_month.get(month_num, Decimal('0.00')),
        })

    return result


def get_opportunities_by_stage(user):
    """
    Get count of open opportunities grouped by stage.
    Only includes non-closed stages (prospeccion, calificacion, propuesta, negociacion).

    Args:
        user: CustomUser instance for role-based scoping.

    Returns:
        list of dicts with 'stage' and 'count' keys.
    """
    scope_filter = _get_user_filter(user)
    closed_stages = ['cierre_ganado', 'cierre_perdido']

    stage_data = (
        Opportunity.objects.filter(scope_filter)
        .exclude(stage__in=closed_stages)
        .values('stage')
        .annotate(count=Count('id'))
        .order_by('stage')
    )

    return list(stage_data)


def get_monthly_new_clients(user, year):
    """
    Get count of new clients acquired per month for a given year.
    Based on client created_at date.

    Args:
        user: CustomUser instance for role-based scoping.
        year: Integer year to filter by.

    Returns:
        list of dicts with 'month' (1-12) and 'count' keys for each month.
    """
    scope_filter = _get_user_filter(user)

    monthly_data = (
        Client.objects.filter(
            scope_filter,
            created_at__year=year
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Build a full 12-month result with zeros for months without data
    clients_by_month = {item['month'].month: item['count'] for item in monthly_data}
    result = []
    for month_num in range(1, 13):
        result.append({
            'month': month_num,
            'count': clients_by_month.get(month_num, 0),
        })

    return result


def get_top_vendedores(limit=5):
    """
    Get top vendedores ranked by total cierre_ganado revenue for the current year.
    This function is not role-scoped as it shows a leaderboard.

    Args:
        limit: Maximum number of vendedores to return (default 5).

    Returns:
        list of dicts with 'vendedor_id', 'vendedor_name', and 'total_revenue' keys,
        ordered by total_revenue descending.
    """
    from django.utils import timezone

    current_year = timezone.now().year

    top_vendedores = (
        Opportunity.objects.filter(
            stage='cierre_ganado',
            actual_close_date__year=current_year
        )
        .values('assigned_vendedor__id', 'assigned_vendedor__first_name', 'assigned_vendedor__last_name')
        .annotate(total_revenue=Sum('estimated_value'))
        .order_by('-total_revenue')[:limit]
    )

    result = []
    for entry in top_vendedores:
        first_name = entry['assigned_vendedor__first_name'] or ''
        last_name = entry['assigned_vendedor__last_name'] or ''
        full_name = f"{first_name} {last_name}".strip() or 'Sin nombre'
        result.append({
            'vendedor_id': entry['assigned_vendedor__id'],
            'vendedor_name': full_name,
            'total_revenue': entry['total_revenue'],
        })

    return result
