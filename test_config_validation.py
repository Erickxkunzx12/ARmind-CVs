#!/usr/bin/env python3
"""
Tests unitarios para validar configuraciones del sistema ARMind
"""

import unittest
import os
from unittest.mock import patch, MagicMock
from config_manager import (
    get_config, 
    DevelopmentConfig, 
    ProductionConfig, 
    TestingConfig,
    ConfigurationError,
    validate_full_config
)

class TestConfigurationManager(unittest.TestCase):
    """Tests para el gestor de configuración"""
    
    def setUp(self):
        """Configurar tests"""
        # Limpiar variables de entorno para tests aislados
        self.env_vars_to_clean = [
            'FLASK_ENV', 'SECRET_KEY', 'DB_HOST', 'DB_NAME', 
            'DB_USER', 'DB_PASSWORD', 'DB_PORT'
        ]
        self.original_env = {}
        for var in self.env_vars_to_clean:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Limpiar después de tests"""
        # Restaurar variables de entorno originales
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password'
    })
    def test_development_config_valid(self):
        """Test configuración de desarrollo válida"""
        config = DevelopmentConfig()
        
        self.assertTrue(config.DEBUG)
        self.assertFalse(config.TESTING)
        self.assertEqual(config.ENVIRONMENT, 'development')
        self.assertEqual(config.DATABASE_CONFIG['host'], 'localhost')
        self.assertEqual(config.DATABASE_CONFIG['database'], 'test_db')
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'production_secret_key_very_long_and_secure_123456789',
        'DB_HOST': 'prod-db.example.com',
        'DB_NAME': 'prod_db',
        'DB_USER': 'prod_user',
        'DB_PASSWORD': 'prod_password',
        'OPENAI_API_KEY': 'sk-test123456789'
    })
    def test_production_config_valid(self):
        """Test configuración de producción válida"""
        config = ProductionConfig()
        
        self.assertFalse(config.DEBUG)
        self.assertFalse(config.TESTING)
        self.assertEqual(config.ENVIRONMENT, 'production')
        self.assertEqual(config.DATABASE_CONFIG['host'], 'prod-db.example.com')
    
    def test_missing_required_vars_raises_error(self):
        """Test que variables faltantes lancen error"""
        with self.assertRaises(ConfigurationError):
            DevelopmentConfig()
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'dev-insecure-key',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'sk-test123456789'
    })
    def test_production_config_insecure_secret_raises_error(self):
        """Test que clave insegura en producción lance error"""
        with self.assertRaises(ConfigurationError):
            ProductionConfig()
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password'
    })
    def test_testing_config(self):
        """Test configuración de testing"""
        config = TestingConfig()
        
        self.assertTrue(config.DEBUG)
        self.assertTrue(config.TESTING)
        self.assertEqual(config.ENVIRONMENT, 'testing')
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'FLASK_ENV': 'development'
    })
    def test_get_config_function(self):
        """Test función get_config"""
        config = get_config()
        self.assertIsInstance(config, DevelopmentConfig)
        
        config = get_config('production')
        # Esto debería fallar por configuración insegura
        with self.assertRaises(ConfigurationError):
            config = get_config('production')
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'sk-test123456789',
        'EMAIL_USER': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password'
    })
    def test_ai_apis_validation(self):
        """Test validación de APIs de IA"""
        config = DevelopmentConfig()
        apis_status = config.validate_ai_apis()
        
        self.assertTrue(apis_status['openai'])
        self.assertFalse(apis_status['anthropic'])  # No configurada
        self.assertFalse(apis_status['gemini'])     # No configurada
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'EMAIL_USER': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password'
    })
    def test_email_validation_valid(self):
        """Test validación de email válida"""
        config = DevelopmentConfig()
        self.assertTrue(config.validate_email_config())
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'EMAIL_USER': 'tu_email@gmail.com',  # Valor de ejemplo
        'EMAIL_PASSWORD': 'tu_app_password'   # Valor de ejemplo
    })
    def test_email_validation_example_values(self):
        """Test validación de email con valores de ejemplo"""
        config = DevelopmentConfig()
        self.assertFalse(config.validate_email_config())
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password'
    })
    def test_aws_validation_iam_roles(self):
        """Test validación AWS con IAM roles (sin credenciales)"""
        config = DevelopmentConfig()
        # Sin credenciales AWS = usando IAM roles
        self.assertTrue(config.validate_aws_config())
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'AWS_ACCESS_KEY_ID': 'AKIA123456789',
        'AWS_SECRET_ACCESS_KEY': 'secret123456789'
    })
    def test_aws_validation_credentials(self):
        """Test validación AWS con credenciales"""
        config = DevelopmentConfig()
        self.assertTrue(config.validate_aws_config())
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'AWS_ACCESS_KEY_ID': 'tu_aws_access_key_aqui',  # Valor de ejemplo
        'AWS_SECRET_ACCESS_KEY': 'tu_aws_secret_key_aqui'  # Valor de ejemplo
    })
    def test_aws_validation_example_values(self):
        """Test validación AWS con valores de ejemplo"""
        config = DevelopmentConfig()
        self.assertFalse(config.validate_aws_config())

class TestFullValidation(unittest.TestCase):
    """Tests para validación completa del sistema"""
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test_secret_key_12345678901234567890',
        'DB_HOST': 'localhost',
        'DB_NAME': 'test_db',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'sk-test123456789',
        'EMAIL_USER': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password',
        'AWS_ACCESS_KEY_ID': 'AKIA123456789',
        'AWS_SECRET_ACCESS_KEY': 'secret123456789'
    })
    def test_validate_full_config(self):
        """Test validación completa de configuración"""
        config = DevelopmentConfig()
        results = validate_full_config(config)
        
        self.assertIn('ai_apis', results)
        self.assertIn('aws_config', results)
        self.assertIn('email_config', results)
        
        # Verificar que al menos algunas validaciones pasen
        self.assertTrue(results['aws_config'])
        self.assertTrue(results['email_config'])

if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.getLogger('security').setLevel(logging.CRITICAL)  # Silenciar logs durante tests
    
    unittest.main(verbosity=2)