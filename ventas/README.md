# Ventas Module - User Guide

## Overview
The Ventas (Sales) module provides comprehensive opportunity management, pipeline visualization, and follow-up tracking for the CRM system.

## Features

### 1. Opportunity Management
- Create, read, update, and delete sales opportunities
- Automatic weighted value calculation
- Role-based access control
- Stage-based pipeline management

### 2. Pipeline Stages
1. **Prospección** - Initial opportunity identification
2. **Calificación** - Qualification and fit assessment
3. **Propuesta** - Solution presentation and quotation
4. **Negociación** - Terms and conditions discussion
5. **Cierre Ganado** - Successfully closed deal
6. **Cierre Perdido** - Lost opportunity

### 3. Follow-up Tracking
- Record interactions with clients and opportunities
- Types: Call, Email, Meeting, Other
- Set next action dates for reminders
- View chronological timeline

### 4. Pipeline Visualization
- Kanban-style board view
- Opportunities grouped by stage
- Summary cards with counts and values
- Color-coded stages

## URL Routes

### Opportunities
- List: `/ventas/`
- Create: `/ventas/nueva/`
- Detail: `/ventas/<id>/`
- Update: `/ventas/<id>/editar/`
- Delete: `/ventas/<id>/eliminar/`
- Stage Change: `/ventas/<id>/cambiar-etapa/` (AJAX)
- Pipeline View: `/ventas/pipeline/`

### Follow-ups
- Create: `/ventas/seguimiento/nuevo/`
- Update: `/ventas/seguimiento/<id>/editar/`
- Delete: `/ventas/seguimiento/<id>/eliminar/`

## Role-Based Access

### Vendedor
- View own assigned opportunities
- Create new opportunities
- Update own opportunities
- Cannot move backward in pipeline
- Cannot modify closed opportunities

### Supervisor
- View all opportunities from team members
- Create opportunities for team
- Update team opportunities
- Can move backward in pipeline
- Can modify closed opportunities

### Administrator
- View all opportunities in system
- Full CRUD permissions
- Can move backward in pipeline
- Can modify closed opportunities

## Business Rules

### Opportunity Creation
- Stage automatically set to 'Prospección'
- Vendedor auto-assigned if not specified
- Estimated value must be > 0
- Probability must be 0-100
- Expected close date cannot be in the past

### Stage Transitions
- Vendedores can only move forward
- Supervisors/Admins can move backward
- Cannot skip stages (except to terminal stages)
- **Cierre Ganado** requires:
  - Actual close date
- **Cierre Perdido** requires:
  - Loss reason (min 10 characters)
  - Actual close date (auto-set if not provided)

### Weighted Value
- Automatically calculated: `estimated_value * probability / 100`
- Updated on every save
- Used for pipeline value assessment

### Follow-ups
- Must be linked to at least one entity (opportunity or client)
- Notes must be at least 10 characters
- Next action date cannot be in the past
- Created by user is automatically recorded

## Advanced Features

### Smart Search
- Search by opportunity ID (numeric)
- Search by title (partial match)
- Search by client company name (partial match)
- Minimum 2 characters required

### Advanced Filters
- Stage filter
- Vendedor filter (Admin/Supervisor only)
- Client filter
- Date range (expected close date)
- Value range (estimated value)

### Sortable Columns
- Title
- Client
- Value (estimated)
- Stage
- Expected close date
- Toggle ASC/DESC with visual indicators

### Pagination
- Configurable page sizes: 15, 30, 50
- Maintains filter and sort state
- Shows total count and page info

## API Endpoints

### Stage Change (AJAX)
**POST** `/ventas/<id>/cambiar-etapa/`

Request body:
```json
{
  "stage": "calificacion",
  "actual_close_date": "2026-05-15",  // Required for cierre_ganado
  "loss_reason": "Cliente eligió competidor"  // Required for cierre_perdido
}
```

Response (success):
```json
{
  "success": true,
  "message": "Etapa cambiada a Calificación exitosamente.",
  "new_stage": "calificacion",
  "new_stage_display": "Calificación"
}
```

Response (error):
```json
{
  "success": false,
  "error": "Los vendedores no pueden retroceder etapas en el pipeline."
}
```

## Models

### Opportunity
```python
{
  "id": 1,
  "title": "Venta Software ERP",
  "client": Client object,
  "estimated_value": 50000.00,
  "probability": 75,
  "expected_close_date": "2026-06-30",
  "stage": "propuesta",
  "assigned_vendedor": User object,
  "actual_close_date": null,
  "loss_reason": "",
  "weighted_value": 37500.00,  // Auto-calculated
  "created_at": "2026-05-01 10:00:00",
  "updated_at": "2026-05-12 14:30:00",
  "is_active": true
}
```

### FollowUp
```python
{
  "id": 1,
  "opportunity": Opportunity object,
  "client": Client object,
  "follow_up_type": "meeting",
  "date": "2026-05-10 15:00:00",
  "notes": "Reunión de presentación de propuesta. Cliente interesado.",
  "next_action_date": "2026-05-20",
  "created_by": User object,
  "created_at": "2026-05-10 16:00:00",
  "is_active": true
}
```

### StageChange
```python
{
  "id": 1,
  "opportunity": Opportunity object,
  "from_stage": "calificacion",
  "to_stage": "propuesta",
  "changed_by": User object,
  "changed_at": "2026-05-12 14:30:00"
}
```

## Services

### `get_opportunities_for_user(user)`
Returns opportunities visible to user based on role.

