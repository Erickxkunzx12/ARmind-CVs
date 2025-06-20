#!/usr/bin/env python3
"""
Gestor de Seguridad para ARMind
Implementa logging de seguridad, rotación de credenciales y monitoreo.
"""

import os
import logging
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configurar logging de seguridad
class SecurityLogger:
    """Logger especializado para eventos de seguridad"""
    
    def __init__(self, log_file: str = 'security.log'):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # Crear handler para archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Crear handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formato de logs
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers si no existen
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_login_attempt(self, username: str, ip_address: str, success: bool):
        """Log intento de login"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"LOGIN_{status}: user={username}, ip={ip_address}")
    
    def log_config_access(self, config_type: str, user: str = "system"):
        """Log acceso a configuración"""
        self.logger.info(f"CONFIG_ACCESS: type={config_type}, user={user}")
    
    def log_credential_rotation(self, credential_type: str, success: bool):
        """Log rotación de credenciales"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"CREDENTIAL_ROTATION_{status}: type={credential_type}")
    
    def log_security_event(self, event_type: str, details: str, severity: str = "INFO"):
        """Log evento de seguridad general"""
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(f"SECURITY_EVENT: type={event_type}, details={details}")
    
    def log_api_usage(self, api_name: str, endpoint: str, user: str, response_code: int):
        """Log uso de APIs"""
        self.logger.info(f"API_USAGE: api={api_name}, endpoint={endpoint}, user={user}, code={response_code}")
    
    def log_file_access(self, file_path: str, action: str, user: str):
        """Log acceso a archivos"""
        self.logger.info(f"FILE_ACCESS: file={file_path}, action={action}, user={user}")
    
    def log_database_access(self, action: str, user: str = "system", details: str = ""):
        """Log acceso a base de datos"""
        if details:
            self.logger.info(f"DATABASE_ACCESS: action={action}, user={user}, details={details}")
        else:
            self.logger.info(f"DATABASE_ACCESS: action={action}, user={user}")

