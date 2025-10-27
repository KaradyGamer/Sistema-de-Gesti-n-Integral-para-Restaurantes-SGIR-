#!/usr/bin/env python
"""
Script para configurar el panel de administración Django con un diseño moderno
Usa admin_interface para personalizar colores y estilos
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from admin_interface.models import Theme

def configurar_admin():
    """Configura el tema del admin con colores del sistema"""

    # Obtener o crear tema
    theme, created = Theme.objects.get_or_create(pk=1)

    # ========================================
    # CONFIGURACIÓN GENERAL
    # ========================================
    theme.active = True
    theme.name = "Restaurante QR - Tema Principal"

    # Logo y títulos
    theme.title = "Sistema Restaurante QR"
    theme.title_color = "#FFFFFF"
    theme.title_visible = True

    # Branding
    theme.logo = ""  # Dejar vacío por ahora
    theme.logo_visible = True
    theme.favicon = ""

    # ========================================
    # COLORES PRINCIPALES (Coherentes con Panel Caja)
    # ========================================

    # Color primario - Azul índigo (mismo que panel caja)
    theme.css_header_background_color = "#6366f1"  # Primary color
    theme.css_header_text_color = "#FFFFFF"
    theme.css_header_link_color = "#FFFFFF"
    theme.css_header_link_hover_color = "#E0E7FF"

    # Sidebar/menú lateral
    theme.css_module_background_color = "#1E293B"  # Gris oscuro
    theme.css_module_text_color = "#E2E8F0"
    theme.css_module_link_color = "#94A3B8"
    theme.css_module_link_hover_color = "#FFFFFF"
    theme.css_module_link_selected_color = "#6366F1"
    theme.css_module_rounded_corners = True

    # Botones de acción
    theme.css_save_button_background_color = "#10B981"  # Verde éxito
    theme.css_save_button_background_hover_color = "#059669"
    theme.css_save_button_text_color = "#FFFFFF"

    theme.css_delete_button_background_color = "#EF4444"  # Rojo peligro
    theme.css_delete_button_background_hover_color = "#DC2626"
    theme.css_delete_button_text_color = "#FFFFFF"

    # ========================================
    # ESTILOS DE LISTAS Y TABLAS
    # ========================================
    theme.list_filter_dropdown = True
    theme.list_filter_sticky = True
    theme.recent_actions_visible = True

    # Tablas
    theme.css_generic_link_color = "#6366F1"
    theme.css_generic_link_hover_color = "#4F46E5"

    # ========================================
    # RESPONSIVE Y UX
    # ========================================
    theme.css_module_rounded_corners = True
    theme.list_filter_highlight = True
    theme.list_filter_removal = True

    # Formularios
    theme.form_pagination_sticky = True
    theme.form_submit_sticky = True

    # ========================================
    # COLORES DE FONDO
    # ========================================
    theme.css_body_background_color = "#F1F5F9"  # Gris claro
    theme.css_body_text_color = "#1E293B"

    # ========================================
    # GUARDAR CONFIGURACIÓN
    # ========================================
    theme.save()

    print("=" * 80)
    print("CONFIGURACION DEL ADMIN COMPLETADA")
    print("=" * 80)
    print(f"Tema: {theme.name}")
    print(f"Estado: {'Activo' if theme.active else 'Inactivo'}")
    print(f"")
    print("Colores principales:")
    print(f"  - Header: {theme.css_header_background_color}")
    print(f"  - Sidebar: {theme.css_module_background_color}")
    print(f"  - Boton Guardar: {theme.css_save_button_background_color}")
    print(f"  - Boton Eliminar: {theme.css_delete_button_background_color}")
    print("")
    print("Panel de administracion listo!")
    print("Visita: http://127.0.0.1:8000/admin/")
    print("")
    print("Para personalizar mas:")
    print("  1. Ve a Admin > Admin Interface > Themes")
    print("  2. Edita el tema 'Restaurante QR - Tema Principal'")
    print("  3. Sube un logo personalizado")
    print("=" * 80)

if __name__ == "__main__":
    configurar_admin()
