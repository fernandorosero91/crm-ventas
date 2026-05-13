"""
Forms for the clientes app.
Provides validated forms for Client creation and update.
"""
from django import forms
from django.conf import settings

from .models import Client
from core.utils import sanitize_input


class ClientForm(forms.ModelForm):
    """
    ModelForm for creating and updating Client records.
    Includes input sanitization and duplicate email validation.
    """

    class Meta:
        model = Client
        fields = [
            'company_name',
            'contact_name',
            'email',
            'phone',
            'address',
            'industry',
            'assigned_vendedor',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
            }),
            'contact_name': forms.TextInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
            }),
            'email': forms.EmailInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
            }),
            'phone': forms.TextInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
            }),
            'address': forms.Textarea(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
                'rows': 3,
            }),
            'industry': forms.TextInput(attrs={
                'class': (
                    'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 '
                    'rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2c6e8a] '
                    'focus:border-[#2c6e8a] transition-colors duration-200 peer'
                ),
                'placeholder': ' ',
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
        # Accept the requesting user to scope the vendedor queryset
        self.requesting_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Restrict assigned_vendedor to active vendedores only
        self.fields['assigned_vendedor'].queryset = User.objects.filter(
            role='vendedor',
            is_active=True,
        )
        self.fields['assigned_vendedor'].required = False
        self.fields['assigned_vendedor'].empty_label = '— Seleccionar vendedor —'

        # address and industry are optional
        self.fields['address'].required = False
        self.fields['industry'].required = False

    # ------------------------------------------------------------------ #
    # Sanitization                                                         #
    # ------------------------------------------------------------------ #

    def clean_company_name(self):
        value = self.cleaned_data.get('company_name', '')
        return sanitize_input(value)

    def clean_contact_name(self):
        value = self.cleaned_data.get('contact_name', '')
        return sanitize_input(value)

    def clean_address(self):
        value = self.cleaned_data.get('address', '')
        return sanitize_input(value) if value else value

    def clean_industry(self):
        value = self.cleaned_data.get('industry', '')
        return sanitize_input(value) if value else value

    # ------------------------------------------------------------------ #
    # Duplicate email validation                                           #
    # ------------------------------------------------------------------ #

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        qs = Client.all_objects.filter(email=email)
        # On update, exclude the current instance
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                'Ya existe un cliente registrado con este correo electrónico.'
            )
        return email