class CredentialManager:
    """Gestor de credenciales y rotación"""
    
    def __init__(self, security_logger: SecurityLogger):
        self.security_logger = security_logger
        self.credentials_file = 'credentials_metadata.json'
    
    def generate_secret_key(self, length: int = 32) -> str:
        """Generar nueva SECRET_KEY segura"""
        new_key = secrets.token_urlsafe(length)
        self.security_logger.log_credential_rotation('SECRET_KEY', True)
        return new_key
    
    def check_credential_age(self, credential_type: str) -> Optional[int]:
        """Verificar edad de credenciales en días"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    metadata = json.load(f)
                
                if credential_type in metadata:
                    created_date = datetime.fromisoformat(metadata[credential_type]['created'])
                    age = (datetime.now() - created_date).days
                    return age
        except Exception as e:
            self.security_logger.log_security_event(
                'CREDENTIAL_CHECK_ERROR', 
                f"Error checking {credential_type}: {str(e)}", 
                'ERROR'
            )
        return None
    
    def update_credential_metadata(self, credential_type: str, created_date: datetime = None):
        """Actualizar metadata de credenciales"""
        if created_date is None:
            created_date = datetime.now()
        
        metadata = {}
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r') as f:
                    metadata = json.load(f)
            except:
                pass
        
        metadata[credential_type] = {
            'created': created_date.isoformat(),
            'last_checked': datetime.now().isoformat()
        }
        
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            self.security_logger.log_security_event(
                'METADATA_UPDATE_ERROR',
                f"Error updating metadata: {str(e)}",
                'ERROR'
            )
    
    def check_aws_credentials_rotation(self) -> Dict[str, any]:
        """Verificar si las credenciales AWS necesitan rotación"""
        result = {
            'needs_rotation': False,
            'age_days': None,
            'using_iam_roles': False,
            'recommendations': []
        }
        
        # Verificar si se están usando IAM roles
        if not os.getenv('AWS_ACCESS_KEY_ID') and not os.getenv('AWS_SECRET_ACCESS_KEY'):
            result['using_iam_roles'] = True
            result['recommendations'].append("Usando IAM roles (recomendado)")
            return result
        
        # Verificar edad de credenciales
        age = self.check_credential_age('AWS_CREDENTIALS')
        if age is not None:
            result['age_days'] = age
            if age > 90:  # Rotar cada 90 días
                result['needs_rotation'] = True
                result['recommendations'].append(f"Credenciales AWS tienen {age} días, rotar recomendado")
        
        # Verificar si son credenciales de ejemplo
        access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
        if access_key.startswith('tu_') or 'ejemplo' in access_key.lower():
            result['recommendations'].append("Credenciales AWS parecen ser de ejemplo")
        
        return result
    
    def rotate_secret_key(self) -> str:
        """Rotar SECRET_KEY y actualizar archivo .env"""
        try:
            new_key = self.generate_secret_key()
            
            # Actualizar archivo .env si existe
            env_file = '.env'
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('SECRET_KEY='):
                        lines[i] = f'SECRET_KEY={new_key}\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'SECRET_KEY={new_key}\n')
                
                with open(env_file, 'w') as f:
                    f.writelines(lines)
            
            self.update_credential_metadata('SECRET_KEY')
            self.security_logger.log_credential_rotation('SECRET_KEY', True)
            return new_key
            
        except Exception as e:
            self.security_logger.log_credential_rotation('SECRET_KEY', False)
            self.security_logger.log_security_event(
                'SECRET_KEY_ROTATION_ERROR',
                str(e),
                'ERROR'
            )
            raise

class AWSSecurityManager:
    """Gestor de seguridad específico para AWS"""
    
    def __init__(self, security_logger: SecurityLogger):
        self.security_logger = security_logger
    
    def check_iam_roles_availability(self) -> bool:
        """Verificar si IAM roles están disponibles"""
        try:
            # Intentar crear cliente STS sin credenciales explícitas
            sts = boto3.client('sts')
            response = sts.get_caller_identity()
            
            self.security_logger.log_security_event(
                'IAM_ROLES_CHECK',
                f"IAM identity: {response.get('Arn', 'Unknown')}"
            )
            return True
            
        except NoCredentialsError:
            self.security_logger.log_security_event(
                'IAM_ROLES_CHECK',
                "No IAM roles or credentials available",
                'WARNING'
            )
            return False
        except Exception as e:
            self.security_logger.log_security_event(
                'IAM_ROLES_CHECK_ERROR',
                str(e),
                'ERROR'
            )
            return False
    
    def validate_s3_permissions(self, bucket_name: str) -> Dict[str, bool]:
        """Validar permisos en bucket S3"""
        permissions = {
            'list': False,
            'read': False,
            'write': False,
            'delete': False
        }
        
        try:
            s3 = boto3.client('s3')
            
            # Test list
            try:
                s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                permissions['list'] = True
            except ClientError:
                pass
            
            # Test write (crear objeto temporal)
            test_key = 'security-test-' + secrets.token_hex(8)
            try:
                s3.put_object(Bucket=bucket_name, Key=test_key, Body=b'test')
                permissions['write'] = True
                
                # Test read
                try:
                    s3.get_object(Bucket=bucket_name, Key=test_key)
                    permissions['read'] = True
                except ClientError:
                    pass
                
                # Test delete
                try:
                    s3.delete_object(Bucket=bucket_name, Key=test_key)
                    permissions['delete'] = True
                except ClientError:
                    pass
                    
            except ClientError:
                pass
            
            self.security_logger.log_security_event(
                'S3_PERMISSIONS_CHECK',
                f"Bucket: {bucket_name}, Permissions: {permissions}"
            )
            
        except Exception as e:
            self.security_logger.log_security_event(
                'S3_PERMISSIONS_ERROR',
                f"Error checking S3 permissions: {str(e)}",
                'ERROR'
            )
        
        return permissions

class SecurityAuditor:
    """Auditor de seguridad del sistema"""
    
    def __init__(self):
        self.security_logger = SecurityLogger()
        self.credential_manager = CredentialManager(self.security_logger)
        self.aws_manager = AWSSecurityManager(self.security_logger)
    
    def run_security_audit(self) -> Dict[str, any]:
        """Ejecutar auditoría completa de seguridad"""
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'secret_key_status': self._audit_secret_key(),
            'aws_security': self._audit_aws_security(),
            'environment_variables': self._audit_environment_variables(),
            'file_permissions': self._audit_file_permissions(),
            'recommendations': []
        }
        
        # Generar recomendaciones
        audit_results['recommendations'] = self._generate_recommendations(audit_results)
        
        self.security_logger.log_security_event(
            'SECURITY_AUDIT_COMPLETED',
            f"Audit completed with {len(audit_results['recommendations'])} recommendations"
        )
        
        return audit_results
    
    def _audit_secret_key(self) -> Dict[str, any]:
        """Auditar SECRET_KEY"""
        secret_key = os.getenv('SECRET_KEY', '')
        
        return {
            'exists': bool(secret_key),
            'length': len(secret_key),
            'is_secure': len(secret_key) >= 32 and not secret_key.startswith('dev-'),
            'age_days': self.credential_manager.check_credential_age('SECRET_KEY')
        }
    
    def _audit_aws_security(self) -> Dict[str, any]:
        """Auditar seguridad AWS"""
        return {
            'iam_roles_available': self.aws_manager.check_iam_roles_availability(),
            'credentials_rotation': self.credential_manager.check_aws_credentials_rotation(),
            's3_permissions': self._check_s3_permissions()
        }
    
    def _check_s3_permissions(self) -> Optional[Dict[str, bool]]:
        """Verificar permisos S3 si está configurado"""
        bucket_name = os.getenv('S3_BUCKET_NAME')
        if bucket_name and not bucket_name.startswith('tu_'):
            return self.aws_manager.validate_s3_permissions(bucket_name)
        return None
    
    def _audit_environment_variables(self) -> Dict[str, any]:
        """Auditar variables de entorno"""
        required_vars = ['SECRET_KEY', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        optional_vars = ['OPENAI_API_KEY', 'EMAIL_USER', 'EMAIL_PASSWORD']
        
        missing_required = [var for var in required_vars if not os.getenv(var)]
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        
        # Verificar valores de ejemplo
        example_patterns = ['tu_', 'ejemplo', 'test_', 'dev-']
        example_vars = []
        
        for var in required_vars + optional_vars:
            value = os.getenv(var, '')
            if any(pattern in value.lower() for pattern in example_patterns):
                example_vars.append(var)
        
        return {
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'example_values': example_vars
        }
    
    def _audit_file_permissions(self) -> Dict[str, any]:
        """Auditar permisos de archivos sensibles"""
        sensitive_files = ['.env', 'config.py', 'database_config.py', 'email_config.py']
        file_status = {}
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                file_status[file_path] = {
                    'exists': True,
                    'permissions': oct(stat.st_mode)[-3:],
                    'is_readable_by_others': bool(stat.st_mode & 0o044)
                }
            else:
                file_status[file_path] = {'exists': False}
        
        return file_status
    
    def _generate_recommendations(self, audit_results: Dict[str, any]) -> List[str]:
        """Generar recomendaciones basadas en auditoría"""
        recommendations = []
        
        # SECRET_KEY
        if not audit_results['secret_key_status']['is_secure']:
            recommendations.append("🔑 Generar nueva SECRET_KEY segura (>32 caracteres)")
        
        # Variables de entorno
        env_audit = audit_results['environment_variables']
        if env_audit['missing_required']:
            recommendations.append(f"❌ Configurar variables requeridas: {', '.join(env_audit['missing_required'])}")
        
        if env_audit['example_values']:
            recommendations.append(f"⚠️ Reemplazar valores de ejemplo: {', '.join(env_audit['example_values'])}")
        
        # AWS
        aws_audit = audit_results['aws_security']
        if not aws_audit['iam_roles_available'] and aws_audit['credentials_rotation']['needs_rotation']:
            recommendations.append("🔄 Rotar credenciales AWS (>90 días)")
        
        if not aws_audit['iam_roles_available']:
            recommendations.append("☁️ Considerar usar IAM roles en lugar de credenciales")
        
        # Permisos de archivos
        for file_path, status in audit_results['file_permissions'].items():
            if status.get('is_readable_by_others'):
                recommendations.append(f"🔒 Restringir permisos de {file_path}")
        
        return recommendations

def main():
    """Función principal para ejecutar auditoría"""
    auditor = SecurityAuditor()
    results = auditor.run_security_audit()
    
    print("\n" + "="*60)
    print("🔒 AUDITORÍA DE SEGURIDAD - ARMind")
    print("="*60)
    
    print(f"\n📅 Fecha: {results['timestamp']}")
    
    print("\n🔑 SECRET_KEY:")
    sk_status = results['secret_key_status']
    print(f"   ✅ Existe: {sk_status['exists']}")
    print(f"   📏 Longitud: {sk_status['length']} caracteres")
    print(f"   🔒 Segura: {sk_status['is_secure']}")
    
    print("\n☁️ AWS:")
    aws_status = results['aws_security']
    print(f"   🎭 IAM Roles: {aws_status['iam_roles_available']}")
    
    print("\n📋 RECOMENDACIONES:")
    if results['recommendations']:
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")
    else:
        print("   ✅ No hay recomendaciones - configuración segura")
    
    print("\n" + "="*60)
    
    # Guardar resultados
    with open('security_audit.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("📄 Resultados guardados en: security_audit.json")
    print("📄 Logs de seguridad en: security.log")

if __name__ == '__main__':
    main()