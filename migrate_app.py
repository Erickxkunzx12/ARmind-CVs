#!/usr/bin/env python3
"""Script de Migración para ARMind - Actualización sin interrupciones"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import json
import importlib.util

class ARMindMigrator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Registrar mensaje en el log de migración"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    def create_backup(self):
        """Crear backup completo del proyecto actual"""
        self.log("Creando backup del proyecto actual...")
        
        try:
            self.backup_dir.mkdir(exist_ok=True)
            
            # Archivos críticos a respaldar
            critical_files = [
                'app.py',
                'requirements.txt',
                'config.py',
                '.env',
                'uploads/',
                'static/',
                'templates/',
                'database.db'
            ]
            
            for item in critical_files:
                source = self.project_root / item
                if source.exists():
                    if source.is_file():
                        shutil.copy2(source, self.backup_dir / item)
                    else:
                        shutil.copytree(source, self.backup_dir / item, dirs_exist_ok=True)
                    self.log(f"Respaldado: {item}")
            
            self.log(f"Backup creado en: {self.backup_dir}")
            return True
            
        except Exception as e:
            self.log(f"Error creando backup: {e}", "ERROR")
            return False
    
    def check_current_app(self):
        """Verificar la aplicación actual"""
        self.log("Verificando aplicación actual...")
        
        checks = {
            'app.py': 'Archivo principal de la aplicación',
            'requirements.txt': 'Dependencias del proyecto',
            'uploads/': 'Directorio de archivos subidos',
            'static/': 'Archivos estáticos',
            'templates/': 'Plantillas HTML'
        }
        
        missing_items = []
        for item, description in checks.items():
            if not (self.project_root / item).exists():
                missing_items.append((item, description))
                self.log(f"Faltante: {item} - {description}", "WARNING")
            else:
                self.log(f"Encontrado: {item}")
        
        if missing_items:
            self.log("Algunos archivos están faltantes, pero continuaremos", "WARNING")
        
        return True
    
    def install_enhanced_dependencies(self):
        """Instalar dependencias mejoradas"""
        self.log("Instalando dependencias mejoradas...")
        
        try:
            # Verificar si existe requirements_enhanced.txt
            enhanced_req = self.project_root / 'requirements_enhanced.txt'
            if enhanced_req.exists():
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_enhanced.txt'], 
                             check=True, capture_output=True)
                self.log("Dependencias mejoradas instaladas")
            else:
                self.log("requirements_enhanced.txt no encontrado, usando requirements.txt original")
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                             check=True, capture_output=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Error instalando dependencias: {e}", "ERROR")
            return False
    
    def create_app_wrapper(self):
        """Crear wrapper para la aplicación existente"""
        self.log("Creando wrapper para la aplicación...")
        
        wrapper_content = '''#!/usr/bin/env python3
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
'''
        
        try:
            with open('run_app.py', 'w', encoding='utf-8') as f:
                f.write(wrapper_content)
            
            self.log("Wrapper de aplicación creado: run_app.py")
            return True
            
        except Exception as e:
            self.log(f"Error creando wrapper: {e}", "ERROR")
            return False
    
    def update_configuration(self):
        """Actualizar configuración sin afectar la existente"""
        self.log("Actualizando configuración...")
        
        try:
            # Verificar si existe .env
            env_file = self.project_root / '.env'
            if not env_file.exists():
                # Crear .env básico basado en configuración existente
                env_content = '''# Configuración ARMind - Generada automáticamente
FLASK_ENV=development
FLASK_DEBUG=True

# Base de datos (ajustar según tu configuración)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=armind_db
DB_USER=postgres
DB_PASSWORD=password

# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# APIs (agregar tus claves)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here

# Email (configurar según tus necesidades)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_password_here

# Configuración de archivos
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216

# Configuración de cache
CACHE_ENABLED=false
MONITORING_ENABLED=false
'''
                
                with open('.env', 'w', encoding='utf-8') as f:
                    f.write(env_content)
                
                self.log("Archivo .env creado con configuración básica")
            else:
                self.log("Archivo .env existente preservado")
            
            return True
            
        except Exception as e:
            self.log(f"Error actualizando configuración: {e}", "ERROR")
            return False
    
    def create_migration_script(self):
        """Crear script para migración gradual"""
        self.log("Creando script de migración gradual...")
        
        migration_script = '''#!/usr/bin/env python3
"""Script de migración gradual para ARMind"""

import os
import sys
from pathlib import Path

def enable_feature(feature_name):
    """Habilitar una característica específica"""
    features = {
        'cache': 'CACHE_ENABLED=true',
        'monitoring': 'MONITORING_ENABLED=true',
        'logging': 'STRUCTURED_LOGGING=true',
        'security': 'ENHANCED_SECURITY=true'
    }
    
    if feature_name not in features:
        print(f"Característica '{feature_name}' no reconocida")
        print(f"Características disponibles: {list(features.keys())}")
        return False
    
    # Leer .env actual
    env_file = Path('.env')
    if not env_file.exists():
        print("Archivo .env no encontrado")
        return False
    
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Actualizar o agregar la configuración
    feature_config = features[feature_name]
    feature_key = feature_config.split('=')[0]
    
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(feature_key):
            lines[i] = feature_config + '\n'
            updated = True
            break
    
    if not updated:
        lines.append(feature_config + '\n')
    
    # Escribir archivo actualizado
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Característica '{feature_name}' habilitada")
    print("Reinicia la aplicación para aplicar los cambios")
    return True

def disable_feature(feature_name):
    """Deshabilitar una característica específica"""
    features = {
        'cache': 'CACHE_ENABLED=false',
        'monitoring': 'MONITORING_ENABLED=false',
        'logging': 'STRUCTURED_LOGGING=false',
        'security': 'ENHANCED_SECURITY=false'
    }
    
    if feature_name not in features:
        print(f"Característica '{feature_name}' no reconocida")
        return False
    
    # Similar lógica pero con false
    env_file = Path('.env')
    if not env_file.exists():
        print("Archivo .env no encontrado")
        return False
    
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    feature_config = features[feature_name]
    feature_key = feature_config.split('=')[0]
    
    for i, line in enumerate(lines):
        if line.startswith(feature_key):
            lines[i] = feature_config + '\n'
            break
    
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Característica '{feature_name}' deshabilitada")
    return True

def show_status():
    """Mostrar estado actual de las características"""
    env_file = Path('.env')
    if not env_file.exists():
        print("Archivo .env no encontrado")
        return
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    features = {
        'Cache': 'CACHE_ENABLED',
        'Monitoreo': 'MONITORING_ENABLED',
        'Logging Estructurado': 'STRUCTURED_LOGGING',
        'Seguridad Mejorada': 'ENHANCED_SECURITY'
    }
    
    print("Estado actual de características:")
    print("-" * 40)
    
    for name, key in features.items():
        if f"{key}=true" in content:
            status = "✅ Habilitado"
        elif f"{key}=false" in content:
            status = "❌ Deshabilitado"
        else:
            status = "❓ No configurado"
        
        print(f"{name:<20}: {status}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python gradual_migration.py <comando> [característica]")
        print("Comandos:")
        print("  enable <feature>   - Habilitar característica")
        print("  disable <feature>  - Deshabilitar característica")
        print("  status            - Mostrar estado actual")
        print("")
        print("Características: cache, monitoring, logging, security")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        show_status()
    elif command == "enable" and len(sys.argv) > 2:
        enable_feature(sys.argv[2])
    elif command == "disable" and len(sys.argv) > 2:
        disable_feature(sys.argv[2])
    else:
        print("Comando no reconocido")

if __name__ == '__main__':
    main()
'''
        
        try:
            with open('gradual_migration.py', 'w', encoding='utf-8') as f:
                f.write(migration_script)
            
            self.log("Script de migración gradual creado")
            return True
            
        except Exception as e:
            self.log(f"Error creando script de migración: {e}", "ERROR")
            return False
    
    def create_compatibility_layer(self):
        """Crear capa de compatibilidad"""
        self.log("Creando capa de compatibilidad...")
        
        compat_content = '''"""Capa de compatibilidad para ARMind"""

import os
import sys
from functools import wraps

def safe_import(module_name, fallback=None):
    """Importar módulo de forma segura con fallback"""
    try:
        return __import__(module_name)
    except ImportError:
        if fallback:
            return fallback
        return None

def feature_flag(feature_name, default=False):
    """Decorator para características opcionales"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            enabled = os.environ.get(f"{feature_name.upper()}_ENABLED", str(default)).lower() == 'true'
            if enabled:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error en característica {feature_name}: {e}")
                    return None
            return None
        return wrapper
    return decorator

