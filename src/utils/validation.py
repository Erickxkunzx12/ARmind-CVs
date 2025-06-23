# Utilidades de validación
import re
from typing import List, Dict, Any, Optional

try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False

def validate_email_format(email: str) -> bool:
    """Validar formato de email"""
    if EMAIL_VALIDATOR_AVAILABLE:
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    else:
        # Fallback si email_validator no está disponible
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validar fortaleza de contraseña"""
    result = {
        'is_valid': True,
        'errors': [],
        'score': 0
    }
    
    # Longitud mínima
    if len(password) < 8:
        result['errors'].append('La contraseña debe tener al menos 8 caracteres')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    # Contiene mayúsculas
    if not re.search(r'[A-Z]', password):
        result['errors'].append('La contraseña debe contener al menos una mayúscula')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    # Contiene minúsculas
    if not re.search(r'[a-z]', password):
        result['errors'].append('La contraseña debe contener al menos una minúscula')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    # Contiene números
    if not re.search(r'\d', password):
        result['errors'].append('La contraseña debe contener al menos un número')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    # Contiene caracteres especiales
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['errors'].append('La contraseña debe contener al menos un carácter especial')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    return result

def validate_analysis_result(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Validar resultado de análisis de IA"""
    result = {
        'is_valid': True,
        'errors': []
    }
    
    required_fields = ['score', 'strengths', 'weaknesses', 'recommendations', 'keywords', 'analysis_type']
    
    for field in required_fields:
        if field not in analysis:
            result['errors'].append(f'Campo requerido faltante: {field}')
            result['is_valid'] = False
    
    # Validar score
    if 'score' in analysis:
        score = analysis['score']
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            result['errors'].append('El score debe ser un número entre 0 y 100')
            result['is_valid'] = False
    
    # Validar listas
    list_fields = ['strengths', 'weaknesses', 'recommendations', 'keywords']
    for field in list_fields:
        if field in analysis:
            if not isinstance(analysis[field], list):
                result['errors'].append(f'{field} debe ser una lista')
                result['is_valid'] = False
    
    return result

def validate_cv_content(content: str) -> Dict[str, Any]:
    """Validar contenido de CV"""
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Longitud mínima
    if len(content.strip()) < 100:
        result['errors'].append('El CV debe tener al menos 100 caracteres')
        result['is_valid'] = False
    
    # Longitud máxima
    if len(content) > 50000:
        result['errors'].append('El CV es demasiado largo (máximo 50,000 caracteres)')
        result['is_valid'] = False
    
    # Verificar secciones comunes
    common_sections = ['experiencia', 'educación', 'habilidades', 'contacto', 'email']
    found_sections = []
    
    for section in common_sections:
        if section.lower() in content.lower():
            found_sections.append(section)
    
    if len(found_sections) < 2:
        result['warnings'].append('El CV parece estar incompleto. Considere agregar más secciones.')
    
    # Verificar información de contacto
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'[\+]?[1-9]?[0-9]{7,14}'
    
    if not re.search(email_pattern, content):
        result['warnings'].append('No se encontró información de email')
    
    if not re.search(phone_pattern, content):
        result['warnings'].append('No se encontró información de teléfono')
    
    return result

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitizar entrada de texto"""
    if not isinstance(text, str):
        return ''
    
    # Remover caracteres peligrosos
    text = re.sub(r'[<>"\']', '', text)
    
    # Limitar longitud
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_file_upload(filename: str, file_size: int, allowed_extensions: List[str] = None) -> Dict[str, Any]:
    """Validar archivo subido"""
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.docx', '.txt']
    
    result = {
        'is_valid': True,
        'errors': []
    }
    
    # Validar nombre de archivo
    if not filename or len(filename.strip()) == 0:
        result['errors'].append('Nombre de archivo vacío')
        result['is_valid'] = False
        return result
    
    # Validar extensión
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    if f'.{file_extension}' not in allowed_extensions:
        result['errors'].append(f'Tipo de archivo no permitido. Permitidos: {", ".join(allowed_extensions)}')
        result['is_valid'] = False
    
    # Validar tamaño (10MB máximo)
    max_size = 10 * 1024 * 1024  # 10MB en bytes
    if file_size > max_size:
        result['errors'].append(f'Archivo demasiado grande. Máximo: {max_size // (1024*1024)}MB')
        result['is_valid'] = False
    
    # Validar caracteres en nombre de archivo
    if re.search(r'[<>:"/\\|?*]', filename):
        result['errors'].append('El nombre del archivo contiene caracteres no válidos')
        result['is_valid'] = False
    
    return result

def validate_analysis_type(analysis_type: str) -> bool:
    """Validar tipo de análisis"""
    valid_types = [
        'general_health_check',
        'ats_optimization', 
        'content_enhancement',
        'visual_design_assessment',
        'comprehensive_score'
    ]
    return analysis_type in valid_types

def validate_ai_provider(provider: str) -> bool:
    """Validar proveedor de IA"""
    valid_providers = ['openai', 'anthropic', 'gemini']
    return provider in valid_providers