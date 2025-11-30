from django import forms
from .models import CategoriaInsumo, Insumo, MovimientoInsumo


class CategoriaInsumoForm(forms.ModelForm):
    """Formulario para categorías de insumos"""

    class Meta:
        model = CategoriaInsumo
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Carnes, Verduras, Lácteos...'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la categoría'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Categoría',
            'descripcion': 'Descripción',
            'activo': 'Activo',
        }


class InsumoForm(forms.ModelForm):
    """Formulario para insumos"""

    class Meta:
        model = Insumo
        fields = ['categoria', 'nombre', 'unidad', 'stock_actual', 'stock_minimo', 'nota', 'activo']
        widgets = {
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Tomate, Harina, Aceite...'
            }),
            'unidad': forms.Select(attrs={
                'class': 'form-control'
            }),
            'stock_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'nota': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales (opcional)'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'categoria': 'Categoría',
            'nombre': 'Nombre del Insumo',
            'unidad': 'Unidad de Medida',
            'stock_actual': 'Stock Actual',
            'stock_minimo': 'Stock Mínimo',
            'nota': 'Notas',
            'activo': 'Activo',
        }


class MovimientoInsumoForm(forms.ModelForm):
    """Formulario para movimientos de inventario (entrada/salida/ajuste)"""

    class Meta:
        model = MovimientoInsumo
        fields = ['insumo', 'tipo', 'cantidad', 'motivo']
        widgets = {
            'insumo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cantidad'
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Razón del movimiento'
            }),
        }
        labels = {
            'insumo': 'Insumo',
            'tipo': 'Tipo de Movimiento',
            'cantidad': 'Cantidad',
            'motivo': 'Motivo',
        }


class AjusteStockForm(forms.Form):
    """Formulario rápido para ajustar stock de un insumo"""

    cantidad_nueva = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva cantidad'
        }),
        label='Cantidad Nueva'
    )
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Razón del ajuste'
        }),
        label='Motivo',
        required=True
    )
