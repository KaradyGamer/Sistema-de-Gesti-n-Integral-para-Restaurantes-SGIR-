from django import forms
from .models import ConfiguracionSistema


class ConfiguracionSistemaForm(forms.ModelForm):
    """Formulario para configuración del sistema"""

    class Meta:
        model = ConfiguracionSistema
        fields = [
            'nombre', 'nit', 'direccion', 'telefono', 'email', 'logo', 'lema',
            'moneda', 'impuesto', 'propina_sugerida',
            'idioma', 'zona_horaria', 'tema',
            'hora_apertura', 'hora_cierre',
            'reserva_max_minutos', 'reserva_tolerancia_minutos',
            'ticket_footer'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nit': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'lema': forms.TextInput(attrs={'class': 'form-control'}),
            'moneda': forms.TextInput(attrs={'class': 'form-control'}),
            'impuesto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'propina_sugerida': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'idioma': forms.Select(attrs={'class': 'form-control'}),
            'zona_horaria': forms.TextInput(attrs={'class': 'form-control'}),
            'tema': forms.Select(attrs={'class': 'form-control'}),
            'hora_apertura': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_cierre': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reserva_max_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'reserva_tolerancia_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'ticket_footer': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nombre': 'Nombre del Restaurante',
            'nit': 'NIT',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Email de Contacto',
            'logo': 'Logo del Restaurante',
            'lema': 'Lema o Eslogan',
            'moneda': 'Moneda',
            'impuesto': 'Impuesto (%)',
            'propina_sugerida': 'Propina Sugerida (%)',
            'idioma': 'Idioma',
            'zona_horaria': 'Zona Horaria',
            'tema': 'Tema Visual',
            'hora_apertura': 'Hora de Apertura',
            'hora_cierre': 'Hora de Cierre',
            'reserva_max_minutos': 'Duración Máxima Reserva (min)',
            'reserva_tolerancia_minutos': 'Tolerancia No-Show (min)',
            'ticket_footer': 'Pie de Ticket/Factura',
        }
