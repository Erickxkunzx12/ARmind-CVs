#!/usr/bin/env python3
"""Wrapper para la aplicación ARMind existente"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Intentar importar la nueva arquitectura
    from app_factory import create_app
    
    def main():
        """Función principal usando la nueva arquitectura"""
        app = create_app('development')
        
        # Configuración para desarrollo
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        )
    
except ImportError:
    # Fallback a la aplicación original
    print("Usando aplicación original...")
    
    try:
        import app as original_app
        
        def main():
            """Función principal usando la aplicación original"""
            if hasattr(original_app, 'app'):
                original_app.app.run(
                    host='0.0.0.0',
                    port=int(os.environ.get('PORT', 5000)),
                    debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
                )
            else:
                print("No se pudo encontrar la aplicación Flask")
                sys.exit(1)
    
    except ImportError as e:
        print(f"Error importando aplicación original: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
