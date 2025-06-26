#!/usr/bin/env python3
"""
Script para marcar usuarios de prueba como verificados
"""

# Importar la función de conexión existente
import sys
sys.path.append('.')
from app import get_db_connection

def fix_test_users():
    """Marcar usuarios de prueba como verificados"""
    print("🔧 Actualizando usuarios de prueba...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    test_emails = [
        'admin@armind.test',
        'free@armind.test', 
        'standard@armind.test',
        'pro@armind.test'
    ]
    
    try:
        # Verificar usuarios existentes
        cursor.execute(
            "SELECT email, email_verified FROM users WHERE email = ANY(%s)",
            (test_emails,)
        )
        existing_users = cursor.fetchall()
        
        print(f"\n📋 Usuarios encontrados: {len(existing_users)}")
        for user in existing_users:
            status = "✅ Verificado" if user['email_verified'] else "❌ No verificado"
            print(f"  - {user['email']}: {status}")
        
        # Actualizar usuarios no verificados
        cursor.execute(
            "UPDATE users SET email_verified = TRUE WHERE email = ANY(%s) AND email_verified = FALSE",
            (test_emails,)
        )
        
        updated_count = cursor.rowcount
        connection.commit()
        
        print(f"\n✅ Usuarios actualizados: {updated_count}")
        
        # Verificar resultado
        cursor.execute(
            "SELECT email, email_verified FROM users WHERE email = ANY(%s)",
            (test_emails,)
        )
        final_users = cursor.fetchall()
        
        print("\n📊 Estado final:")
        for user in final_users:
            status = "✅ Verificado" if user['email_verified'] else "❌ No verificado"
            print(f"  - {user['email']}: {status}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando usuarios: {e}")
        connection.rollback()
        cursor.close()
        connection.close()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando corrección de usuarios de prueba...")
    
    if fix_test_users():
        print("\n🎉 ¡Usuarios de prueba actualizados correctamente!")
        print("\n📝 Ahora puedes iniciar sesión con cualquiera de estas credenciales:")
        print("  - admin@armind.test / admin123")
        print("  - free@armind.test / free123")
        print("  - standard@armind.test / standard123")
        print("  - pro@armind.test / pro123")
    else:
        print("\n❌ Error actualizando usuarios de prueba")