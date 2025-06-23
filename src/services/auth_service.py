# Servicio de autenticación y gestión de usuarios
from typing import Optional, Dict, Any, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from core.models import UserProfile
from core.database import get_db_service
from utils.validation import validate_email_format, validate_password_strength, sanitize_input
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AuthService:
    """Servicio centralizado para autenticación y gestión de usuarios"""
    
    def __init__(self):
        self.db_service = get_db_service()
    
    def register_user(self, email: str, password: str, name: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Registrar nuevo usuario"""
        try:
            # Sanitizar inputs
            email = sanitize_input(email).lower().strip()
            name = sanitize_input(name) if name else None
            
            # Validar email
            if not validate_email_format(email):
                return False, {'error': 'Formato de email inválido'}
            
            # Validar contraseña
            password_validation = validate_password_strength(password)
            if not password_validation['is_valid']:
                return False, {'error': password_validation['message']}
            
            # Verificar si el usuario ya existe
            if self.user_exists(email):
                return False, {'error': 'El email ya está registrado'}
            
            # Hash de la contraseña
            password_hash = generate_password_hash(password)
            
            # Crear perfil de usuario
            user_profile = UserProfile(
                id=None,
                email=email,
                password_hash=password_hash,
                name=name,
                created_at=datetime.now(),
                last_login=None,
                is_active=True
            )
            
            # Guardar en base de datos
            user_id = self.db_service.create_user(user_profile)
            if not user_id:
                return False, {'error': 'Error creando usuario en base de datos'}
            
            logger.info(f"Usuario registrado exitosamente: {email} (ID: {user_id})")
            
            return True, {
                'user_id': user_id,
                'email': email,
                'name': name,
                'message': 'Usuario registrado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error registrando usuario: {e}")
            return False, {'error': f'Error interno: {str(e)}'}
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        """Autenticar usuario"""
        try:
            # Sanitizar email
            email = sanitize_input(email).lower().strip()
            
            # Validar formato de email
            if not validate_email_format(email):
                return False, {'error': 'Formato de email inválido'}
            
            # Obtener usuario de la base de datos
            user = self.get_user_by_email(email)
            if not user:
                return False, {'error': 'Credenciales inválidas'}
            
            # Verificar contraseña
            if not check_password_hash(user.password_hash, password):
                return False, {'error': 'Credenciales inválidas'}
            
            # Verificar si el usuario está activo
            if not user.is_active:
                return False, {'error': 'Cuenta desactivada'}
            
            # Actualizar último login
            self.update_last_login(user.id)
            
            logger.info(f"Usuario autenticado exitosamente: {email}")
            
            return True, {
                'user_id': user.id,
                'email': user.email,
                'name': user.name,
                'message': 'Autenticación exitosa'
            }
            
        except Exception as e:
            logger.error(f"Error autenticando usuario: {e}")
            return False, {'error': f'Error interno: {str(e)}'}
    
    def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """Obtener usuario por email"""
        try:
            email = sanitize_input(email).lower().strip()
            return self.db_service.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error obteniendo usuario por email: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """Obtener usuario por ID"""
        try:
            return self.db_service.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID: {e}")
            return None
    
    def user_exists(self, email: str) -> bool:
        """Verificar si un usuario existe"""
        return self.get_user_by_email(email) is not None
    
    def update_user_profile(self, user_id: int, updates: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Actualizar perfil de usuario"""
        try:
            # Validar que el usuario existe
            user = self.get_user_by_id(user_id)
            if not user:
                return False, {'error': 'Usuario no encontrado'}
            
            # Sanitizar y validar campos permitidos
            allowed_fields = ['name', 'email']
            sanitized_updates = {}
            
            for field, value in updates.items():
                if field in allowed_fields and value is not None:
                    if field == 'email':
                        email = sanitize_input(value).lower().strip()
                        if not validate_email_format(email):
                            return False, {'error': 'Formato de email inválido'}
                        # Verificar que el nuevo email no esté en uso
                        if email != user.email and self.user_exists(email):
                            return False, {'error': 'El email ya está en uso'}
                        sanitized_updates[field] = email
                    else:
                        sanitized_updates[field] = sanitize_input(value)
            
            if not sanitized_updates:
                return False, {'error': 'No hay campos válidos para actualizar'}
            
            # Actualizar en base de datos
            success = self.db_service.update_user_profile(user_id, sanitized_updates)
            if not success:
                return False, {'error': 'Error actualizando perfil'}
            
            logger.info(f"Perfil actualizado exitosamente para usuario {user_id}")
            
            return True, {
                'message': 'Perfil actualizado exitosamente',
                'updated_fields': list(sanitized_updates.keys())
            }
            
        except Exception as e:
            logger.error(f"Error actualizando perfil: {e}")
            return False, {'error': f'Error interno: {str(e)}'}
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, Dict[str, Any]]:
        """Cambiar contraseña de usuario"""
        try:
            # Obtener usuario
            user = self.get_user_by_id(user_id)
            if not user:
                return False, {'error': 'Usuario no encontrado'}
            
            # Verificar contraseña actual
            if not check_password_hash(user.password_hash, current_password):
                return False, {'error': 'Contraseña actual incorrecta'}
            
            # Validar nueva contraseña
            password_validation = validate_password_strength(new_password)
            if not password_validation['is_valid']:
                return False, {'error': password_validation['message']}
            
            # Verificar que la nueva contraseña sea diferente
            if check_password_hash(user.password_hash, new_password):
                return False, {'error': 'La nueva contraseña debe ser diferente a la actual'}
            
            # Hash de la nueva contraseña
            new_password_hash = generate_password_hash(new_password)
            
            # Actualizar en base de datos
            success = self.db_service.update_user_password(user_id, new_password_hash)
            if not success:
                return False, {'error': 'Error actualizando contraseña'}
            
            logger.info(f"Contraseña cambiada exitosamente para usuario {user_id}")
            
            return True, {'message': 'Contraseña actualizada exitosamente'}
            
        except Exception as e:
            logger.error(f"Error cambiando contraseña: {e}")
            return False, {'error': f'Error interno: {str(e)}'}
    
    def deactivate_user(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Desactivar usuario"""
        try:
            success = self.db_service.update_user_profile(user_id, {'is_active': False})
            if not success:
                return False, {'error': 'Error desactivando usuario'}
            
            logger.info(f"Usuario {user_id} desactivado exitosamente")
            return True, {'message': 'Usuario desactivado exitosamente'}
            
        except Exception as e:
            logger.error(f"Error desactivando usuario: {e}")
            return False, {'error': f'Error interno: {str(e)}'}
    
    def update_last_login(self, user_id: int) -> bool:
        """Actualizar último login del usuario"""
        try:
            return self.db_service.update_user_profile(user_id, {'last_login': datetime.now()})
        except Exception as e:
            logger.error(f"Error actualizando último login: {e}")
            return False
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Obtener estadísticas del usuario"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {}
            
            # Obtener CVs del usuario
            cv_documents = self.db_service.get_user_cvs(user_id)
            
            # Obtener análisis del usuario
            analysis_results = self.db_service.get_user_analysis_results(user_id)
            
            stats = {
                'user_info': {
                    'email': user.email,
                    'name': user.name,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'is_active': user.is_active
                },
                'activity': {
                    'total_cvs': len(cv_documents),
                    'total_analyses': len(analysis_results),
                    'cv_types': {},
                    'analysis_types': {},
                    'ai_providers_used': set()
                }
            }
            
            # Estadísticas de CVs
            for cv in cv_documents:
                file_type = cv.file_type
                stats['activity']['cv_types'][file_type] = stats['activity']['cv_types'].get(file_type, 0) + 1
            
            # Estadísticas de análisis
            for analysis in analysis_results:
                analysis_type = analysis.analysis_type
                ai_provider = analysis.ai_provider
                
                stats['activity']['analysis_types'][analysis_type] = stats['activity']['analysis_types'].get(analysis_type, 0) + 1
                stats['activity']['ai_providers_used'].add(ai_provider)
            
            # Convertir set a lista para JSON
            stats['activity']['ai_providers_used'] = list(stats['activity']['ai_providers_used'])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del usuario: {e}")
            return {}

# Instancia global del servicio
auth_service = AuthService()

def get_auth_service() -> AuthService:
    """Obtener instancia del servicio de autenticación"""
    return auth_service