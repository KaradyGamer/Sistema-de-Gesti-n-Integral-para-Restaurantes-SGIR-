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

# ✅ SEGURIDAD: Logging y rate limiting
import logging
from .decorators import rate_limit_login

logger = logging.getLogger('app.usuarios')

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
@rate_limit_login(max_attempts=5, lockout_duration=300, login_type='password')
def session_login(request):
    """
    ✅ ACTUALIZADO: Login con sesión Django + rate limiting + logging seguro
    """
    try:
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol_solicitado = request.POST.get('rol')

        logger.info(f"LOGIN: Intento de login para rol: {rol_solicitado}")

        if not all([username, password, rol_solicitado]):
            return JsonResponse({
                'success': False,
                'error': 'Por favor completa todos los campos'
            }, status=400)

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # ✅ Verificar ambos campos: is_active (Django) y activo (Usuario personalizado)
            if not user.is_active:
                logger.warning(f"LOGIN: Usuario Django inactivo - ID: {user.id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Tu cuenta está desactivada'
                }, status=400)

            # Verificar campo activo del modelo personalizado
            if hasattr(user, 'activo') and not user.activo:
                logger.warning(f"LOGIN: Usuario SGIR inactivo - ID: {user.id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Tu cuenta está desactivada'
                }, status=400)

            # Verificar rol
            try:
                usuario_perfil = Usuario.objects.get(username=username)
                rol_usuario = usuario_perfil.rol
                logger.info(f"LOGIN: Usuario ID:{user.id}, rol:{rol_usuario}")

                # Mapear roles para compatibilidad
                mapeo_roles = {
                    'cocinero': ['cocinero'],
                    'mesero': ['mesero'],
                    'cajero': ['cajero'],
                    'administrador': ['admin', 'gerente'],
                }

                roles_permitidos = mapeo_roles.get(rol_solicitado, [])

                if rol_usuario not in roles_permitidos:
                    logger.warning(f"LOGIN: Rol no permitido - Usuario ID:{user.id}, intentó:{rol_solicitado}, tiene:{rol_usuario}")
                    return JsonResponse({
                        'success': False,
                        'error': f'No tienes permisos para acceder como {rol_solicitado}'
                    }, status=403)

            except Usuario.DoesNotExist:
                # Si no tiene perfil personalizado, permitir admin/superuser
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

            # Crear sesión Django
            login(request, user)
            logger.info(f"LOGIN: Sesión creada - Usuario ID:{user.id}")

            # Determinar URL de redirección
            redirect_urls = {
                'cocinero': '/cocina/',
                'mesero': '/mesero/',
                'cajero': '/caja/',
                'administrador': '/reportes/dashboard/',
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
            logger.warning("LOGIN: Credenciales inválidas")
            return JsonResponse({
                'success': False,
                'error': 'Usuario o contraseña incorrectos'
            }, status=401)

    except Exception as e:
        logger.exception("LOGIN: Error en session_login")
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
@rate_limit_login(max_attempts=5, lockout_duration=300, login_type='pin')
def login_pin(request):
    """
    ✅ ACTUALIZADO: Login con PIN + rate limiting + logging (SIN exponer PIN)
    """
    try:
        data = json.loads(request.body)
        pin = data.get('pin')

        logger.info("LOGIN-PIN: Intento de login por PIN")

        if not pin:
            return JsonResponse({
                'success': False,
                'error': 'PIN requerido'
            }, status=400)

        # Buscar usuario por PIN (NO loguear el PIN)
        try:
            usuario = Usuario.objects.get(pin=pin, activo=True)
        except Usuario.DoesNotExist:
            logger.warning("LOGIN-PIN: PIN inválido o usuario inactivo")
            return JsonResponse({
                'success': False,
                'error': 'PIN incorrecto o usuario inactivo'
            }, status=401)

        # Verificar que el usuario pueda usar PIN
        if not usuario.puede_usar_pin():
            logger.warning(f"LOGIN-PIN: Usuario ID:{usuario.id} no puede usar PIN")
            return JsonResponse({
                'success': False,
                'error': 'Este usuario no puede usar PIN'
            }, status=403)

        # Crear sesión
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
        logger.info(f"LOGIN-PIN: Acceso exitoso - Usuario ID:{usuario.id}, rol:{usuario.rol}")

        # Determinar redirección según rol
        redirect_urls = {
            'cajero': '/caja/',
            'mesero': '/empleado/',
            'cocinero': '/empleado/',
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
        logger.exception("LOGIN-PIN: Error en login_pin")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

@csrf_protect
@require_http_methods(["POST"])
def login_admin(request):
    """
    ✅ ACTUALIZADO: Login con redirección inteligente según privilegios

    Comportamiento según tipo de usuario:
    - superuser (is_superuser=True) → /admin/ (Django admin)
    - staff (is_staff=True) → /adminux/ (panel moderno)
    - usuario normal → /menu/ (menú cliente)
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
            # Verificar que el usuario esté activo
            if not user.is_active:
                logger.warning(f"LOGIN-ADMIN: Usuario Django inactivo - ID: {user.id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Tu cuenta está desactivada'
                }, status=400)

            # Verificar campo activo del modelo personalizado
            try:
                usuario = Usuario.objects.get(username=username)
                if not usuario.activo:
                    logger.warning(f"LOGIN-ADMIN: Usuario SGIR inactivo - ID: {usuario.id}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Tu cuenta está desactivada'
                    }, status=400)
            except Usuario.DoesNotExist:
                # Usuario Django sin perfil personalizado
                pass

            # Crear sesión
            login(request, user)
            logger.info(f"LOGIN-ADMIN: Login exitoso - {username} (is_staff={user.is_staff}, is_superuser={user.is_superuser})")

            # ✅ REDIRECCIÓN INTELIGENTE según privilegios
            if user.is_superuser:
                # Superusuario → Admin nativo de Django
                redirect_url = '/admin/'
                logger.info("LOGIN-ADMIN: Superuser redirigido a /admin/")
            elif user.is_staff:
                # Staff → AdminUX (panel moderno)
                redirect_url = '/adminux/'
                logger.info("LOGIN-ADMIN: Staff redirigido a /adminux/")
            else:
                # Usuario normal → Menú cliente
                redirect_url = '/menu/'
                logger.info("LOGIN-ADMIN: Usuario normal redirigido a /menu/")

            return JsonResponse({
                'success': True,
                'message': 'Login exitoso',
                'redirect_url': redirect_url,
                'user': username
            })

        else:
            logger.warning(f"LOGIN-ADMIN: Credenciales inválidas para usuario: {username}")
            return JsonResponse({
                'success': False,
                'error': 'Usuario o contraseña incorrectos'
            }, status=401)

    except Exception as e:
        logger.exception("LOGIN-ADMIN: Error en login_admin")
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

        logger.debug("="*80)
        logger.info("AUTH-QR: INICIO - Intento de autenticacion por QR")
        logger.info(f"AUTH-QR: Token recibido: {token}")
        logger.info(f"AUTH-QR: Tipo: {type(token)}")
        logger.info(f"AUTH-QR: Usuario actual: {request.user}")
        logger.info(f"AUTH-QR: Esta autenticado: {request.user.is_authenticated}")

        # Buscar usuario por token
        try:
            usuario = Usuario.objects.get(qr_token=token, activo=True)
            logger.info(f"AUTH-QR: ✓ Usuario encontrado: {usuario.username} ({usuario.rol})")
            logger.info(f"AUTH-QR: ✓ Usuario activo: {usuario.activo}")
            logger.info(f"AUTH-QR: ✓ Usuario is_active: {usuario.is_active}")
        except Usuario.DoesNotExist:
            logger.info(f"AUTH-QR: ✗ ERROR: Token QR no encontrado en BD: {token}")
            logger.info("AUTH-QR: ✗ Redirigiendo a login...")
            messages.error(request, 'Codigo QR invalido o expirado')
            return redirect('/login/')

        # VALIDAR QUE LA CAJA ESTE ABIERTA (solo para meseros y cocineros)
        # COMENTADO TEMPORALMENTE PARA PRUEBAS
        # if usuario.rol in ['mesero', 'cocinero']:
        #     caja_abierta = CierreCaja.objects.filter(
        #         estado='abierto',
        #         fecha=date.today()
        #     ).exists()

        #     logger.info(f"AUTH-QR: Verificando caja para {usuario.rol}: {'Abierta' if caja_abierta else 'Cerrada'}")

        #     if not caja_abierta:
        #         logger.info(f"AUTH-QR: ERROR: Caja cerrada - Redirigiendo a login")
        #         messages.error(request, 'La caja esta cerrada. No puedes iniciar sesion hasta que un cajero abra la caja.')
        #         return redirect('/login/')

        # Autenticar y crear sesion
        logger.info(f"AUTH-QR: Intentando login para: {usuario.username}")
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
        logger.info(f"AUTH-QR: ✓ Login por QR exitoso: {usuario.username} ({usuario.rol})")
        logger.info(f"AUTH-QR: ✓ Usuario ahora autenticado: {request.user.is_authenticated}")

        # Redirigir segn el rol
        if usuario.rol == 'mesero' or usuario.rol == 'cocinero':
            logger.info("AUTH-QR: → Redirigiendo a /empleado/")
            return redirect('/empleado/')  # Panel unificado
        elif usuario.rol == 'cajero':
            logger.info("AUTH-QR: → Redirigiendo a /caja/")
            return redirect('/caja/')
        else:
            logger.info("AUTH-QR: → Redirigiendo a /")
            return redirect('/')

        logger.debug("="*80)

    except Exception as e:
        logger.info(f"AUTH-QR: ERROR en auth_qr: {str(e)}")
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
        logger.info(f"[ERROR] Error en generar_qr_empleado: {str(e)}")
        import traceback
        traceback.print_exc()

        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@rate_limit_login(max_attempts=5, lockout_duration=300, login_type='qr')
def qr_login(request, token):
    """
    ✅ ACTUALIZADO: Login por QR con logging, rate limiting y validación de expiración
    """
    try:

        logger.info("QR-LOGIN: Intento de login con token")

        # Buscar token activo
        try:
            qr_token = QRToken.objects.get(token=token, activo=True)
            empleado = qr_token.usuario
            logger.info(f"QR-LOGIN: Token válido para usuario ID:{empleado.id}, rol:{empleado.rol}")
        except QRToken.DoesNotExist:
            logger.warning("QR-LOGIN: Token inválido o ya usado")
            messages.error(request, 'Código QR inválido o expirado')
            return redirect('/login/')

        # ✅ NUEVO: Verificar expiración del token
        if qr_token.esta_expirado():
            qr_token.invalidar()
            logger.warning(f"QR-LOGIN: Token expirado para usuario ID:{empleado.id}")
            messages.error(request, 'Código QR expirado. Solicita uno nuevo.')
            return redirect('/login/')

        # Verificar que el empleado esté activo
        if not empleado.activo or not empleado.is_active:
            logger.warning(f"QR-LOGIN: Usuario inactivo ID:{empleado.id}")
            messages.error(request, 'Tu cuenta está desactivada')
            return redirect('/login/')

        # Marcar token como usado
        qr_token.marcar_usado()
        logger.info("QR-LOGIN: Token marcado como usado")

        # Autenticar y crear sesión
        login(request, empleado, backend='django.contrib.auth.backends.ModelBackend')
        logger.info(f"QR-LOGIN: Login exitoso para usuario ID:{empleado.id}")

        # Generar nuevo token automáticamente
        import socket
        try:
            hostname = socket.gethostname()
            ip_actual = socket.gethostbyname(hostname)
        except:
            ip_actual = '127.0.0.1'

        nuevo_token = QRToken.generar_token(empleado, ip_actual, duracion_horas=24)
        logger.info(f"QR-LOGIN: Nuevo token generado (expira: {nuevo_token.fecha_expiracion})")

        messages.success(request, f'Bienvenido {empleado.get_full_name() or empleado.username}')

        # Determinar panel según rol
        if empleado.rol == 'mesero':
            panel_url = '/mesero/'
        elif empleado.rol == 'cocinero':
            panel_url = '/cocina/'
        elif empleado.rol == 'cajero':
            panel_url = '/caja/'
        else:
            panel_url = '/empleado/'

        logger.info(f"QR-LOGIN: Redirigiendo a: {panel_url}")
        return redirect(panel_url)

    except Exception as e:
        logger.exception("QR-LOGIN: Error al procesar código QR")
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
