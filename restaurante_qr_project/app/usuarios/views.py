from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegistroUsuarioSerializer, CustomTokenObtainPairSerializer

#  NUEVAS IMPORTACIONES PARA DJANGO SESSION
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

#  NUEVA VISTA: Login con Django Session
@csrf_protect
@require_http_methods(["POST"])
def session_login(request):
    """
    Vista para login con sesin Django (compatible con @login_required)
    """
    try:
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol_solicitado = request.POST.get('rol')
        
        print(f" Intento de login: {username}, rol: {rol_solicitado}")
        
        if not all([username, password, rol_solicitado]):
            return JsonResponse({
                'success': False,
                'error': 'Por favor completa todos los campos'
            }, status=400)
        
        #  Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            #  Verificar si el usuario est activo
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'error': 'Tu cuenta est desactivada'
                }, status=400)
            
            #  Verificar rol (si el usuario tiene el modelo Usuario personalizado)
            try:
                usuario_perfil = Usuario.objects.get(username=username)
                rol_usuario = usuario_perfil.rol
                print(f" Rol del usuario en BD: {rol_usuario}")
                
                #  Mapear roles para compatibilidad
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
                #  Si no tiene perfil personalizado, permitir admin/superuser
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

            #  Crear sesin Django
            login(request, user)
            print(f" Sesin creada para {username}")

            #  Determinar URL de redireccin
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
            print(f" Credenciales invlidas para {username}")
            return JsonResponse({
                'success': False,
                'error': 'Usuario o contrasea incorrectos'
            }, status=401)
            
    except Exception as e:
        print(f" Error en session_login: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

#  NUEVA VISTA: Logout
def session_logout(request):
    """
    Vista para cerrar sesin
    """
    logout(request)
    messages.success(request, 'Sesin cerrada correctamente')
    return redirect('/login/')

#  NUEVO SISTEMA DE LOGIN

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

        # Crear sesin
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')

        # Determinar redireccin segn rol
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
        print(f" Error en login_pin: {str(e)}")
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
                        'error': 'Tu cuenta est desactivada'
                    }, status=400)

            except Usuario.DoesNotExist:
                # Permitir superusuarios de Django
                if not user.is_superuser:
                    return JsonResponse({
                        'success': False,
                        'error': 'Usuario sin permisos de administrador'
                    }, status=403)

            # Crear sesin
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
                'error': 'Usuario o contrasea incorrectos'
            }, status=401)

    except Exception as e:
        print(f" Error en login_admin: {str(e)}")
        import traceback
        traceback.print_exc()

        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

#  AUTENTICACIN POR QR

