# Ventas Services Module

## Overview

The `services.py` module provides business logic functions for the Sales (Ventas) module. It handles:

- **Pipeline summary calculations** with role-based data scoping
- **Weighted value calculations** for opportunities
- **Stage transition management** with validation
- **Role-based data filtering** (Vendedor, Supervisor, Administrator)

## Functions

### `calculate_weighted_value(opportunity: Opportunity) -> Decimal`

Calculates the weighted value for an opportunity using the formula:

```
weighted_value = estimated_value * probability / 100
```

**Example:**
```python
from ventas.services import calculate_weighted_value
from ventas.models import Opportunity

opp = Opportunity.objects.get(id=1)
weighted = calculate_weighted_value(opp)
# If estimated_value=10000.00 and probability=75
# Result: Decimal('7500.00')
```

**Validates:** Requirements 16.3, 16.4

---

### `get_opportunities_for_user(user: User) -> QuerySet`

Returns opportunities visible to a user based on their role:

- **Vendedor**: Only their own assigned opportunities
- **Supervisor**: All opportunities from their team members
- **Administrator**: All opportunities in the system

**Example:**
```python
from ventas.services import get_opportunities_for_user

opportunities = get_opportunities_for_user(request.user)
# Returns filtered QuerySet based on user role
```

**Validates:** Requirements 15.1

---

### `get_pipeline_summary(user: User, queryset: Optional[QuerySet] = None) -> Dict`

Calculates comprehensive pipeline statistics with role-based filtering.

**Returns:**
```python
{
    'stages': [
        {
            'name': 'prospeccion',
            'display_name': 'Prospección',
            'count': 10,
            'total_value': Decimal('50000.00'),
            'weighted_value': Decimal('25000.00')
        },
        # ... more stages
    ],
    'total_count': 25,
    'total_estimated_value': Decimal('250000.00'),
    'total_weighted_value': Decimal('125000.50')
}
```

**Example:**
```python
from ventas.services import get_pipeline_summary

# Get summary for current user
summary = get_pipeline_summary(request.user)

# Or with pre-filtered queryset
filtered_opps = Opportunity.objects.filter(stage='prospeccion')
summary = get_pipeline_summary(request.user, queryset=filtered_opps)
```

**Validates:** Requirements 15.1, 15.2

---

### `advance_stage(opportunity, new_stage, user, actual_close_date=None, loss_reason='') -> bool`

Advances an opportunity to a new stage with comprehensive validation.

**Validation Rules:**
- Vendedores cannot move backward in the pipeline
- Supervisors and Administrators can move backward
- Cannot skip sequential stages (except to terminal stages)
- `cierre_ganado` requires `actual_close_date`
- `cierre_perdido` requires `loss_reason` (min 10 characters)
- Creates audit trail in `StageChange` model

**Example:**
```python
from ventas.services import advance_stage
from django.utils import timezone

# Move to next stage
try:
    advance_stage(
        opportunity=opp,
        new_stage='calificacion',
        user=request.user
    )
except StageTransitionError as e:
    # Handle invalid transition
    print(e.message)

# Close as won
advance_stage(
    opportunity=opp,
    new_stage='cierre_ganado',
    user=request.user,
    actual_close_date=timezone.now().date()
)

# Close as lost
advance_stage(
    opportunity=opp,
    new_stage='cierre_perdido',
    user=request.user,
    loss_reason='Cliente eligió a la competencia por precio más bajo'
)
```

**Raises:**
- `StageTransitionError`: Invalid transition (skipping stages, missing required fields)
- `InsufficientPermissionError`: User lacks permission (e.g., Vendedor moving backward)

**Validates:** Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8

---

### `get_open_opportunities(user: User) -> QuerySet`

Returns all open (non-closed) opportunities for a user.

Open opportunities are those NOT in terminal stages (`cierre_ganado`, `cierre_perdido`).

**Example:**
```python
from ventas.services import get_open_opportunities

open_opps = get_open_opportunities(request.user)
count = open_opps.count()
```

**Validates:** Requirements 15.1

---

### `get_closed_opportunities(user: User) -> QuerySet`

Returns all closed opportunities for a user.

Closed opportunities are those in terminal stages (`cierre_ganado`, `cierre_perdido`).

