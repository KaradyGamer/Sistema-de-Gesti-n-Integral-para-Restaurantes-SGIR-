from django import forms
from .models import Reserva
from app.mesas.models import Mesa
from datetime import datetime, date, time, timedelta

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = [
            'numero_carnet', 'nombre_completo', 'telefono', 'email',
            'fecha_reserva', 'hora_reserva', 'numero_personas', 'observaciones'
        ]
        widgets = {
            'numero_carnet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12345678',
                'required': True
            }),
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de teléfono'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'fecha_reserva': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().isoformat(),
                'required': True
            }),
            'hora_reserva': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'numero_personas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20,
                'required': True
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales (opcional)'
            })
        }
    
    def clean_fecha_reserva(self):
        fecha = self.cleaned_data.get('fecha_reserva')
        if fecha and fecha < date.today():
            raise forms.ValidationError('No puedes reservar para fechas pasadas.')
        return fecha
    
    def clean_hora_reserva(self):
        hora = self.cleaned_data.get('hora_reserva')
        fecha = self.cleaned_data.get('fecha_reserva')
        
        if hora and fecha:
            # Validar horario de funcionamiento (ejemplo: 11:00 - 22:00)
            if not (time(11, 0) <= hora <= time(22, 0)):
                raise forms.ValidationError('El horario de atención es de 11:00 AM a 10:00 PM.')
            
            # Si es hoy, validar que no sea una hora pasada
            if fecha == date.today():
                ahora = datetime.now().time()
                if hora <= ahora:
                    raise forms.ValidationError('No puedes reservar para una hora que ya pasó.')
        
        return hora