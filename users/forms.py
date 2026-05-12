"""
Forms for user registration, authentication, and profile management.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from .models import CustomUser
from core.utils import sanitize_input, validate_phone_format
from PIL import Image
from django.conf import settings


class RegistrationForm(UserCreationForm):
    """
    Form for user registration with role assignment.
    Only administrators can register new users.
    """
    email = forms.EmailField(
        required=True,
        max_length=254,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nombre'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Apellido'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de usuario'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Contraseña (mínimo 8 caracteres)'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirmar contraseña'
        })
    
    def clean_username(self):
        """Validate username uniqueness and sanitize input."""
        username = self.cleaned_data.get('username')
        username = sanitize_input(username)
        
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        
        return username
    
    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        
        return email
    
    def clean_password1(self):
        """Validate password length."""
        password = self.cleaned_data.get('password1')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if len(password) > 128:
            raise ValidationError('La contraseña no puede exceder 128 caracteres.')
        
        return password
    
    def clean_first_name(self):
        """Sanitize first name."""
        return sanitize_input(self.cleaned_data.get('first_name'))
    
    def clean_last_name(self):
        """Sanitize last name."""
        return sanitize_input(self.cleaned_data.get('last_name'))


class CustomLoginForm(AuthenticationForm):
    """
    Custom login form with enhanced styling.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nombre de usuario o correo',
            'autocomplete': 'username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    Role field is not editable by users.
    """
    email = forms.EmailField(
        required=True,
        max_length=254,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    
    phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+57 300 123 4567'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Apellido'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/jpeg,image/png,image/webp'
            })
        }
    
    def clean_email(self):
        """Validate email uniqueness (excluding current user)."""
        email = self.cleaned_data.get('email')
        
        # Check if email is already used by another user
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Este correo electrónico ya está en uso.')
        
        return email
    
    def clean_phone(self):
        """Validate phone format."""
        phone = self.cleaned_data.get('phone')
        
        if phone and not validate_phone_format(phone):
            raise ValidationError(
                'Formato de teléfono inválido. Use solo dígitos, espacios, guiones, paréntesis y el símbolo +.'
            )
        
        return phone
    
    def clean_avatar(self):
        """Validate avatar file size and format."""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Check file size (max 2MB)
            if avatar.size > settings.AVATAR_MAX_SIZE:
                raise ValidationError('El archivo no puede exceder 2 MB.')
            
            # Check image format and resolution
            try:
                img = Image.open(avatar)
                
                # Check format
                if img.format not in settings.AVATAR_ALLOWED_FORMATS:
                    raise ValidationError(
                        f'Formato no permitido. Use: {", ".join(settings.AVATAR_ALLOWED_FORMATS)}'
                    )
                
                # Check resolution
                max_width, max_height = settings.AVATAR_MAX_RESOLUTION
                if img.width > max_width or img.height > max_height:
                    raise ValidationError(
                        f'La resolución máxima permitida es {max_width}x{max_height} píxeles.'
                    )
                
            except Exception as e:
                raise ValidationError('Archivo de imagen inválido.')
        
        return avatar
    
    def clean_first_name(self):
        """Sanitize first name."""
        return sanitize_input(self.cleaned_data.get('first_name'))
    
    def clean_last_name(self):
        """Sanitize last name."""
        return sanitize_input(self.cleaned_data.get('last_name'))


class PasswordChangeForm(forms.Form):
    """
    Form for changing user password with current password verification.
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Contraseña actual',
            'autocomplete': 'current-password'
        })
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nueva contraseña (mínimo 8 caracteres)',
            'autocomplete': 'new-password'
        })
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirmar nueva contraseña',
            'autocomplete': 'new-password'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        """Verify current password is correct."""
        current_password = self.cleaned_data.get('current_password')
        
        if not self.user.check_password(current_password):
            raise ValidationError('La contraseña actual es incorrecta.')
        
        return current_password
    
    def clean_new_password1(self):
        """Validate new password length."""
        password = self.cleaned_data.get('new_password1')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if len(password) > 128:
            raise ValidationError('La contraseña no puede exceder 128 caracteres.')
        
        return password
    
    def clean(self):
        """Validate that both new passwords match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas nuevas no coinciden.')
        
        return cleaned_data
    
    def save(self):
        """Save the new password."""
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save()
        return self.user


class UserManagementForm(forms.ModelForm):
    """
    Form for administrators to create/edit users with role assignment.
    """
    email = forms.EmailField(
        required=True,
        max_length=254,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    
    supervisor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='supervisor', is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        empty_label='Sin supervisor'
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'supervisor', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de usuario'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Apellido'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+57 300 123 4567'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            })
        }
    
    def clean_phone(self):
        """Validate phone format."""
        phone = self.cleaned_data.get('phone')
        
        if phone and not validate_phone_format(phone):
            raise ValidationError(
                'Formato de teléfono inválido. Use solo dígitos, espacios, guiones, paréntesis y el símbolo +.'
            )
        
        return phone
