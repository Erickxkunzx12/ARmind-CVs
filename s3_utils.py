import boto3
import json
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from config_manager import ConfigManager

def get_s3_client():
    """Crear cliente S3 con las credenciales configuradas"""
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        return boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
    except NoCredentialsError:
        print("Error: Credenciales de AWS no configuradas")
        return None
    except Exception as e:
        print(f"Error al crear cliente S3: {e}")
        return None

def generate_s3_key(user_id, analysis_type, ai_provider):
    """Generar clave S3 única para el análisis"""
    config_manager = ConfigManager()
    config = config_manager.get_config()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{config.S3_FOLDER_PREFIX}user_{user_id}/{analysis_type}_{ai_provider}_{timestamp}.json"

def save_analysis_to_s3(user_id, analysis_data, analysis_type, ai_provider):
    """Guardar análisis de CV en S3"""
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Generar clave S3
        s3_key = generate_s3_key(user_id, analysis_type, ai_provider)
        
        # Preparar datos para S3
        s3_data = {
            'user_id': user_id,
            'analysis_type': analysis_type,
            'ai_provider': ai_provider,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_data
        }
        
        # Subir a S3
        s3_client.put_object(
            Bucket=config.S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(s3_data, ensure_ascii=False, indent=2),
            ContentType='application/json',
            Metadata={
                'user_id': str(user_id),
                'analysis_type': analysis_type,
                'ai_provider': ai_provider
            }
        )
        
        print(f"Análisis guardado en S3: {s3_key}")
        return s3_key
        
    except ClientError as e:
        print(f"Error al guardar en S3: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al guardar en S3: {e}")
        return None

def get_analysis_from_s3(s3_key):
    """Recuperar análisis de CV desde S3"""
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        response = s3_client.get_object(
            Bucket=config.S3_BUCKET_NAME,
            Key=s3_key
        )
        
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data['analysis']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"Análisis no encontrado en S3: {s3_key}")
        else:
            print(f"Error al recuperar de S3: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al recuperar de S3: {e}")
        return None

def delete_analysis_from_s3(s3_key):
    """Eliminar análisis de CV desde S3"""
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        s3_client.delete_object(
            Bucket=config.S3_BUCKET_NAME,
            Key=s3_key
        )
        print(f"Análisis eliminado de S3: {s3_key}")
        return True
        
    except ClientError as e:
        print(f"Error al eliminar de S3: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado al eliminar de S3: {e}")
        return False

def list_user_analyses_in_s3(user_id):
    """Listar todos los análisis de un usuario en S3"""
    s3_client = get_s3_client()
    if not s3_client:
        return []
    
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        prefix = f"{config.S3_FOLDER_PREFIX}user_{user_id}/"
        
        response = s3_client.list_objects_v2(
            Bucket=config.S3_BUCKET_NAME,
            Prefix=prefix
        )
        
        analyses = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # Extraer información del nombre del archivo
                key = obj['Key']
                filename = key.split('/')[-1]  # Obtener solo el nombre del archivo
                
                # Parsear información del nombre del archivo
                if filename.endswith('.json'):
                    parts = filename.replace('.json', '').split('_')
                    if len(parts) >= 3:
                        analysis_type = parts[0]
                        ai_provider = parts[1]
                        timestamp = '_'.join(parts[2:])
                        
                        analyses.append({
                            's3_key': key,
                            'analysis_type': analysis_type,
                            'ai_provider': ai_provider,
                            'timestamp': timestamp,
                            'last_modified': obj['LastModified']
                        })
        
        return analyses
        
    except ClientError as e:
        print(f"Error al listar análisis en S3: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado al listar análisis en S3: {e}")
        return []

def delete_old_analysis_for_section(user_id, analysis_type, ai_provider):
    """Eliminar análisis anterior para la misma sección y proveedor de IA"""
    analyses = list_user_analyses_in_s3(user_id)
    
    for analysis in analyses:
        if (analysis['analysis_type'] == analysis_type and 
            analysis['ai_provider'] == ai_provider):
            delete_analysis_from_s3(analysis['s3_key'])
            print(f"Análisis anterior eliminado: {analysis['s3_key']}")

def check_s3_connection():
    """
    Check if S3 connection is working
    """
    try:
        s3_client = get_s3_client()
        if not s3_client:
            return {'success': False, 'error': 'Failed to create S3 client'}
        
        # Try to list buckets to test connection
        s3_client.list_buckets()
        return {'success': True, 'message': 'S3 connection successful'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_bucket_if_not_exists():
    """
    Create S3 bucket if it doesn't exist
    """
    try:
        s3_client = get_s3_client()
        if not s3_client:
            return {'success': False, 'error': 'Failed to create S3 client'}
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        bucket_name = config.S3_BUCKET_NAME
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            return {
                'success': True, 
                'message': f'Bucket {bucket_name} already exists',
                'bucket_name': bucket_name
            }
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    if config.AWS_REGION == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': config.AWS_REGION}
                        )
                    
                    return {
                        'success': True, 
                        'message': f'Bucket {bucket_name} created successfully',
                        'bucket_name': bucket_name
                    }
                except Exception as create_error:
                    return {
                        'success': False, 
                        'error': f'Failed to create bucket: {str(create_error)}'
                    }
            else:
                return {
                    'success': False, 
                    'error': f'Error checking bucket: {str(e)}'
                }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}