def auth_qr(request, token):
    """
    Autentica a un usuario mediante su token QR y lo redirige a su panel
    SOLO funciona si hay una caja abierta (para meseros y cocineros)
    """
    try:
        from .models import Usuario
        from app.caja.models import CierreCaja
        from datetime import date

        print("=" * 80)
        print(f"[AUTH-QR] INICIO - Intento de autenticacion por QR")
        print(f"[AUTH-QR] Token recibido: {token}")
        print(f"[AUTH-QR] Tipo: {type(token)}")
        print(f"[AUTH-QR] Usuario actual: {request.user}")
        print(f"[AUTH-QR] Esta autenticado: {request.user.is_authenticated}")

        # Buscar usuario por token
        try:
            usuario = Usuario.objects.get(qr_token=token, activo=True)
            print(f"[AUTH-QR] ✓ Usuario encontrado: {usuario.username} ({usuario.rol})")
            print(f"[AUTH-QR] ✓ Usuario activo: {usuario.activo}")
            print(f"[AUTH-QR] ✓ Usuario is_active: {usuario.is_active}")
        except Usuario.DoesNotExist:
            print(f"[AUTH-QR] ✗ ERROR: Token QR no encontrado en BD: {token}")
            print(f"[AUTH-QR] ✗ Redirigiendo a login...")
            messages.error(request, 'Codigo QR invalido o expirado')
            return redirect('/login/')

        # VALIDAR QUE LA CAJA ESTE ABIERTA (solo para meseros y cocineros)
        # COMENTADO TEMPORALMENTE PARA PRUEBAS
        # if usuario.rol in ['mesero', 'cocinero']:
        #     caja_abierta = CierreCaja.objects.filter(
        #         estado='abierto',
        #         fecha=date.today()
        #     ).exists()

        #     print(f"[AUTH-QR] Verificando caja para {usuario.rol}: {'Abierta' if caja_abierta else 'Cerrada'}")

        #     if not caja_abierta:
        #         print(f"[AUTH-QR] ERROR: Caja cerrada - Redirigiendo a login")
        #         messages.error(request, 'La caja esta cerrada. No puedes iniciar sesion hasta que un cajero abra la caja.')
        #         return redirect('/login/')

        # Autenticar y crear sesion
        print(f"[AUTH-QR] Intentando login para: {usuario.username}")
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
        print(f"[AUTH-QR] ✓ Login por QR exitoso: {usuario.username} ({usuario.rol})")
        print(f"[AUTH-QR] ✓ Usuario ahora autenticado: {request.user.is_authenticated}")

        # Redirigir segn el rol
        if usuario.rol == 'mesero' or usuario.rol == 'cocinero':
            print(f"[AUTH-QR] → Redirigiendo a /empleado/")
            return redirect('/empleado/')  # Panel unificado
        elif usuario.rol == 'cajero':
            print(f"[AUTH-QR] → Redirigiendo a /caja/")
            return redirect('/caja/')
        else:
            print(f"[AUTH-QR] → Redirigiendo a /")
            return redirect('/')

        print("=" * 80)

    except Exception as e:
        print(f"[AUTH-QR] ERROR en auth_qr: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Error al procesar el codigo QR')
        return redirect('/login/')

# VISTA PARA VER TODOS LOS QR
def ver_todos_qr(request):
    """
    Muestra todos los códigos QR del sistema (mesas y empleados)
    """
    from app.mesas.models import Mesa
    import socket

    # Obtener IP del servidor
    try:
        hostname = socket.gethostname()
        ip_servidor = socket.gethostbyname(hostname)
        ip_servidor = f"{ip_servidor}:8000"
    except:
        ip_servidor = "localhost:8000"

    # Obtener todas las mesas activas
    mesas = Mesa.objects.filter(activo=True).order_by('numero')

    # Obtener empleados que pueden usar QR
    empleados = Usuario.objects.filter(
        rol__in=['mesero', 'cocinero'],
        activo=True
    ).order_by('rol', 'username')

    context = {
        'ip_servidor': ip_servidor,
        'mesas': mesas,
        'empleados': empleados,
        'MEDIA_URL': '/media/'
    }

    return render(request, 'admin/ver_qr.html', context)

def ver_qr_simple(request):
    import socket
    try:
        hostname = socket.gethostname()
        ip_servidor = socket.gethostbyname(hostname)
        ip_servidor = f"{ip_servidor}:8000"
    except:
        ip_servidor = "localhost:8000"

    context = {
        'ip_servidor': ip_servidor,
        'mesas': range(1, 16),
        'total_mesas': 15,
    }
    return render(request, 'admin/qr_simple.html', context)


# ✅ NUEVO SISTEMA DE QR REGENERABLE
from django.contrib.auth.decorators import login_required
from .models import QRToken

@login_required
@require_http_methods(["POST"])
def generar_qr_empleado(request):
    """
    Genera un nuevo QR para un empleado
    SOLO el cajero puede generar QRs
    """
    try:
        # Verificar que el usuario logueado sea cajero
        if request.user.rol != 'cajero':
            return JsonResponse({
                'success': False,
                'error': 'Solo los cajeros pueden generar códigos QR'
            }, status=403)

        data = json.loads(request.body)
        empleado_id = data.get('empleado_id')

        if not empleado_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de empleado requerido'
            }, status=400)

        # Obtener empleado
        try:
            empleado = Usuario.objects.get(id=empleado_id, activo=True)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Empleado no encontrado'
            }, status=404)

        # Verificar que el empleado pueda tener QR (mesero o cocinero)
        if empleado.rol not in ['mesero', 'cocinero']:
            return JsonResponse({
                'success': False,
                'error': 'Solo meseros y cocineros pueden tener códigos QR'
            }, status=400)

        # Obtener IP actual del servidor
        import socket
        try:
            hostname = socket.gethostname()
            ip_actual = socket.gethostbyname(hostname)
        except:
            ip_actual = '127.0.0.1'

        # Generar nuevo token (invalida anteriores automáticamente)
        nuevo_token = QRToken.generar_token(empleado, ip_actual)

        # Construir URL del QR
        url_qr = f"http://{ip_actual}:8000/qr-login/{nuevo_token.token}/"

        return JsonResponse({
            'success': True,
            'message': f'Código QR generado para {empleado.get_full_name() or empleado.username}',
            'qr_url': url_qr,
            'token': str(nuevo_token.token),
            'empleado': {
                'id': empleado.id,
                'nombre': empleado.get_full_name() or empleado.username,
                'rol': empleado.get_rol_display()
            }
        })

    except Exception as e:
        print(f"[ERROR] Error en generar_qr_empleado: {str(e)}")
        import traceback
        traceback.print_exc()

        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


