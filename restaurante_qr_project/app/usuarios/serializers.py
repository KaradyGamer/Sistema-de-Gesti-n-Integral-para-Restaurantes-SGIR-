from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import Usuario

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'password_confirm', 'rol']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para login que incluye validación de rol
    """
    rol = serializers.CharField(required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        rol = attrs.get('rol')
        
        # Validar que todos los campos estén presentes
        if not all([username, password, rol]):
            raise serializers.ValidationError('Todos los campos son requeridos')
        
        # Autenticar usuario
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError('Credenciales incorrectas')
        
        if not user.is_active:
            raise serializers.ValidationError('Usuario inactivo')
        
        # Verificar rol
        if user.rol != rol:
            raise serializers.ValidationError(f'Tu rol es {user.get_rol_display()}, no {rol}')
        
        # Llamar al método padre para generar tokens
        data = super().validate(attrs)
        
        # Agregar información adicional del usuario
        data['user'] = {
            'username': user.username,
            'rol': user.rol,
            'email': user.email
        }
        
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar claims personalizados al token
        token['username'] = user.username
        token['rol'] = user.rol
        
        return token