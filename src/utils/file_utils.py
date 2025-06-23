# Utilidades para manejo de archivos
import os
import tempfile
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_content: bytes) -> Optional[str]:
    """Extraer texto de un archivo PDF"""
    try:
        import PyPDF2
        from io import BytesIO
        
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
        
    except ImportError:
        logger.error("PyPDF2 no está instalado")
        return None
    except Exception as e:
        logger.error(f"Error extrayendo texto del PDF: {e}")
        return None

def extract_text_from_docx(file_content: bytes) -> Optional[str]:
    """Extraer texto de un archivo DOCX"""
    try:
        from docx import Document
        from io import BytesIO
        
        doc_file = BytesIO(file_content)
        doc = Document(doc_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
        
    except ImportError:
        logger.error("python-docx no está instalado")
        return None
    except Exception as e:
        logger.error(f"Error extrayendo texto del DOCX: {e}")
        return None

def extract_text_from_txt(file_content: bytes) -> Optional[str]:
    """Extraer texto de un archivo TXT"""
    try:
        # Intentar diferentes codificaciones
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        logger.error("No se pudo decodificar el archivo de texto")
        return None
        
    except Exception as e:
        logger.error(f"Error extrayendo texto del TXT: {e}")
        return None

def extract_text_from_file(filename: str, file_content: bytes) -> Optional[str]:
    """Extraer texto de un archivo según su extensión"""
    file_extension = os.path.splitext(filename)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_content)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_content)
    elif file_extension in ['.txt', '.text']:
        return extract_text_from_txt(file_content)
    else:
        logger.warning(f"Tipo de archivo no soportado: {file_extension}")
        return None

def validate_file_type(filename: str) -> bool:
    """Validar si el tipo de archivo es soportado"""
    allowed_extensions = ['.pdf', '.docx', '.txt', '.text']
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in allowed_extensions

def validate_file_size(file_content: bytes, max_size_mb: int = 10) -> bool:
    """Validar el tamaño del archivo"""
    file_size_mb = len(file_content) / (1024 * 1024)
    return file_size_mb <= max_size_mb

def get_file_info(filename: str, file_content: bytes) -> dict:
    """Obtener información del archivo"""
    file_extension = os.path.splitext(filename)[1].lower()
    file_size = len(file_content)
    file_size_mb = file_size / (1024 * 1024)
    
    return {
        'filename': filename,
        'extension': file_extension,
        'size_bytes': file_size,
        'size_mb': round(file_size_mb, 2),
        'is_valid_type': validate_file_type(filename),
        'is_valid_size': validate_file_size(file_content)
    }

def sanitize_filename(filename: str) -> str:
    """Sanitizar nombre de archivo"""
    import re
    
    # Remover caracteres no válidos
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limitar longitud
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext

def create_temp_file(content: bytes, suffix: str = '') -> Tuple[str, str]:
    """Crear archivo temporal"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            return temp_file.name, temp_file.name
    except Exception as e:
        logger.error(f"Error creando archivo temporal: {e}")
        return None, None

def cleanup_temp_file(file_path: str):
    """Limpiar archivo temporal"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.error(f"Error eliminando archivo temporal {file_path}: {e}")