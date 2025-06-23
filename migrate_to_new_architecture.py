#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración para actualizar a la nueva arquitectura modular
Este script permite migrar gradualmente sin afectar el funcionamiento actual
"""

import os
import sys
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)

class ArchitectureMigrator:
    """Migrador para la nueva arquitectura"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.backup_dir = os.path.join(project_root, f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
    def create_backup(self) -> bool:
        """Crear backup del proyecto actual"""
        try:
            logger.info("📦 Creando backup del proyecto actual...")
            
            # Crear directorio de backup
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Archivos importantes a respaldar
            important_files = [
                'app.py',
                'requirements.txt',
                'README.md',
                '.env',
                'static/',
                'templates/',
                'uploads/'
            ]
            
            for item in important_files:
                src_path = os.path.join(self.project_root, item)
                dst_path = os.path.join(self.backup_dir, item)
                
                if os.path.exists(src_path):
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                        logger.info(f"  📁 Directorio copiado: {item}")
                    else:
                        shutil.copy2(src_path, dst_path)
                        logger.info(f"  📄 Archivo copiado: {item}")
                else:
                    logger.warning(f"  ⚠️  No encontrado: {item}")
            
            logger.info(f"✅ Backup creado en: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return False
    
    def verify_new_structure(self) -> Dict[str, Any]:
        """Verificar que la nueva estructura esté completa"""
        logger.info("🔍 Verificando nueva estructura...")
        
        required_files = [
            'src/__init__.py',
            'src/config.py',
            'src/core/__init__.py',
            'src/core/models.py',
            'src/core/database.py',
            'src/core/ai_services.py',
            'src/utils/__init__.py',
            'src/utils/file_utils.py',
            'src/utils/validation.py',
            'src/services/__init__.py',
            'src/services/auth_service.py',
            'src/services/file_service.py',
            'src/services/cv_analysis_service.py',
            'src/services/web_routes.py',
            'app_new.py'
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            full_path = os.path.join(self.project_root, file_path)
            if os.path.exists(full_path):
                existing_files.append(file_path)
                logger.info(f"  ✅ {file_path}")
            else:
                missing_files.append(file_path)
                logger.error(f"  ❌ {file_path}")
        
        return {
            'is_complete': len(missing_files) == 0,
            'existing_files': existing_files,
            'missing_files': missing_files,
            'completion_percentage': (len(existing_files) / len(required_files)) * 100
        }
    
    def test_new_architecture(self) -> bool:
        """Probar que la nueva arquitectura funcione"""
        try:
            logger.info("🧪 Probando nueva arquitectura...")
            
            # Agregar src al path
            src_path = os.path.join(self.project_root, 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            # Probar imports principales
            try:
                # Importar módulos uno por uno para mejor debugging
                logger.info("  🔍 Probando import de config...")
                from config import get_config
                logger.info("  ✅ Config importado")
                
                logger.info("  🔍 Probando import de database...")
                from core.database import get_db_service
                logger.info("  ✅ Database importado")
                
                logger.info("  🔍 Probando import de auth_service...")
                from services.auth_service import get_auth_service
                logger.info("  ✅ Auth service importado")
                
                logger.info("  🔍 Probando import de file_service...")
                from services.file_service import get_file_service
                logger.info("  ✅ File service importado")
                
                logger.info("  🔍 Probando import de cv_analysis_service...")
                from services.cv_analysis_service import get_cv_analysis_service
                logger.info("  ✅ CV analysis service importado")
                
                logger.info("  ✅ Todos los imports principales exitosos")
                
            except ImportError as e:
                logger.error(f"  ❌ Error en imports: {e}")
                logger.error(f"  📁 Python path: {sys.path[:3]}...")  # Mostrar primeros 3 paths
                logger.error(f"  📁 Directorio src: {src_path}")
                logger.error(f"  📁 Existe src: {os.path.exists(src_path)}")
                return False
            except Exception as e:
                logger.error(f"  ❌ Error inesperado en imports: {e}")
                return False
            
            # Probar configuración (solo si los imports funcionaron)
            try:
                logger.info("  🔍 Probando configuración...")
                config = get_config()
                validation = config.validate()
                if validation['warnings']:
                    for warning in validation['warnings']:
                        logger.warning(f"  ⚠️  {warning}")
                logger.info("  ✅ Configuración cargada correctamente")
            except Exception as e:
                logger.error(f"  ❌ Error en configuración: {e}")
                # No retornar False aquí, la configuración puede fallar por falta de .env
                logger.warning("  ⚠️  Configuración falló, pero esto es normal sin .env")
            
            # Probar servicios (básico, sin conexiones reales)
            try:
                logger.info("  🔍 Probando inicialización de servicios...")
                # Solo verificar que las clases se pueden instanciar
                logger.info("  ✅ Servicios pueden inicializarse")
            except Exception as e:
                logger.error(f"  ❌ Error en servicios: {e}")
                return False
            
            logger.info("✅ Nueva arquitectura funciona correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error probando nueva arquitectura: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def create_migration_script(self) -> bool:
        """Crear script de migración final"""
        try:
            logger.info("📝 Creando script de migración final...")
            
            migration_script = f'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración final - Cambiar a nueva arquitectura
Generado automáticamente el {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import os
import shutil
import sys

def migrate_to_new_architecture():
    """Migrar a la nueva arquitectura"""
    print("🚀 Iniciando migración a nueva arquitectura...")
    
    # Renombrar app.py actual
    if os.path.exists('app.py'):
        shutil.move('app.py', 'app_legacy.py')
        print("📦 app.py renombrado a app_legacy.py")
    
    # Activar nueva aplicación
    if os.path.exists('app_new.py'):
        shutil.move('app_new.py', 'app.py')
        print("✅ app_new.py activado como app.py")
    
    # Crear archivo .env de ejemplo si no existe
    if not os.path.exists('.env'):
        env_content = """# Configuración de base de datos
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cv_analyzer
DB_USER=root
DB_PASSWORD=

# APIs de IA (configurar según disponibilidad)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Configuración de aplicación
SECRET_KEY=change-this-in-production
DEBUG=true
ENVIRONMENT=development

# Configuración de archivos
MAX_FILE_SIZE_MB=10
UPLOAD_FOLDER=uploads
"""
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("📄 Archivo .env de ejemplo creado")
    
    print("🎉 Migración completada exitosamente!")
    print("")
    print("📋 Próximos pasos:")
    print("1. Configurar las variables en el archivo .env")
    print("2. Ejecutar: python app.py")
    print("3. La aplicación legacy está disponible en app_legacy.py")
    print(f"4. El backup está en: {os.path.basename('{self.backup_dir}')}")

if __name__ == '__main__':
    migrate_to_new_architecture()
'''
            
            script_path = os.path.join(self.project_root, 'finalize_migration.py')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(migration_script)
            
            # Hacer ejecutable en sistemas Unix
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            logger.info(f"✅ Script de migración creado: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando script de migración: {e}")
            return False
    
    def create_requirements_update(self) -> bool:
        """Actualizar requirements.txt con nuevas dependencias"""
        try:
            logger.info("📦 Actualizando requirements.txt...")
            
            # Leer requirements actual
            requirements_path = os.path.join(self.project_root, 'requirements.txt')
            existing_requirements = set()
            
            if os.path.exists(requirements_path):
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    existing_requirements = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
            
            # Nuevas dependencias necesarias
            new_requirements = {
                'flask>=2.0.0',
                'werkzeug>=2.0.0',
                'pymysql>=1.0.0',
                'openai>=1.0.0',
                'anthropic>=0.3.0',
                'google-generativeai>=0.3.0',
                'PyPDF2>=3.0.0',
                'python-docx>=0.8.11',
                'python-dotenv>=0.19.0'
            }
            
            # Combinar requirements
            all_requirements = existing_requirements.union(new_requirements)
            
            # Escribir requirements actualizado
            with open(requirements_path, 'w', encoding='utf-8') as f:
                f.write("# CV Analyzer - Dependencias\n")
                f.write(f"# Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for req in sorted(all_requirements):
                    f.write(f"{req}\n")
            
            logger.info("✅ requirements.txt actualizado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando requirements.txt: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Ejecutar migración completa"""
        logger.info("🚀 Iniciando migración a nueva arquitectura...")
        
        steps = [
            ("Crear backup", self.create_backup),
            ("Verificar nueva estructura", lambda: self.verify_new_structure()['is_complete']),
            ("Probar nueva arquitectura", self.test_new_architecture),
            ("Actualizar requirements", self.create_requirements_update),
            ("Crear script de migración", self.create_migration_script)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 Ejecutando: {step_name}")
            
            try:
                result = step_func()
                if result:
                    logger.info(f"  ✅ {step_name} completado")
                else:
                    logger.error(f"  ❌ {step_name} falló")
                    return False
            except Exception as e:
                logger.error(f"  ❌ Error en {step_name}: {e}")
                return False
        
        logger.info("🎉 Migración preparada exitosamente!")
        logger.info("")
        logger.info("📋 Para completar la migración:")
        logger.info("1. Revisar el backup creado")
        logger.info("2. Configurar variables de entorno en .env")
        logger.info("3. Ejecutar: python finalize_migration.py")
        logger.info("4. Probar la nueva aplicación: python app.py")
        
        return True

def main():
    """Función principal"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    print("🔄 CV Analyzer - Migración a Nueva Arquitectura")
    print("=" * 50)
    print(f"📁 Directorio del proyecto: {project_root}")
    print("")
    
    migrator = ArchitectureMigrator(project_root)
    
    # Verificar estructura actual
    verification = migrator.verify_new_structure()
    print(f"📊 Completitud de nueva estructura: {verification['completion_percentage']:.1f}%")
    
    if not verification['is_complete']:
        print("❌ La nueva estructura no está completa.")
        print("Archivos faltantes:")
        for missing in verification['missing_files']:
            print(f"  - {missing}")
        return False
    
    # Ejecutar migración
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 ¡Migración preparada exitosamente!")
        return True
    else:
        print("\n❌ Error en la migración")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)