### `get_pipeline_summary(user, queryset=None)`
Returns pipeline statistics:
```python
{
  "stages": [
    {
      "name": "prospeccion",
      "display_name": "Prospección",
      "count": 10,
      "total_value": 50000.00,
      "weighted_value": 25000.00
    },
    ...
  ],
  "total_count": 25,
  "total_estimated_value": 250000.00,
  "total_weighted_value": 125000.00
}
```

### `advance_stage(opportunity, new_stage, user, actual_close_date=None, loss_reason='')`
Validates and executes stage transition. Returns `True` on success.

Raises:
- `StageTransitionError` - Invalid transition
- `InsufficientPermissionError` - User lacks permission

### `calculate_weighted_value(opportunity)`
Returns weighted value: `estimated_value * probability / 100`

### `get_open_opportunities(user)`
Returns non-closed opportunities for user.

### `get_closed_opportunities(user)`
Returns closed opportunities (Cierre Ganado/Perdido) for user.

## Forms

### OpportunityForm
- Fields: title, client, estimated_value, probability, expected_close_date, assigned_vendedor
- Validation: All business rules enforced
- Sanitization: Title field sanitized
- Role-based queryset scoping

### FollowUpForm
- Fields: opportunity, client, follow_up_type, date, notes, next_action_date
- Validation: At least one entity required, notes min 10 chars
- Sanitization: Notes field sanitized
- Role-based queryset scoping

## Templates

### opportunity_list.html
- Pipeline summary cards
- Advanced search and filters
- Sortable table
- Pagination
- Empty state

### opportunity_form.html
- Floating label inputs
- Real-time validation
- Weighted value display (edit mode)
- Responsive layout

### opportunity_detail.html
- Two-column layout
- Stage management buttons
- Stage change modals
- Follow-ups timeline
- Stage change history
- Quick actions sidebar

### followup_form.html
- Clean form layout
- Type selector and date picker
- Notes textarea
- Next action date field

### opportunity_pipeline.html
- Kanban-style board
- 6 stage columns
- Opportunity cards
- Pipeline summary
- Legend and tips

## JavaScript Features

### Real-time Form Validation
- Validates on blur event
- Shows error messages dynamically
- Visual feedback (red/green borders)
- Prevents invalid form submission

### AJAX Stage Change
- No page reload required
- Handles terminal stage requirements
- Shows confirmation modals
- Displays success/error messages

### Modal Management
- Backdrop click to close
- Escape key to close
- Smooth animations
- Accessible controls

## Security Features

### Input Sanitization
- HTML tags stripped
- Special characters escaped
- Script content removed
- XSS prevention

### CSRF Protection
- All forms include CSRF token
- AJAX requests include CSRF header
- Django middleware validation

### SQL Injection Prevention
- ORM used for all queries
- No raw SQL execution
- Parameterized queries

### Access Control
- LoginRequiredMixin on all views
- RoleRequiredMixin for role checks
- OwnershipRequiredMixin for edit permissions
- Role-based queryset filtering

## Performance Optimizations

### Database Indexes
- `[assigned_vendedor, stage, is_active]`
- `[client, is_active]`
- `[expected_close_date]`
- `[opportunity, date]` (FollowUp)
- `[next_action_date, is_active]` (FollowUp)
- `[opportunity, -changed_at]` (StageChange)

### Query Optimization
- `select_related()` for foreign keys
- Efficient role-based filtering
- Pagination to limit result sets
- Aggregate queries for summaries

## Error Handling

### Form Validation Errors
- Displayed inline with fields
- Non-field errors at top of form
- User-friendly error messages
- Maintains form state on error

### Stage Transition Errors
- `StageTransitionError` - Business rule violation
- `InsufficientPermissionError` - Permission denied
- JSON error response for AJAX
- User-friendly error messages

### 404 Errors
- Raised when opportunity not found
- Raised when user lacks access
- Django's default 404 handler

### 403 Errors
- Raised on permission denied
- Raised on ownership violation
- Django's default 403 handler

## Best Practices

### Creating Opportunities
1. Always assign to a client
2. Set realistic probability
3. Use appropriate stage
4. Assign to correct vendedor
5. Set expected close date

### Managing Pipeline
1. Update stage regularly
2. Record follow-ups after interactions
3. Set next action dates
4. Document loss reasons
5. Keep probability updated

### Follow-up Tracking
1. Record all client interactions
2. Use appropriate type
3. Write detailed notes (min 10 chars)
4. Set next action dates
5. Link to opportunity when possible

## Troubleshooting

### Cannot change stage
- Check user role (vendedor cannot move backward)
- Check if opportunity is closed (vendedor cannot modify)
- Ensure required fields provided (close date, loss reason)

### Cannot see opportunities
- Check role-based access
- Verify vendedor assignment
- Check is_active status

### Form validation errors
- Check all required fields
- Verify estimated_value > 0
- Verify probability 0-100
- Verify expected_close_date not in past

### Follow-up creation fails
- Ensure at least one entity selected
- Verify notes length >= 10 chars
- Check next_action_date not in past

## Integration with Other Modules

### Clientes Module
- Opportunities linked to clients
- Follow-ups can be linked to clients
- Client detail shows related opportunities

### Users Module
- Opportunities assigned to vendedores
- Follow-ups track created_by
- Role-based access control
- Supervisor-team relationship

### Dashboard Module (Future)
- KPIs from opportunity data
- Pipeline analytics
- Revenue forecasting
- Conversion rates

### Notifications Module (Future)
- Follow-up reminders
- Stage change notifications
- Inactivity alerts

### Reports Module (Future)
- Sales reports
- Pipeline reports
- Vendedor performance
- Export to PDF/Excel

---

For technical documentation, see `README_SERVICES.md` and `DEV3_COMPLETION_SUMMARY.md`.
