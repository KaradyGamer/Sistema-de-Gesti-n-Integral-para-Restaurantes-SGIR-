"""
Django Forms para AdminUX
Validación segura de inputs con Forms en lugar de request.POST directo
"""
from django import forms
from app.usuarios.models import Usuario
from app.productos.models import Producto, Categoria
from app.mesas.models import Mesa
from app.reservas.models import Reserva
import json


class UsuarioForm(forms.ModelForm):
    """Form para crear/editar usuarios con validación"""
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Dejar en blanco para mantener contraseña actual"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Confirmar contraseña"
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'rol', 'pin', 'areas_permitidas', 'is_staff', 'activo'
        ]
        widgets = {
            'areas_permitidas': forms.SelectMultiple(choices=[
                ('mesero', 'Mesero'),
                ('cocina', 'Cocina'),
                ('caja', 'Caja'),
                ('reportes', 'Reportes'),
            ]),
        }

    def clean_username(self):
        """Validar que username sea único"""
        username = self.cleaned_data.get('username')
        if self.instance.pk is None:  # Nuevo usuario
            if Usuario.objects.filter(username=username).exists():
                raise forms.ValidationError("Este nombre de usuario ya existe")
        return username

    def clean_email(self):
        """Validar formato de email"""
        email = self.cleaned_data.get('email')
        if email:
            # Django ya valida formato con EmailField
            return email.lower()
        return email

    def clean_pin(self):
        """Validar PIN (4-6 dígitos)"""
        pin = self.cleaned_data.get('pin')
        if pin:
            if not pin.isdigit():
                raise forms.ValidationError("El PIN debe contener solo números")
            if len(pin) < 4 or len(pin) > 6:
                raise forms.ValidationError("El PIN debe tener entre 4 y 6 dígitos")
        return pin

    def clean_areas_permitidas(self):
        """Validar que areas_permitidas sea JSON válido"""
        areas = self.cleaned_data.get('areas_permitidas')
        if areas:
            if isinstance(areas, str):
                try:
                    areas_list = json.loads(areas)
                    if not isinstance(areas_list, list):
                        raise forms.ValidationError("areas_permitidas debe ser una lista JSON")
                    return areas_list
                except json.JSONDecodeError:
                    raise forms.ValidationError("JSON inválido en areas_permitidas")
        return areas or []

    def clean(self):
        """Validación cruzada de campos"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden")

        return cleaned_data

    def save(self, commit=True):
        """Guardar usuario con contraseña hasheada"""
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user


class ProductoForm(forms.ModelForm):
    """Form para crear/editar productos"""

    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'categoria', 'precio',
            'imagen', 'disponible', 'requiere_inventario',
            'stock_actual', 'stock_minimo'
        ]

    def clean_nombre(self):
        """Validar que nombre no esté vacío y sanitizar"""
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio")
        return nombre

    def clean_precio(self):
        """Validar que precio sea positivo"""
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo")
        return precio

    def clean_stock_actual(self):
        """Validar stock actual"""
        stock = self.cleaned_data.get('stock_actual')
        if stock is not None and stock < 0:
            raise forms.ValidationError("El stock no puede ser negativo")
        return stock

    def clean_stock_minimo(self):
        """Validar stock mínimo"""
        stock_min = self.cleaned_data.get('stock_minimo')
        if stock_min is not None and stock_min < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo")
        return stock_min

    def clean(self):
        """Validación cruzada"""
        cleaned_data = super().clean()
        requiere_inventario = cleaned_data.get('requiere_inventario')
        stock_actual = cleaned_data.get('stock_actual')

        if requiere_inventario and stock_actual is None:
            raise forms.ValidationError(
                "Si requiere inventario, debe especificar stock actual"
            )

        return cleaned_data


class CategoriaForm(forms.ModelForm):
    """Form para crear/editar categorías con validación"""

    class Meta:
        model = Categoria
        fields = ['nombre', 'activo']

    def clean_nombre(self):
        """Validar unicidad y sanitizar"""
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio")

        # Verificar unicidad solo si es nuevo o cambió el nombre
        if self.instance.pk is None:  # Nuevo
            if Categoria.objects.filter(nombre__iexact=nombre).exists():
                raise forms.ValidationError("Ya existe una categoría con este nombre")
        else:  # Editando
            if Categoria.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe una categoría con este nombre")

        return nombre


class MesaForm(forms.ModelForm):
    """Form para crear/editar mesas con validación"""

    class Meta:
        model = Mesa
        fields = [
            'numero', 'capacidad', 'estado', 'disponible',
            'activo', 'es_combinada', 'mesas_combinadas',
            'posicion_x', 'posicion_y'
        ]

    def clean_numero(self):
        """Validar unicidad de número"""
        numero = self.cleaned_data.get('numero')
        if self.instance.pk is None:  # Nueva
            if Mesa.objects.filter(numero=numero).exists():
                raise forms.ValidationError("Ya existe una mesa con este número")
        else:  # Editando
            if Mesa.objects.filter(numero=numero).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe una mesa con este número")
        return numero

    def clean_capacidad(self):
        """Validar capacidad"""
        capacidad = self.cleaned_data.get('capacidad')
        if capacidad is not None and capacidad < 1:
            raise forms.ValidationError("La capacidad debe ser al menos 1")
        if capacidad is not None and capacidad > 50:
            raise forms.ValidationError("La capacidad máxima es 50 personas")
        return capacidad


class ReservaForm(forms.ModelForm):
    """Form para crear/editar reservas con validación"""

    class Meta:
        model = Reserva
        fields = [
            'mesa', 'numero_carnet', 'nombre_completo', 'telefono', 'email',
            'fecha_reserva', 'hora_reserva', 'numero_personas',
            'observaciones', 'estado'
        ]
        widgets = {
            'fecha_reserva': forms.DateInput(attrs={'type': 'date'}),
            'hora_reserva': forms.TimeInput(attrs={'type': 'time'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_telefono(self):
        """Validar formato de teléfono"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        # Remover espacios y guiones
        telefono = telefono.replace(' ', '').replace('-', '')
        if telefono and not telefono.isdigit():
            raise forms.ValidationError("El teléfono debe contener solo números")
        return telefono

    def clean_numero_personas(self):
        """Validar número de personas"""
        num = self.cleaned_data.get('numero_personas')
        if num is not None and num < 1:
            raise forms.ValidationError("Debe haber al menos 1 persona")
        if num is not None and num > 50:
            raise forms.ValidationError("El máximo es 50 personas")
        return num

    def clean(self):
        """Validar solapamiento de reservas"""
        cleaned_data = super().clean()
        mesa = cleaned_data.get('mesa')
        fecha = cleaned_data.get('fecha_reserva')
        hora = cleaned_data.get('hora_reserva')

        if mesa and fecha and hora:
            # Aquí se puede agregar validación de solapamiento
            # (ya existe en el modelo, pero double-check en form)
            pass

        return cleaned_data
