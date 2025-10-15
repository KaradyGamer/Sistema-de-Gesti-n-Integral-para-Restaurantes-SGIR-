from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegistroUsuarioSerializer, CustomTokenObtainPairSerializer

# ✅ NUEVAS IMPORTACIONES PARA DJANGO SESSION
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from .models import Usuario

class RegistroUsuarioView(generics.CreateAPIView):
    """
    Vista para registrar nuevos usuarios.
    """
    serializer_class = RegistroUsuarioSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"mensaje": "Usuario registrado correctamente."},
            status=status.HTTP_201_CREATED
        )

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# ✅ NUEVA VISTA: Login con Django Session
@csrf_protect
@require_http_methods(["POST"])
def session_login(request):
    """
    Vista para login con sesión Django (compatible con @login_required)
    """
    try:
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol_solicitado = request.POST.get('rol')
        
        print(f"🔐 Intento de login: {username}, rol: {rol_solicitado}")
        
        if not all([username, password, rol_solicitado]):
            return JsonResponse({
                'success': False,
                'error': 'Por favor completa todos los campos'
            }, status=400)
        
        # ✅ Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # ✅ Verificar si el usuario está activo
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'error': 'Tu cuenta está desactivada'
                }, status=400)
            
            # ✅ Verificar rol (si el usuario tiene el modelo Usuario personalizado)
            try:
                usuario_perfil = Usuario.objects.get(username=username)
                rol_usuario = usuario_perfil.rol
                print(f"🔐 Rol del usuario en BD: {rol_usuario}")
                
                # ✅ Mapear roles para compatibilidad
                mapeo_roles = {
                    'cocinero': ['cocinero'],
                    'mesero': ['mesero'],
                    'cajero': ['cajero'],  # Nuevo rol cajero
                    'administrador': ['admin', 'gerente'],
                }

                roles_permitidos = mapeo_roles.get(rol_solicitado, [])

                if rol_usuario not in roles_permitidos:
                    return JsonResponse({
                        'success': False,
                        'error': f'No tienes permisos para acceder como {rol_solicitado}'
                    }, status=403)

            except Usuario.DoesNotExist:
                # ✅ Si no tiene perfil personalizado, permitir admin/superuser
                if not user.is_superuser and rol_solicitado == 'administrador':
                    return JsonResponse({
                        'success': False,
                        'error': 'No tienes permisos de administrador'
                    }, status=403)
                elif not user.is_superuser and rol_solicitado in ['cocinero', 'mesero', 'cajero']:
                    return JsonResponse({
                        'success': False,
                        'error': 'Usuario sin rol asignado'
                    }, status=403)

            # ✅ Crear sesión Django
            login(request, user)
            print(f"✅ Sesión creada para {username}")

            # ✅ Determinar URL de redirección
            redirect_urls = {
                'cocinero': '/cocina/',
                'mesero': '/mesero/',
                'cajero': '/caja/',  # Nueva URL para cajero
                'administrador': '/reportes/dashboard/',  # Panel de reportes para admin
            }
            
            redirect_url = redirect_urls.get(rol_solicitado, '/')
            
            return JsonResponse({
                'success': True,
                'message': 'Login exitoso',
                'redirect_url': redirect_url,
                'user': username,
                'rol': rol_solicitado
            })
            
        else:
            print(f"❌ Credenciales inválidas para {username}")
            return JsonResponse({
                'success': False,
                'error': 'Usuario o contraseña incorrectos'
            }, status=401)
            
    except Exception as e:
        print(f"❌ Error en session_login: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

# ✅ NUEVA VISTA: Logout
def session_logout(request):
    """
    Vista para cerrar sesión
    """
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('/login/')

# 🆕 NUEVO SISTEMA DE LOGIN

import json

@csrf_protect
@require_http_methods(["POST"])
def login_pin(request):
    """
    Login con PIN para cajeros y empleados
    """
    try:
        data = json.loads(request.body)
        pin = data.get('pin')

        if not pin:
            return JsonResponse({
                'success': False,
                'error': 'PIN requerido'
            }, status=400)

        # Buscar usuario por PIN
        try:
            usuario = Usuario.objects.get(pin=pin, activo=True)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'PIN incorrecto o usuario inactivo'
            }, status=401)

        # Verificar que el usuario pueda usar PIN
        if not usuario.puede_usar_pin():
            return JsonResponse({
                'success': False,
                'error': 'Este usuario no puede usar PIN'
            }, status=403)

        # Crear sesión
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')

        # Determinar redirección según rol
        redirect_urls = {
            'cajero': '/caja/',
            'mesero': '/empleado/',  # Panel unificado
            'cocinero': '/empleado/',  # Panel unificado
        }

        redirect_url = redirect_urls.get(usuario.rol, '/empleado/')

        return JsonResponse({
            'success': True,
            'message': 'Acceso concedido',
            'redirect_url': redirect_url,
            'user': usuario.get_full_name() or usuario.username,
            'rol': usuario.rol
        })

    except Exception as e:
        print(f"❌ Error en login_pin: {str(e)}")
        import traceback
        traceback.print_exc()

        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

