# Configuración de Verificación por Email

Este documento explica cómo configurar el sistema de verificación por email en ARMind CVs.

## Características Implementadas

✅ **Registro con verificación obligatoria**
- Los usuarios deben verificar su email antes de poder acceder
- Se envía un email automático con enlace de verificación
- Token único y seguro para cada verificación

✅ **Bloqueo de acceso sin verificación**
- Los usuarios no verificados no pueden iniciar sesión
- Mensaje claro indicando la necesidad de verificación

✅ **Reenvío de verificación**
- Opción para reenviar email de verificación desde el login
- Modal intuitivo para solicitar reenvío

✅ **Emails profesionales**
- Plantilla HTML responsive y atractiva
- Versión de texto plano como respaldo
- Branding consistente con la aplicación

## Configuración Requerida

### 1. Configurar Credenciales de Email

1. Copia el archivo de ejemplo:
   ```bash
   cp email_config_example.py email_config.py
   ```

2. Edita `email_config.py` con tus credenciales:
   ```python
   EMAIL_CONFIG = {
       'smtp_server': 'smtp.gmail.com',
       'smtp_port': 587,
       'email': 'tu_email@gmail.com',
       'password': 'tu_app_password',
       'use_tls': True
   }
   ```

### 2. Configuración para Gmail

1. **Habilitar verificación en 2 pasos:**
   - Ve a [Configuración de Google](https://myaccount.google.com/security)
   - Activa la verificación en 2 pasos

2. **Generar contraseña de aplicación:**
   - Ve a [Contraseñas de aplicación](https://myaccount.google.com/apppasswords)
   - Selecciona "Mail" como aplicación
   - Copia la contraseña generada
   - Úsala en `email_config.py`

### 3. Configuración para Outlook

1. **Habilitar verificación en 2 pasos:**
   - Ve a [Seguridad de Microsoft](https://account.microsoft.com/security)
   - Activa la verificación en 2 pasos

2. **Generar contraseña de aplicación:**
   - Genera una contraseña de aplicación
   - Úsala en lugar de tu contraseña normal

### 4. Actualizar app.py

Reemplaza la configuración de email en `app.py`:

```python
# Importar configuración de email
from email_config import EMAIL_CONFIG
```

## Base de Datos

La tabla `users` ahora incluye:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Flujo de Usuario

### Registro
1. Usuario completa formulario de registro
2. Sistema genera token único de verificación
3. Usuario se guarda con `email_verified = FALSE`
4. Se envía email con enlace de verificación
5. Usuario ve pantalla de "Email enviado"

### Verificación
1. Usuario hace clic en enlace del email
2. Sistema valida el token
3. Se actualiza `email_verified = TRUE`
4. Usuario es redirigido al login con mensaje de éxito

### Login
1. Usuario intenta iniciar sesión
2. Sistema verifica credenciales
3. Si email no está verificado, se bloquea el acceso
4. Usuario puede reenviar email de verificación

## URLs del Sistema

- `/register` - Formulario de registro
- `/verify_email/<token>` - Verificación de email
- `/resend_verification` - Reenvío de verificación
- `/login` - Inicio de sesión con validación

## Seguridad

- **Tokens únicos:** Cada verificación usa un UUID único
- **Validación de estado:** Solo usuarios no verificados pueden usar tokens
- **Limpieza de tokens:** Los tokens se eliminan después de la verificación
- **Credenciales seguras:** Las contraseñas de email deben ser de aplicación

## Troubleshooting

### Error: "Authentication failed"
- Verifica que uses contraseña de aplicación, no la contraseña normal
- Confirma que la verificación en 2 pasos esté habilitada

### Error: "Connection refused"
- Verifica la configuración del servidor SMTP
- Confirma que el puerto sea correcto (587 para TLS)

### Emails no llegan
- Revisa la carpeta de spam
- Verifica que el email remitente esté configurado correctamente
- Confirma que el servidor SMTP permita el envío

### Token inválido
- Los tokens son de un solo uso
- Verifica que el usuario no esté ya verificado
- Usa la función de reenvío para generar un nuevo token

## Personalización

### Cambiar plantilla de email
Edita la función `send_verification_email()` en `app.py` para personalizar:
- Colores y estilos
- Texto del mensaje
- URL de verificación
- Información de contacto

### Cambiar tiempo de expiración
Actualmente no hay expiración automática, pero puedes agregar:
```python
# Agregar campo de timestamp para expiración
verification_expires_at TIMESTAMP
```

## Mantenimiento

- **Monitorear logs** de envío de emails
- **Limpiar tokens** antiguos periódicamente
- **Actualizar credenciales** de email según sea necesario
- **Revisar métricas** de verificación de usuarios