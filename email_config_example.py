# Configuración de Email para CV Analyzer Pro
# Copia este archivo como 'email_config.py' y configura tus credenciales

# Configuración para Gmail
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'tu_email@gmail.com',  # Tu email de Gmail
    'password': 'tu_app_password',  # Contraseña de aplicación de Gmail
    'use_tls': True
}

# Configuración para Outlook/Hotmail
# EMAIL_CONFIG = {
#     'smtp_server': 'smtp-mail.outlook.com',
#     'smtp_port': 587,
#     'email': 'tu_email@outlook.com',
#     'password': 'tu_contraseña',
#     'use_tls': True
# }

# Configuración para Yahoo
# EMAIL_CONFIG = {
#     'smtp_server': 'smtp.mail.yahoo.com',
#     'smtp_port': 587,
#     'email': 'tu_email@yahoo.com',
#     'password': 'tu_app_password',
#     'use_tls': True
# }

# INSTRUCCIONES PARA GMAIL:
# 1. Habilita la verificación en 2 pasos en tu cuenta de Google
# 2. Ve a https://myaccount.google.com/apppasswords
# 3. Genera una contraseña de aplicación para "Mail"
# 4. Usa esa contraseña de aplicación en lugar de tu contraseña normal

# INSTRUCCIONES PARA OUTLOOK:
# 1. Ve a https://account.microsoft.com/security
# 2. Habilita la verificación en 2 pasos
# 3. Genera una contraseña de aplicación
# 4. Usa esa contraseña de aplicación

# NOTA DE SEGURIDAD:
# - Nunca subas este archivo con credenciales reales a un repositorio público
# - Mantén tus credenciales seguras y no las compartas
# - Considera usar variables de entorno para mayor seguridad