**Example:**
```python
from ventas.services import get_closed_opportunities

closed_opps = get_closed_opportunities(request.user)
won_opps = closed_opps.filter(stage='cierre_ganado')
lost_opps = closed_opps.filter(stage='cierre_perdido')
```

**Validates:** Requirements 15.1

---

## Usage in Views

### Example: OpportunityListView with Pipeline Summary

```python
from django.views.generic import ListView
from ventas.models import Opportunity
from ventas.services import get_pipeline_summary, get_opportunities_for_user

class OpportunityListView(ListView):
    model = Opportunity
    template_name = 'ventas/opportunity_list.html'
    paginate_by = 15
    
    def get_queryset(self):
        return get_opportunities_for_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add pipeline summary to context
        context['pipeline_summary'] = get_pipeline_summary(
            self.request.user,
            queryset=self.get_queryset()
        )
        
        return context
```

### Example: Stage Transition View

```python
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from ventas.models import Opportunity
from ventas.services import advance_stage
from core.exceptions import StageTransitionError, InsufficientPermissionError

class OpportunityStageUpdateView(View):
    def post(self, request, pk):
        opportunity = get_object_or_404(Opportunity, pk=pk)
        new_stage = request.POST.get('stage')
        
        try:
            advance_stage(
                opportunity=opportunity,
                new_stage=new_stage,
                user=request.user,
                actual_close_date=request.POST.get('actual_close_date'),
                loss_reason=request.POST.get('loss_reason', '')
            )
            messages.success(request, 'Etapa actualizada correctamente')
        except StageTransitionError as e:
            messages.error(request, e.message)
        except InsufficientPermissionError as e:
            messages.error(request, e.message)
        
        return redirect('ventas:opportunity_detail', pk=pk)
```

## Role-Based Data Scoping

All service functions respect role-based access control:

| Role | Data Access |
|------|-------------|
| **Vendedor** | Only their own assigned opportunities |
| **Supervisor** | All opportunities from their team members (via `supervisor` FK) |
| **Administrator** | All opportunities in the system |

This is implemented in `get_opportunities_for_user()` and used by all other functions.

## Stage Transition Rules

### Sequential Stages

```
Prospección → Calificación → Propuesta → Negociación → Cierre Ganado/Perdido
```

### Rules

1. **Forward Movement**: Can only advance to the next immediate stage OR jump to a terminal stage
2. **Backward Movement**: Only Supervisors and Administrators can move backward
3. **Terminal Stages**: `cierre_ganado` and `cierre_perdido` are final states
4. **Closed Opportunities**: Only Supervisors and Administrators can modify closed opportunities

### Required Fields by Stage

| Stage | Required Fields |
|-------|----------------|
| `cierre_ganado` | `actual_close_date` |
| `cierre_perdido` | `loss_reason` (min 10 chars), `actual_close_date` (auto-set if not provided) |

## Error Handling

The services module uses custom exceptions from `core.exceptions`:

- **`StageTransitionError`**: Invalid stage transitions
- **`InsufficientPermissionError`**: User lacks required permissions

Always wrap service calls in try-except blocks in views:

```python
try:
    result = advance_stage(...)
except (StageTransitionError, InsufficientPermissionError) as e:
    # Handle error - display message to user
    messages.error(request, e.message)
```

## Testing

The service functions are designed to be easily testable:

```python
from django.test import TestCase
from ventas.services import calculate_weighted_value
from ventas.models import Opportunity
from decimal import Decimal

class ServicesTestCase(TestCase):
    def test_calculate_weighted_value(self):
        opp = Opportunity(
            estimated_value=Decimal('10000.00'),
            probability=75
        )
        result = calculate_weighted_value(opp)
        self.assertEqual(result, Decimal('7500.00'))
```

## Requirements Traceability

This module validates the following requirements:

- **13.1-13.8**: Opportunity Pipeline Management
- **15.1**: Sales Listing role-based filtering
- **15.2**: Pipeline summary with weighted values
- **16.3, 16.4**: Weighted value calculation invariant

## Notes

- All monetary values use `Decimal` for precision
- Weighted values are always rounded to 2 decimal places
- Stage changes create audit records in `StageChange` model
- The module is stateless - all functions are pure or have minimal side effects