@csrf_protect
@require_http_methods(["POST"])
def login_admin(request):
    """
    Login tradicional para administradores y gerentes
    """
    try:
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not all([username, password]):
            return JsonResponse({
                'success': False,
                'error': 'Por favor completa todos los campos'
            }, status=400)

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verificar que sea admin o gerente
            try:
                usuario = Usuario.objects.get(username=username)

                if usuario.rol not in ['admin', 'gerente']:
                    return JsonResponse({
                        'success': False,
                        'error': 'Acceso restringido a administradores'
                    }, status=403)

                if not usuario.activo:
                    return JsonResponse({
                        'success': False,
                        'error': 'Tu cuenta está desactivada'
                    }, status=400)

            except Usuario.DoesNotExist:
                # Permitir superusuarios de Django
                if not user.is_superuser:
                    return JsonResponse({
                        'success': False,
                        'error': 'Usuario sin permisos de administrador'
                    }, status=403)

            # Crear sesión
            login(request, user)

            return JsonResponse({
                'success': True,
                'message': 'Login exitoso',
                'redirect_url': '/admin/',
                'user': username
            })

        else:
            return JsonResponse({
                'success': False,
                'error': 'Usuario o contraseña incorrectos'
            }, status=401)

    except Exception as e:
        print(f"❌ Error en login_admin: {str(e)}")
        import traceback
        traceback.print_exc()

        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

# 🆕 AUTENTICACIÓN POR QR

def auth_qr(request, token):
    """
    Autentica a un usuario mediante su token QR y lo redirige a su panel
    SOLO funciona si hay una caja abierta (para meseros y cocineros)
    """
    try:
        from .models import Usuario
        from app.caja.models import CierreCaja
        from datetime import date

        # Buscar usuario por token
        try:
            usuario = Usuario.objects.get(qr_token=token, activo=True)
        except Usuario.DoesNotExist:
            messages.error(request, 'Código QR inválido o expirado')
            return redirect('/login/')

        # ✅ VALIDAR QUE LA CAJA ESTÉ ABIERTA (solo para meseros y cocineros)
        if usuario.rol in ['mesero', 'cocinero']:
            caja_abierta = CierreCaja.objects.filter(
                estado='abierto',
                fecha=date.today()
            ).exists()

            if not caja_abierta:
                messages.error(request, '🔒 La caja está cerrada. No puedes iniciar sesión hasta que un cajero abra la caja.')
                return redirect('/login/')

        # Autenticar y crear sesión
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
        print(f"✅ Login por QR exitoso: {usuario.username} ({usuario.rol})")

        # Redirigir según el rol
        if usuario.rol == 'mesero' or usuario.rol == 'cocinero':
            return redirect('/empleado/')  # Panel unificado
        elif usuario.rol == 'cajero':
            return redirect('/caja/')
        else:
            return redirect('/')

    except Exception as e:
        print(f"❌ Error en auth_qr: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Error al procesar el código QR')
        return redirect('/login/')