def qr_login(request, token):
    """
    Login por QR usando el nuevo sistema de tokens regenerables
    Al hacer login, invalida el token usado y genera uno nuevo
    """
    try:
        from django.utils import timezone

        print("=" * 80)
        print(f"[QR-LOGIN] Token recibido: {token}")

        # Buscar token activo
        try:
            qr_token = QRToken.objects.get(token=token, activo=True)
            empleado = qr_token.usuario
            print(f"[QR-LOGIN] ✓ Token válido para: {empleado.username} ({empleado.rol})")
        except QRToken.DoesNotExist:
            print(f"[QR-LOGIN] ✗ Token inválido o expirado")
            messages.error(request, 'Código QR inválido o expirado')
            return redirect('/login/')

        # Verificar que el empleado esté activo
        if not empleado.activo or not empleado.is_active:
            print(f"[QR-LOGIN] ✗ Empleado inactivo")
            messages.error(request, 'Tu cuenta está desactivada')
            return redirect('/login/')

        # ✅ Marcar token como usado
        qr_token.marcar_usado()
        print(f"[QR-LOGIN] ✓ Token marcado como usado")

        # ✅ Autenticar y crear sesión
        login(request, empleado, backend='django.contrib.auth.backends.ModelBackend')
        print(f"[QR-LOGIN] ✓ Login exitoso para: {empleado.username}")

        # ✅ Generar nuevo token automáticamente (invalida el usado)
        import socket
        try:
            hostname = socket.gethostname()
            ip_actual = socket.gethostbyname(hostname)
        except:
            ip_actual = '127.0.0.1'

        nuevo_token = QRToken.generar_token(empleado, ip_actual)
        print(f"[QR-LOGIN] ✓ Nuevo token generado: {nuevo_token.token}")

        # ✅ CORREGIDO: Redirigir según el rol del empleado
        messages.success(request, f'Bienvenido {empleado.get_full_name() or empleado.username}')

        # Determinar panel según rol
        if empleado.rol == 'mesero':
            panel_url = '/mesero/'
        elif empleado.rol == 'cocinero':
            panel_url = '/cocina/'
        elif empleado.rol == 'cajero':
            panel_url = '/caja/'
        else:
            panel_url = '/empleado/'  # Fallback por si hay otro rol

        print(f"[QR-LOGIN] ✓ Redirigiendo a: {panel_url}")
        return redirect(panel_url)

    except Exception as e:
        print(f"[QR-LOGIN] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Error al procesar el código QR')
        return redirect('/login/')


@login_required
def listar_empleados_qr(request):
    """
    Lista empleados para generar QR
    SOLO accesible por cajeros
    """
    if request.user.rol != 'cajero':
        messages.error(request, 'Acceso denegado')
        return redirect('/caja/')

    empleados = Usuario.objects.filter(
        rol__in=['mesero', 'cocinero'],
        activo=True
    ).order_by('rol', 'first_name', 'last_name')

    context = {
        'empleados': empleados
    }

    return render(request, 'caja/generar_qr.html', context)
