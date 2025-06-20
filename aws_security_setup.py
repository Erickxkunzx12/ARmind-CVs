#!/usr/bin/env python3
"""
Configuración de Seguridad AWS para ARMind
Implementa rotación de credenciales y configuración de IAM roles.
"""

import os
import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional

class AWSSecuritySetup:
    """Configurador de seguridad AWS"""
    
    def __init__(self):
        self.iam = None
        self.sts = None
        self.s3 = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializar clientes AWS"""
        try:
            self.iam = boto3.client('iam')
            self.sts = boto3.client('sts')
            self.s3 = boto3.client('s3')
        except Exception as e:
            print(f"⚠️ Error inicializando clientes AWS: {e}")
    
    def create_iam_role_for_ec2(self, role_name: str = "ARMindEC2Role") -> Dict[str, any]:
        """Crear rol IAM para instancias EC2"""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Crear rol
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Rol para aplicación ARMind en EC2"
            )
            
            print(f"✅ Rol IAM creado: {role_name}")
            return {
                'success': True,
                'role_arn': response['Role']['Arn'],
                'role_name': role_name
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"ℹ️ Rol {role_name} ya existe")
                try:
                    role = self.iam.get_role(RoleName=role_name)
                    return {
                        'success': True,
                        'role_arn': role['Role']['Arn'],
                        'role_name': role_name,
                        'already_exists': True
                    }
                except ClientError:
                    pass
            
            print(f"❌ Error creando rol IAM: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_s3_policy(self, bucket_name: str, policy_name: str = "ARMindS3Policy") -> Dict[str, any]:
        """Crear política para acceso a S3"""
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
            ]
        }
        
        try:
            response = self.iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description=f"Política de acceso S3 para bucket {bucket_name}"
            )
            
            print(f"✅ Política S3 creada: {policy_name}")
            return {
                'success': True,
                'policy_arn': response['Policy']['Arn'],
                'policy_name': policy_name
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"ℹ️ Política {policy_name} ya existe")
                # Obtener ARN de política existente
                try:
                    account_id = self.sts.get_caller_identity()['Account']
                    policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
                    return {
                        'success': True,
                        'policy_arn': policy_arn,
                        'policy_name': policy_name,
                        'already_exists': True
                    }
                except ClientError:
                    pass
            
            print(f"❌ Error creando política S3: {e}")
            return {'success': False, 'error': str(e)}
    
    def attach_policy_to_role(self, role_name: str, policy_arn: str) -> bool:
        """Adjuntar política a rol"""
        try:
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✅ Política adjuntada al rol {role_name}")
            return True
            
        except ClientError as e:
            print(f"❌ Error adjuntando política: {e}")
            return False
    
    def create_instance_profile(self, role_name: str, profile_name: str = None) -> Dict[str, any]:
        """Crear perfil de instancia para EC2"""
        if profile_name is None:
            profile_name = f"{role_name}Profile"
        
        try:
            # Crear perfil de instancia
            response = self.iam.create_instance_profile(
                InstanceProfileName=profile_name
            )
            
            # Agregar rol al perfil
            self.iam.add_role_to_instance_profile(
                InstanceProfileName=profile_name,
                RoleName=role_name
            )
            
            print(f"✅ Perfil de instancia creado: {profile_name}")
            return {
                'success': True,
                'profile_arn': response['InstanceProfile']['Arn'],
                'profile_name': profile_name
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"ℹ️ Perfil {profile_name} ya existe")
                try:
                    profile = self.iam.get_instance_profile(InstanceProfileName=profile_name)
                    return {
                        'success': True,
                        'profile_arn': profile['InstanceProfile']['Arn'],
                        'profile_name': profile_name,
                        'already_exists': True
                    }
                except ClientError:
                    pass
            
            print(f"❌ Error creando perfil de instancia: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_complete_iam_configuration(self, bucket_name: str) -> Dict[str, any]:
        """Configuración completa de IAM para ARMind"""
        print("🚀 Iniciando configuración completa de IAM...")
        
        results = {
            'role': None,
            'policy': None,
            'instance_profile': None,
            'success': False
        }
        
        # 1. Crear rol IAM
        role_result = self.create_iam_role_for_ec2()
        if not role_result['success']:
            return results
        results['role'] = role_result
        
        # 2. Crear política S3
        policy_result = self.create_s3_policy(bucket_name)
        if not policy_result['success']:
            return results
        results['policy'] = policy_result
        
        # 3. Adjuntar política al rol
        if not self.attach_policy_to_role(role_result['role_name'], policy_result['policy_arn']):
            return results
        
        # 4. Crear perfil de instancia
        profile_result = self.create_instance_profile(role_result['role_name'])
        if not profile_result['success']:
            return results
        results['instance_profile'] = profile_result
        
        results['success'] = True
        print("✅ Configuración IAM completada exitosamente")
        
        return results
    
    def generate_iam_setup_instructions(self, results: Dict[str, any]) -> str:
        """Generar instrucciones para usar IAM roles"""
        if not results['success']:
            return "❌ Error en configuración IAM"
        
        instructions = f"""
🔧 INSTRUCCIONES DE CONFIGURACIÓN IAM
{'='*50}

✅ Configuración completada:
   • Rol IAM: {results['role']['role_name']}
   • Política S3: {results['policy']['policy_name']}
   • Perfil de instancia: {results['instance_profile']['profile_name']}

📋 PASOS PARA IMPLEMENTAR:

1. 🖥️ EN INSTANCIA EC2:
   - Asignar el perfil de instancia: {results['instance_profile']['profile_name']}
   - Esto se hace en la consola AWS o con AWS CLI:
     aws ec2 associate-iam-instance-profile \
       --instance-id i-1234567890abcdef0 \
       --iam-instance-profile Name={results['instance_profile']['profile_name']}

