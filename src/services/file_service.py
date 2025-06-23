# Servicio de gestión de archivos
from typing import Optional, Dict, Any, Tuple
from werkzeug.datastructures import FileStorage
from core.models import CVDocument
from core.database import get_db_service
from utils.file_utils import (
    extract_text_from_file,
    validate_file_type,
    validate_file_size,
    get_file_info,
    sanitize_filename
)
from utils.validation import validate_file_upload, validate_cv_content
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileService:
    """Servicio centralizado para gestión de archivos"""
    
    def __init__(self):
        self.db_service = get_db_service()
        self.allowed_extensions = ['.pdf', '.docx', '.txt', '.text']
        self.max_file_size_mb = 10
    
    def process_uploaded_file(self, file: FileStorage, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Procesar archivo subido"""
        try:
            # Validaciones iniciales
            if not file or not file.filename:
                return False, {'error': 'No se proporcionó archivo'}
            
            # Leer contenido del archivo
            file_content = file.read()
            file.seek(0)  # Resetear puntero para futuras lecturas
            
            # Sanitizar nombre de archivo
            filename = sanitize_filename(file.filename)
            
            # Validar archivo
            validation = validate_file_upload(
                filename, 
                len(file_content), 
                self.allowed_extensions
            )
            
            if not validation['is_valid']:
                return False, {'error': validation['errors'][0]}
            
            # Extraer texto
            extracted_text = extract_text_from_file(filename, file_content)
            if not extracted_text:
                return False, {'error': 'No se pudo extraer texto del archivo'}
            
            # Validar contenido del CV
            content_validation = validate_cv_content(extracted_text)
            if not content_validation['is_valid']:
                return False, {'error': content_validation['errors'][0]}
            
            # Crear objeto CVDocument
            cv_document = CVDocument(
                id=None,
                user_id=user_id,
                filename=filename,
                content=extracted_text,
                file_type=filename.split('.')[-1].lower(),
                upload_date=datetime.now(),
                file_size=len(file_content)
            )
            
            # Guardar en base de datos
            cv_id = self.db_service.save_cv_document(cv_document)
            if not cv_id:
                return False, {'error': 'Error guardando archivo en base de datos'}
            
            # Preparar respuesta exitosa
            result = {
                'cv_id': cv_id,
                'filename': filename,
                'content': extracted_text,
                'file_info': get_file_info(filename, file_content),
                'warnings': content_validation.get('warnings', [])
            }
            
            logger.info(f"Archivo procesado exitosamente: {filename} (ID: {cv_id})")
            return True, result
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {e}")
            return False, {'error': f'Error interno: {str(e)}'}
    
    def get_user_files(self, user_id: int) -> list:
        """Obtener archivos de un usuario"""
        try:
            cv_documents = self.db_service.get_user_cvs(user_id)
            
            files = []
            for cv_doc in cv_documents:
                files.append({
                    'id': cv_doc.id,
                    'filename': cv_doc.filename,
                    'file_type': cv_doc.file_type,
                    'upload_date': cv_doc.upload_date.isoformat() if cv_doc.upload_date else None,
                    'file_size': cv_doc.file_size,
                    'content_preview': cv_doc.content[:200] + '...' if len(cv_doc.content) > 200 else cv_doc.content
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos del usuario {user_id}: {e}")
            return []
    
    def get_file_content(self, file_id: int, user_id: int) -> Optional[str]:
        """Obtener contenido de un archivo específico"""
        try:
            cv_documents = self.db_service.get_user_cvs(user_id)
            
            for cv_doc in cv_documents:
                if cv_doc.id == file_id:
                    return cv_doc.content
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo contenido del archivo {file_id}: {e}")
            return None
    
    def delete_file(self, file_id: int, user_id: int) -> bool:
        """Eliminar archivo"""
        try:
            # Verificar que el archivo pertenece al usuario
            cv_documents = self.db_service.get_user_cvs(user_id)
            file_exists = any(cv.id == file_id for cv in cv_documents)
            
            if not file_exists:
                return False
            
            # Eliminar de base de datos
            connection = self.db_service.get_connection()
            if not connection:
                return False
            
            with connection.cursor() as cursor:
                # Primero eliminar análisis relacionados
                cursor.execute("DELETE FROM feedback WHERE resume_id = %s", (file_id,))
                
                # Luego eliminar el archivo
                cursor.execute("DELETE FROM resumes WHERE id = %s AND user_id = %s", (file_id, user_id))
                
                connection.commit()
            
            logger.info(f"Archivo {file_id} eliminado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando archivo {file_id}: {e}")
            return False
    
    def get_file_statistics(self, user_id: int) -> Dict[str, Any]:
        """Obtener estadísticas de archivos del usuario"""
        try:
            cv_documents = self.db_service.get_user_cvs(user_id)
            
            stats = {
                'total_files': len(cv_documents),
                'total_size_bytes': 0,
                'by_type': {},
                'latest_upload': None,
                'oldest_upload': None
            }
            
            if not cv_documents:
                return stats
            
            upload_dates = []
            
            for cv_doc in cv_documents:
                # Tamaño total
                if cv_doc.file_size:
                    stats['total_size_bytes'] += cv_doc.file_size
                
                # Por tipo
                file_type = cv_doc.file_type
                stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1
                
                # Fechas
                if cv_doc.upload_date:
                    upload_dates.append(cv_doc.upload_date)
            
            # Fechas de subida
            if upload_dates:
                stats['latest_upload'] = max(upload_dates).isoformat()
                stats['oldest_upload'] = min(upload_dates).isoformat()
            
            # Convertir tamaño a MB
            stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de archivos: {e}")
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'by_type': {},
                'latest_upload': None,
                'oldest_upload': None
            }
    
    def validate_file_before_upload(self, file: FileStorage) -> Dict[str, Any]:
        """Validar archivo antes de procesarlo"""
        if not file or not file.filename:
            return {
                'is_valid': False,
                'errors': ['No se proporcionó archivo']
            }
        
        # Leer una muestra del archivo para validación
        file.seek(0)
        sample = file.read(1024)  # Leer primeros 1KB
        file.seek(0)  # Resetear
        
        filename = sanitize_filename(file.filename)
        
        return validate_file_upload(
            filename,
            len(sample) * 1000,  # Estimación aproximada del tamaño
            self.allowed_extensions
        )
    
    def get_supported_formats(self) -> Dict[str, str]:
        """Obtener formatos soportados"""
        return {
            '.pdf': 'Documento PDF',
            '.docx': 'Documento Word',
            '.txt': 'Archivo de texto',
            '.text': 'Archivo de texto'
        }

# Instancia global del servicio
file_service = FileService()

def get_file_service() -> FileService:
    """Obtener instancia del servicio de archivos"""
    return file_service