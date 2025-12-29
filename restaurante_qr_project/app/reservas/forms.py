from django import forms
from .models import Reserva
from datetime import datetime, date, time

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

    def clean_numero_carnet(self):
        """✅ Validar formato de número de carnet"""
        numero_carnet = self.cleaned_data.get('numero_carnet')
        if numero_carnet:
            # Eliminar espacios y guiones
            numero_carnet = numero_carnet.replace(' ', '').replace('-', '')
            # Validar que tenga al menos 6 dígitos
            if len(numero_carnet) < 6:
                raise forms.ValidationError('El número de carnet debe tener al menos 6 dígitos.')
            # Validar que sea alfanumérico
            if not numero_carnet.isalnum():
                raise forms.ValidationError('El número de carnet solo puede contener letras y números.')
        return numero_carnet

    def clean_telefono(self):
        """✅ Validar formato de teléfono boliviano"""
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Eliminar espacios, guiones y paréntesis
            telefono_limpio = telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            # Validar longitud (7-8 dígitos para Bolivia)
            if not (7 <= len(telefono_limpio) <= 8):
                raise forms.ValidationError('El número de teléfono debe tener 7 u 8 dígitos.')
            # Validar que solo contenga dígitos
            if not telefono_limpio.isdigit():
                raise forms.ValidationError('El teléfono solo puede contener números.')
        return telefono

    def clean_numero_personas(self):
        """✅ Validar número de personas"""
        numero_personas = self.cleaned_data.get('numero_personas')
        if numero_personas:
            if numero_personas < 1:
                raise forms.ValidationError('Debe reservar para al menos 1 persona.')
            if numero_personas > 20:
                raise forms.ValidationError('Para grupos mayores a 20 personas, contacte directamente al restaurante.')
        return numero_personas