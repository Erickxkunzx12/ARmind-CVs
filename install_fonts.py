#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar e instalar fuentes DejaVu Sans para ReportLab
"""

import os
import urllib.request
import zipfile
from pathlib import Path

def download_dejavu_fonts():
    """Descargar fuentes DejaVu Sans desde el repositorio oficial"""
    
    # URL de las fuentes DejaVu Sans
    font_url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"
    
    # Crear directorio de fuentes si no existe
    fonts_dir = Path("fonts")
    fonts_dir.mkdir(exist_ok=True)
    
    zip_path = fonts_dir / "dejavu-fonts.zip"
    
    try:
        print("Descargando fuentes DejaVu Sans...")
        urllib.request.urlretrieve(font_url, zip_path)
        
        print("Extrayendo fuentes...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extraer solo los archivos TTF que necesitamos
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.ttf'):
                    # Extraer solo el nombre del archivo, no la ruta completa
                    file_info.filename = os.path.basename(file_info.filename)
                    zip_ref.extract(file_info, fonts_dir)
        
        # Limpiar archivo zip
        zip_path.unlink()
        
        print("Fuentes instaladas correctamente en el directorio 'fonts/'")
        
        # Listar fuentes instaladas
        font_files = list(fonts_dir.glob('*.ttf'))
        print(f"Fuentes disponibles: {[f.name for f in font_files]}")
        
        return True
        
    except Exception as e:
        print(f"Error al descargar fuentes: {str(e)}")
        return False

def create_font_fallback():
    """Crear fuentes de respaldo embebidas"""
    
    fonts_dir = Path("fonts")
    fonts_dir.mkdir(exist_ok=True)
    
    # Crear un archivo de configuración de fuentes
    font_config = fonts_dir / "font_config.py"
    
    font_config_content = '''
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
'''
    
    with open(font_config, 'w', encoding='utf-8') as f:
        f.write(font_config_content)
    
    print(f"Archivo de configuración de fuentes creado: {font_config}")

if __name__ == "__main__":
    print("Instalando fuentes para soporte UTF-8 en PDFs...")
    
    # Intentar descargar fuentes DejaVu
    if not download_dejavu_fonts():
        print("No se pudieron descargar las fuentes, creando configuración de respaldo...")
    
    # Crear configuración de fuentes
    create_font_fallback()
    
    print("\nInstalación completada. Las fuentes están listas para usar con ReportLab.")