"""
Forms for the ventas app.
Provides validated forms for Opportunity and FollowUp creation and update.
"""
from django import forms
from django.conf import settings
from django.utils import timezone
from datetime import date

from .models import Opportunity, FollowUp
from core.utils import sanitize_input


class OpportunityForm(forms.ModelForm):
    """
    ModelForm for creating and updating Opportunity records.
    Includes real-time validation for estimated_value, probability, and expected_close_date.
    """

    class Meta:
        model = Opportunity
        fields = [
            'title',
            'client',
            'estimated_value',
            'probability',
            'expected_close_date',
            'assigned_vendedor',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
            }),
            'client': forms.Select(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200'
                ),
            }),
            'estimated_value': forms.NumberInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
                'step': '0.01',
                'min': '0.01',
            }),
            'probability': forms.NumberInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
                'min': '0',
                'max': '100',
            }),
            'expected_close_date': forms.DateInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
                'type': 'date',
            }),
            'assigned_vendedor': forms.Select(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200'
                ),
            }),
        }

    def __init__(self, *args, **kwargs):
        # Accept the requesting user to scope the queryset
        self.requesting_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from django.contrib.auth import get_user_model
        from clientes.models import Client
        
        User = get_user_model()

        # Restrict assigned_vendedor to active vendedores only
        self.fields['assigned_vendedor'].queryset = User.objects.filter(
            role='vendedor',
            is_active=True,
        )
        self.fields['assigned_vendedor'].required = False
        self.fields['assigned_vendedor'].empty_label = '— Seleccionar vendedor —'

        # Restrict client to active clients only, scoped by user role
        if self.requesting_user:
            if self.requesting_user.role == 'administrator':
                client_qs = Client.objects.all()
            elif self.requesting_user.role == 'supervisor':
                team_ids = list(self.requesting_user.get_team_members().values_list('id', flat=True))
                team_ids.append(self.requesting_user.id)
                client_qs = Client.objects.filter(assigned_vendedor__in=team_ids)
            else:  # vendedor
                client_qs = Client.objects.filter(assigned_vendedor=self.requesting_user)
        else:
            client_qs = Client.objects.all()

        self.fields['client'].queryset = client_qs
        self.fields['client'].empty_label = '— Seleccionar cliente —'

    # ------------------------------------------------------------------ #
    # Sanitization                                                         #
    # ------------------------------------------------------------------ #

    def clean_title(self):
        value = self.cleaned_data.get('title', '')
        return sanitize_input(value)

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #

    def clean_estimated_value(self):
        """Validate that estimated_value is positive (> 0)."""
        value = self.cleaned_data.get('estimated_value')
        if value is not None and value <= 0:
            raise forms.ValidationError(
                'El valor estimado debe ser mayor a 0.'
            )
        return value

    def clean_probability(self):
        """Validate that probability is between 0 and 100."""
        value = self.cleaned_data.get('probability')
        if value is not None and (value < 0 or value > 100):
            raise forms.ValidationError(
                'La probabilidad debe estar entre 0 y 100.'
            )
        return value

    def clean_expected_close_date(self):
        """Validate that expected_close_date is not in the past."""
        value = self.cleaned_data.get('expected_close_date')
        if value is not None and value < date.today():
            raise forms.ValidationError(
                'La fecha esperada de cierre no puede estar en el pasado.'
            )
        return value

    def clean_client(self):
        """Validate that the selected client exists and is active."""
        client = self.cleaned_data.get('client')
        if client and not client.is_active:
            raise forms.ValidationError(
                'El cliente seleccionado está inactivo. Por favor, seleccione un cliente activo.'
            )
        return client


class FollowUpForm(forms.ModelForm):
    """
    ModelForm for creating and updating FollowUp records.
    Includes validation for notes length and next_action_date.
    """

    class Meta:
        model = FollowUp
        fields = [
            'opportunity',
            'client',
            'follow_up_type',
            'date',
            'notes',
            'next_action_date',
        ]
        widgets = {
            'opportunity': forms.Select(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200'
                ),
            }),
            'client': forms.Select(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200'
                ),
            }),
            'follow_up_type': forms.Select(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200'
                ),
            }),
            'date': forms.DateTimeInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
                'type': 'datetime-local',
            }),
            'notes': forms.Textarea(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
                'rows': 4,
            }),
            'next_action_date': forms.DateInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Accept the requesting user to scope the queryset
        self.requesting_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Make opportunity and client optional (at least one required)
        self.fields['opportunity'].required = False
        self.fields['client'].required = False
        self.fields['next_action_date'].required = False

        # Scope querysets by user role
        if self.requesting_user:
            from clientes.models import Client
            
            if self.requesting_user.role == 'administrator':
                opportunity_qs = Opportunity.objects.all()
                client_qs = Client.objects.all()
            elif self.requesting_user.role == 'supervisor':
                team_ids = list(self.requesting_user.get_team_members().values_list('id', flat=True))
                team_ids.append(self.requesting_user.id)
                opportunity_qs = Opportunity.objects.filter(assigned_vendedor__in=team_ids)
                client_qs = Client.objects.filter(assigned_vendedor__in=team_ids)
            else:  # vendedor
                opportunity_qs = Opportunity.objects.filter(assigned_vendedor=self.requesting_user)
                client_qs = Client.objects.filter(assigned_vendedor=self.requesting_user)
        else:
            opportunity_qs = Opportunity.objects.all()
            client_qs = Client.objects.all()

        self.fields['opportunity'].queryset = opportunity_qs
        self.fields['opportunity'].empty_label = '— Seleccionar oportunidad (opcional) —'
        
        self.fields['client'].queryset = client_qs
        self.fields['client'].empty_label = '— Seleccionar cliente (opcional) —'

    def clean_notes(self):
        """Sanitize notes input."""
        value = self.cleaned_data.get('notes', '')
        return sanitize_input(value)

    def clean_next_action_date(self):
        """Validate that next_action_date is not in the past."""
        value = self.cleaned_data.get('next_action_date')
        if value is not None and value < date.today():
            raise forms.ValidationError(
                'La fecha de próxima acción debe ser hoy o una fecha futura.'
            )
        return value

    def clean(self):
        """Validate that at least one entity (opportunity or client) is selected."""
        cleaned_data = super().clean()
        opportunity = cleaned_data.get('opportunity')
        client = cleaned_data.get('client')

        if not opportunity and not client:
            raise forms.ValidationError(
                'El seguimiento debe estar asociado al menos con un cliente o una oportunidad.'
            )

        return cleaned_data
