from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Area, PerfilUsuario

# --- FORMULARIO DE REGISTRO (Ya lo tenías, está perfecto) ---
class RegistroUsuarioForm(UserCreationForm):
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=True,
        empty_label="Selecciona tu Área",
        widget=forms.Select(attrs={'class': 'input-pill cursor-pointer'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Nombre de Usuario'
        self.fields['email'].widget.attrs['placeholder'] = 'Correo Electrónico'
        
        # 2. Contraseñas
        password_fields = [name for name, field in self.fields.items() if isinstance(field.widget, forms.PasswordInput)]
        
        if len(password_fields) >= 1:
            self.fields[password_fields[0]].widget.attrs['placeholder'] = 'Contraseña'
        if len(password_fields) >= 2:
            self.fields[password_fields[1]].widget.attrs['placeholder'] = 'Confirmar Contraseña'
        
        # 3. Estilo General
        for field in self.fields.values():
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' input-pill'

    def save(self, commit=True):
        user = super().save(commit=commit)
        area_seleccionada = self.cleaned_data.get('area')
        if area_seleccionada:
            PerfilUsuario.objects.create(user=user, area=area_seleccionada)
        return user

# --- FORMULARIO DE EDICIÓN (¡ESTO FALTABA!) ---
class EditarUsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'is_active']