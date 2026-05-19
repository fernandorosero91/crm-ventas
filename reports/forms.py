"""
Forms for the reports app.
Provides ReportFilterForm for filtering and generating reports.
"""
from django import forms


INPUT_CLASS = (
    'block w-full px-4 py-2.5 text-sm text-gray-900 bg-white border border-gray-300 '
    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
    'focus:border-[#2c6e8a] transition-colors duration-200'
)

# Status/stage choices per report type (used in JS to swap options dynamically)
CLIENT_STATUS_CHOICES = [
    ('', 'Todos'),
    ('active', 'Activo'),
    ('inactive', 'Inactivo'),
]

OPPORTUNITY_STAGE_CHOICES = [
    ('', 'Todas las etapas'),
    ('prospeccion', 'Prospección'),
    ('calificacion', 'Calificación'),
    ('propuesta', 'Propuesta'),
    ('negociacion', 'Negociación'),
    ('cierre_ganado', 'Cierre Ganado'),
    ('cierre_perdido', 'Cierre Perdido'),
]

FOLLOW_UP_TYPE_CHOICES = [
    ('', 'Todos los tipos'),
    ('call', 'Llamada'),
    ('email', 'Email'),
    ('meeting', 'Reunión'),
    ('other', 'Otro'),
]

# Combined superset for the status field (view filters by report_type)
ALL_STATUS_CHOICES = (
    CLIENT_STATUS_CHOICES
    + [c for c in OPPORTUNITY_STAGE_CHOICES if c[0]]
    + [c for c in FOLLOW_UP_TYPE_CHOICES if c[0]]
)


class ReportFilterForm(forms.Form):
    """
    Filter form for generating CRM reports.

    Fields
    ------
    report_type : ChoiceField
        Which entity to report on (clients, opportunities, followups, sales).
    date_from : DateField (optional)
        Start of the date range filter.
    date_to : DateField (optional)
        End of the date range filter.
    seller : ModelChoiceField (optional)
        Filter results by assigned vendedor / creator.
    status : ChoiceField (optional)
        Status / stage / type filter — meaning varies by report_type.
    format : ChoiceField
        Output format: preview (table), pdf, excel, csv.
    """

    REPORT_TYPE_CHOICES = [
        ('clients', 'Clientes'),
        ('opportunities', 'Oportunidades'),
        ('followups', 'Seguimientos'),
        ('sales', 'Ventas Cerradas'),
    ]

    FORMAT_CHOICES = [
        ('preview', 'Vista Previa'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        label='Tipo de reporte',
        widget=forms.Select(attrs={'class': INPUT_CLASS, 'id': 'id_report_type'}),
    )

    date_from = forms.DateField(
        required=False,
        label='Fecha desde',
        widget=forms.DateInput(
            attrs={'class': INPUT_CLASS, 'type': 'date'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d'],
    )

    date_to = forms.DateField(
        required=False,
        label='Fecha hasta',
        widget=forms.DateInput(
            attrs={'class': INPUT_CLASS, 'type': 'date'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d'],
    )

    seller = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False,
        label='Vendedor',
        empty_label='— Todos los vendedores —',
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
    )

    status = forms.ChoiceField(
        choices=[('', 'Todos')] + ALL_STATUS_CHOICES,
        required=False,
        label='Estado / Etapa',
        widget=forms.Select(attrs={'class': INPUT_CLASS, 'id': 'id_status'}),
    )

    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        label='Formato',
        initial='preview',
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        # Accept the requesting user to scope the seller queryset
        self.requesting_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = self.requesting_user
        if user is not None:
            if user.role == 'administrator':
                qs = User.objects.filter(role='vendedor', is_active=True)
            elif user.role == 'supervisor':
                qs = user.get_team_members()
            else:
                # Vendedor: only themselves
                qs = User.objects.filter(pk=user.pk)
        else:
            qs = User.objects.none()

        self.fields['seller'].queryset = qs

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(
                'La fecha "desde" no puede ser posterior a la fecha "hasta".'
            )
        return cleaned