def graceful_fallback(fallback_func):
    """Decorator para fallback graceful"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Fallback activado para {func.__name__}: {e}")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator

class CompatibilityManager:
    """Gestor de compatibilidad"""
    
    def __init__(self):
        self.features = {}
        self.fallbacks = {}
    
    def register_feature(self, name, implementation, fallback=None):
        """Registrar una característica con fallback"""
        self.features[name] = implementation
        if fallback:
            self.fallbacks[name] = fallback
    
    def get_feature(self, name):
        """Obtener implementación de característica"""
        if name in self.features:
            enabled = os.environ.get(f"{name.upper()}_ENABLED", 'false').lower() == 'true'
            if enabled:
                return self.features[name]
        
        return self.fallbacks.get(name, lambda *args, **kwargs: None)

# Instancia global
compat_manager = CompatibilityManager()
'''
        
        try:
            with open('compatibility.py', 'w', encoding='utf-8') as f:
                f.write(compat_content)
            
            self.log("Capa de compatibilidad creada")
            return True
            
        except Exception as e:
            self.log(f"Error creando capa de compatibilidad: {e}", "ERROR")
            return False
    
    def save_migration_log(self):
        """Guardar log de migración"""
        log_file = self.project_root / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.migration_log))
            
            self.log(f"Log de migración guardado en: {log_file}")
            return True
            
        except Exception as e:
            self.log(f"Error guardando log: {e}", "ERROR")
            return False
    
    def run_migration(self):
        """Ejecutar migración completa"""
        self.log("=" * 50)
        self.log("INICIANDO MIGRACIÓN DE ARMIND")
        self.log("=" * 50)
        
        steps = [
            ("Verificar aplicación actual", self.check_current_app),
            ("Crear backup", self.create_backup),
            ("Instalar dependencias mejoradas", self.install_enhanced_dependencies),
            ("Crear wrapper de aplicación", self.create_app_wrapper),
            ("Actualizar configuración", self.update_configuration),
            ("Crear script de migración gradual", self.create_migration_script),
            ("Crear capa de compatibilidad", self.create_compatibility_layer),
            ("Guardar log de migración", self.save_migration_log)
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            self.log(f"\n📋 Ejecutando: {step_name}")
            if step_func():
                success_count += 1
                self.log(f"✅ {step_name} completado")
            else:
                self.log(f"❌ {step_name} falló", "ERROR")
        
        self.log("\n" + "=" * 50)
        self.log(f"MIGRACIÓN COMPLETADA: {success_count}/{len(steps)} pasos exitosos")
        self.log("=" * 50)
        
        if success_count == len(steps):
            self.log("\n🎉 ¡Migración exitosa!")
            self.log("\n📋 Próximos pasos:")
            self.log("1. Ejecutar: python run_app.py")
            self.log("2. Verificar que la aplicación funciona correctamente")
            self.log("3. Usar 'python gradual_migration.py status' para ver características")
            self.log("4. Habilitar características gradualmente con 'python gradual_migration.py enable <feature>'")
        else:
            self.log("\n⚠️ Migración parcial completada")
            self.log("Revisa los errores y ejecuta nuevamente si es necesario")
            self.log(f"Backup disponible en: {self.backup_dir}")
        
        return success_count == len(steps)

def main():
    """Función principal"""
    migrator = ARMindMigrator()
    migrator.run_migration()

if __name__ == '__main__':
    main()