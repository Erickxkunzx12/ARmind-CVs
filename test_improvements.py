"""Tests para verificar las mejoras implementadas en el proyecto WEB ARMIND"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar módulos a testear
from utils.database_context import (
    DatabaseValidator, AdminLogger, DatabaseService,
    safe_float, safe_int, sanitize_string
)
from security_improvements import (
    SecurityManager, LoginAttemptManager, SessionManager
)

class TestDatabaseValidator(unittest.TestCase):
    """Tests para DatabaseValidator"""
    
    def test_validate_seller_data_valid(self):
        """Test validación de datos de vendedor válidos"""
        valid_data = {
            'name': 'Juan Pérez',
            'email': 'juan@example.com',
            'phone': '+1234567890',
            'commission_rate': 0.15
        }
        
        errors = DatabaseValidator.validate_seller_data(valid_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_seller_data_invalid_email(self):
        """Test validación de datos de vendedor con email inválido"""
        invalid_data = {
            'name': 'Juan Pérez',
            'email': 'email-invalido',
            'phone': '+1234567890',
            'commission_rate': 0.15
        }
        
        errors = DatabaseValidator.validate_seller_data(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('email' in error.lower() for error in errors))
    
    def test_validate_seller_data_invalid_commission(self):
        """Test validación de datos de vendedor con comisión inválida"""
        invalid_data = {
            'name': 'Juan Pérez',
            'email': 'juan@example.com',
            'phone': '+1234567890',
            'commission_rate': 1.5  # Mayor a 100%
        }
        
        errors = DatabaseValidator.validate_seller_data(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('comisión' in error.lower() for error in errors))
    
    def test_validate_offer_data_valid(self):
        """Test validación de datos de oferta válidos"""
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        valid_data = {
            'title': 'Oferta Especial',
            'description': 'Descripción de la oferta',
            'discount_percentage': 25.0,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': future_date
        }
        
        errors = DatabaseValidator.validate_offer_data(valid_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_offer_data_invalid_dates(self):
        """Test validación de datos de oferta con fechas inválidas"""
        past_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        invalid_data = {
            'title': 'Oferta Especial',
            'description': 'Descripción de la oferta',
            'discount_percentage': 25.0,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': past_date  # Fecha de fin en el pasado
        }
        
        errors = DatabaseValidator.validate_offer_data(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('fecha' in error.lower() for error in errors))

class TestSecurityManager(unittest.TestCase):
    """Tests para SecurityManager"""
    
    def test_hash_and_verify_password(self):
        """Test hash y verificación de contraseña"""
        password = "MiPassword123!"
        
        # Hash de la contraseña
        hashed = SecurityManager.hash_password(password)
        self.assertIsInstance(hashed, str)
        self.assertGreater(len(hashed), 64)  # Salt + hash
        
        # Verificar contraseña correcta
        self.assertTrue(SecurityManager.verify_password(password, hashed))
        
        # Verificar contraseña incorrecta
        self.assertFalse(SecurityManager.verify_password("password_incorrecta", hashed))
    
    def test_validate_password_strength_strong(self):
        """Test validación de contraseña fuerte"""
        strong_password = "SecurePass789"  # Contraseña fuerte sin patrones comunes
        errors = SecurityManager.validate_password_strength(strong_password)
        self.assertEqual(len(errors), 0)
    
    def test_validate_password_strength_weak(self):
        """Test validación de contraseña débil"""
        weak_passwords = [
            "123456",  # Muy corta y común
            "password",  # Común
            "PASSWORD",  # Solo mayúsculas
            "password123",  # Sin mayúsculas ni caracteres especiales
            "Password",  # Sin números ni caracteres especiales
        ]
        
        for weak_password in weak_passwords:
            errors = SecurityManager.validate_password_strength(weak_password)
            self.assertGreater(len(errors), 0, f"Contraseña '{weak_password}' debería ser inválida")
    
    def test_validate_email(self):
        """Test validación de email"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        invalid_emails = [
            "email_sin_arroba",
            "@domain.com",
            "user@",
            "user@domain",
            "user..name@domain.com"
        ]
        
        for email in valid_emails:
            self.assertTrue(SecurityManager.validate_email(email), f"Email '{email}' debería ser válido")
        
        for email in invalid_emails:
            self.assertFalse(SecurityManager.validate_email(email), f"Email '{email}' debería ser inválido")
    
    def test_validate_phone(self):
        """Test validación de teléfono"""
        valid_phones = [
            "1234567890",
            "+1234567890",
            "(123) 456-7890",
            "+1 (123) 456-7890",
            "123-456-7890"
        ]
        
        invalid_phones = [
            "123",  # Muy corto
            "abc1234567890",  # Contiene letras
            "123456789012345678",  # Muy largo
            "",  # Vacío
        ]
        
        for phone in valid_phones:
            self.assertTrue(SecurityManager.validate_phone(phone), f"Teléfono '{phone}' debería ser válido")
        
        for phone in invalid_phones:
            self.assertFalse(SecurityManager.validate_phone(phone), f"Teléfono '{phone}' debería ser inválido")
    
    def test_sanitize_input(self):
        """Test sanitización de entrada"""
        dangerous_input = "<script>alert('xss')</script>"
        sanitized = SecurityManager.sanitize_input(dangerous_input)
        
        # Verificar que se removieron caracteres peligrosos
        self.assertNotIn('<', sanitized)
        self.assertNotIn('>', sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("'", sanitized)
    
    def test_generate_secure_token(self):
        """Test generación de token seguro"""
        token1 = SecurityManager.generate_secure_token()
        token2 = SecurityManager.generate_secure_token()
        
        # Verificar que los tokens son diferentes
        self.assertNotEqual(token1, token2)
        
        # Verificar longitud
        self.assertGreater(len(token1), 20)
        self.assertGreater(len(token2), 20)

class TestUtilityFunctions(unittest.TestCase):
    """Tests para funciones de utilidad"""
    
    def test_safe_float(self):
        """Test conversión segura a float"""
        # Casos válidos
        self.assertEqual(safe_float("10.5"), 10.5)
        self.assertEqual(safe_float("0"), 0.0)
        self.assertEqual(safe_float(10), 10.0)
        
        # Casos inválidos
        self.assertIsNone(safe_float("abc"))
        self.assertIsNone(safe_float(""))
        self.assertIsNone(safe_float(None))
        
        # Con valor por defecto
        self.assertEqual(safe_float("abc", 5.0), 5.0)
    
    def test_safe_int(self):
        """Test conversión segura a int"""
        # Casos válidos
        self.assertEqual(safe_int("10"), 10)
        self.assertEqual(safe_int("0"), 0)
        self.assertEqual(safe_int(10.5), 10)
        
        # Casos inválidos
        self.assertIsNone(safe_int("abc"))
        self.assertIsNone(safe_int(""))
        self.assertIsNone(safe_int(None))
        
        # Con valor por defecto
        self.assertEqual(safe_int("abc", 5), 5)
    
    def test_sanitize_string(self):
        """Test sanitización de string"""
        # String normal
        self.assertEqual(sanitize_string("Hola Mundo"), "Hola Mundo")
        
        # String con espacios extra
        self.assertEqual(sanitize_string("  Hola Mundo  "), "Hola Mundo")
        
        # String con caracteres especiales
        result = sanitize_string("Hola<script>Mundo")
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        
        # String con longitud máxima
        long_string = "a" * 100
        result = sanitize_string(long_string, 50)
        self.assertEqual(len(result), 50)
        
        # String None
        self.assertEqual(sanitize_string(None), "")

class TestIntegration(unittest.TestCase):
    """Tests de integración"""
    
    @patch('utils.database_context.get_db_cursor')
    def test_database_service_update_entity(self, mock_cursor):
        """Test actualización de entidad en DatabaseService"""
        # Mock del cursor
        mock_cursor_instance = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.rowcount = 1
        
        # Test actualización exitosa
        success, message = DatabaseService.update_entity(
            'sellers', 1, ['name', 'email'], 
            name='Juan Pérez', email='juan@example.com'
        )
        
        self.assertTrue(success)
        self.assertIn('actualizado', message.lower())
        
        # Verificar que se llamó execute
        mock_cursor_instance.execute.assert_called()
    
    @patch('utils.database_context.get_db_cursor')
    def test_database_service_get_entity_by_id(self, mock_cursor):
        """Test obtención de entidad por ID"""
        # Mock del cursor
        mock_cursor_instance = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {
            'id': 1, 'name': 'Juan Pérez', 'email': 'juan@example.com'
        }
        
        # Test obtención exitosa
        result = DatabaseService.get_entity_by_id('sellers', 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], 'Juan Pérez')
        
        # Verificar que se llamó execute
        mock_cursor_instance.execute.assert_called()

def run_tests():
    """Ejecutar todos los tests"""
    # Crear suite de tests
    test_suite = unittest.TestSuite()
    
    # Agregar tests
    test_classes = [
        TestDatabaseValidator,
        TestSecurityManager,
        TestUtilityFunctions,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Mostrar resumen
    print(f"\n{'='*50}")
    print(f"RESUMEN DE TESTS")
    print(f"{'='*50}")
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Éxito: {result.wasSuccessful()}")
    
    if result.errors:
        print(f"\nERRORES:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    if result.failures:
        print(f"\nFALLOS:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Ejecutando tests para las mejoras implementadas...")
    print("="*60)
    
    success = run_tests()
    
    if success:
        print("\n✅ Todos los tests pasaron exitosamente!")
        print("Las mejoras implementadas están funcionando correctamente.")
    else:
        print("\n❌ Algunos tests fallaron.")
        print("Revisar los errores arriba para corregir los problemas.")
    
    # Salir con código apropiado
    sys.exit(0 if success else 1)