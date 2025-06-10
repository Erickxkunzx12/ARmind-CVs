import smtplib
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales
email_user = os.getenv('EMAIL_USER')
email_password = os.getenv('EMAIL_PASSWORD')
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT'))

print(f"Probando conexión SMTP...")
print(f"Servidor: {smtp_server}:{smtp_port}")
print(f"Usuario: {email_user}")
print(f"Contraseña: {email_password}")
print("="*50)

try:
    # Crear conexión SMTP
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    
    print("✅ Conexión establecida")
    print("Intentando autenticación...")
    
    # Intentar login
    server.login(email_user, email_password)
    print("✅ Autenticación exitosa")
    
    server.quit()
    print("✅ Conexión cerrada correctamente")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Error de autenticación: {e}")
    print("Posibles causas:")
    print("1. Contraseña de aplicación incorrecta")
    print("2. Verificación en 2 pasos no habilitada")
    print("3. Contraseña de aplicación expirada")
    
except Exception as e:
    print(f"❌ Error general: {e}")