2. 🔧 EN CÓDIGO PYTHON:
   - Remover AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY del .env
   - El SDK de AWS usará automáticamente el rol IAM
   - Ejemplo:
     ```python
     # No necesitas credenciales explícitas
     s3_client = boto3.client('s3')  # Usa automáticamente el rol IAM
     ```

3. 🐳 EN DOCKER/CONTENEDORES:
   - Si usas ECS, asignar el rol a la tarea
   - Si usas EC2 con Docker, el contenedor heredará el rol

4. ⚙️ VARIABLES DE ENTORNO A REMOVER:
   ```
   # Comentar o eliminar estas líneas del .env:
   # AWS_ACCESS_KEY_ID=tu_access_key_aqui
   # AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
   ```

5. ✅ VERIFICACIÓN:
   ```bash
   # Verificar identidad IAM
   aws sts get-caller-identity
   
   # Debería mostrar el ARN del rol:
   # "Arn": "{results['role']['role_arn']}"
   ```

🔒 BENEFICIOS DE SEGURIDAD:
   ✓ No más credenciales hardcodeadas
   ✓ Rotación automática de credenciales
   ✓ Permisos granulares por recurso
   ✓ Auditoría completa en CloudTrail
   ✓ Principio de menor privilegio

⚠️ IMPORTANTE:
   - Revocar las credenciales AWS anteriores
   - Actualizar documentación del equipo
   - Probar en entorno de desarrollo primero
"""
        return instructions
    
    def revoke_old_credentials_guide(self) -> str:
        """Guía para revocar credenciales anteriores"""
        return """
🚨 GUÍA PARA REVOCAR CREDENCIALES ANTERIORES
{'='*50}

⚠️ URGENTE: Si tienes credenciales AWS expuestas en código:

1. 🔍 IDENTIFICAR CREDENCIALES:
   - Buscar AWS_ACCESS_KEY_ID en tu código
   - Revisar archivos .env, config.py, etc.
   - Verificar repositorios Git (historial completo)

2. 🗑️ ELIMINAR CREDENCIALES:
   ```bash
   # Listar usuarios IAM
   aws iam list-users
   
   # Listar access keys del usuario
   aws iam list-access-keys --user-name NOMBRE_USUARIO
   
   # Desactivar access key
   aws iam update-access-key --user-name NOMBRE_USUARIO \
     --access-key-id AKIAIOSFODNN7EXAMPLE --status Inactive
   
   # Eliminar access key
   aws iam delete-access-key --user-name NOMBRE_USUARIO \
     --access-key-id AKIAIOSFODNN7EXAMPLE
   ```

3. 🧹 LIMPIAR REPOSITORIO GIT:
   ```bash
   # Buscar credenciales en historial
   git log --all --full-history -- .env
   git log -p --all -S "AWS_ACCESS_KEY_ID"
   
   # Si encontraste credenciales en historial:
   # OPCIÓN 1: Reescribir historial (PELIGROSO)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch .env' \
     --prune-empty --tag-name-filter cat -- --all
   
   # OPCIÓN 2: Crear nuevo repositorio (MÁS SEGURO)
   # - Hacer backup del código actual
   # - Crear nuevo repositorio
   # - Copiar código sin archivos sensibles
   ```

4. 📧 NOTIFICAR AL EQUIPO:
   - Informar sobre el cambio a IAM roles
   - Actualizar documentación
   - Revisar otros proyectos que usen las mismas credenciales

5. 🔍 MONITOREAR:
   - Revisar CloudTrail por uso no autorizado
   - Configurar alertas de seguridad
   - Verificar facturación por actividad sospechosa

📞 EN CASO DE EMERGENCIA:
   - Contactar soporte AWS inmediatamente
   - Revisar AWS Security Hub
   - Considerar rotar TODAS las credenciales
"""

def main():
    """Función principal"""
    print("🔒 Configurador de Seguridad AWS - ARMind")
    print("="*50)
    
    # Verificar credenciales AWS
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Conectado como: {identity.get('Arn', 'Unknown')}")
    except NoCredentialsError:
        print("❌ No se encontraron credenciales AWS")
        print("   Configura AWS CLI: aws configure")
        return
    except Exception as e:
        print(f"❌ Error de conexión AWS: {e}")
        return
    
    setup = AWSSecuritySetup()
    
    # Obtener nombre del bucket
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not bucket_name or bucket_name.startswith('tu_'):
        bucket_name = input("\n📦 Ingresa el nombre del bucket S3: ").strip()
        if not bucket_name:
            print("❌ Nombre de bucket requerido")
            return
    
    print(f"\n🚀 Configurando IAM para bucket: {bucket_name}")
    
    # Ejecutar configuración completa
    results = setup.setup_complete_iam_configuration(bucket_name)
    
    if results['success']:
        # Mostrar instrucciones
        instructions = setup.generate_iam_setup_instructions(results)
        print("\n" + instructions)
        
        # Guardar configuración
        config_file = 'aws_iam_config.json'
        with open(config_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'bucket_name': bucket_name,
                'iam_configuration': results
            }, f, indent=2)
        
        print(f"\n💾 Configuración guardada en: {config_file}")
        
        # Mostrar guía de revocación
        revoke_guide = setup.revoke_old_credentials_guide()
        print("\n" + revoke_guide)
        
    else:
        print("\n❌ Error en configuración IAM")
        print("   Verifica permisos y configuración AWS")

if __name__ == '__main__':
    main()