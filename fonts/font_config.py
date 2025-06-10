
# -*- coding: utf-8 -*-
"""
Configuración de fuentes para ReportLab con soporte UTF-8
"""

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import os

def register_fonts():
    """Registrar fuentes disponibles para ReportLab"""
    
    fonts_dir = Path(__file__).parent
    
    # Mapeo de fuentes disponibles
    font_mapping = {
        'DejaVuSans': 'DejaVuSans.ttf',
        'DejaVuSans-Bold': 'DejaVuSans-Bold.ttf',
        'DejaVuSans-Oblique': 'DejaVuSans-Oblique.ttf',
        'DejaVuSans-BoldOblique': 'DejaVuSans-BoldOblique.ttf'
    }
    
    registered_fonts = []
    
    for font_name, font_file in font_mapping.items():
        font_path = fonts_dir / font_file
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                registered_fonts.append(font_name)
                print(f"Fuente registrada: {font_name}")
            except Exception as e:
                print(f"Error al registrar fuente {font_name}: {str(e)}")
    
    return registered_fonts

def get_best_font():
    """Obtener la mejor fuente disponible para UTF-8"""
    
    # Intentar registrar fuentes
    registered = register_fonts()
    
    # Prioridad de fuentes
    font_priority = ['DejaVuSans', 'DejaVuSans-Bold']
    
    for font in font_priority:
        if font in registered:
            return font
    
    # Fallback a fuente por defecto
    return 'Helvetica'
