# Servicio de rutas web - Centralización de endpoints Flask
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from services.auth_service import get_auth_service
from services.file_service import get_file_service
from services.cv_analysis_service import get_cv_analysis_service
from core.models import AnalysisTypes, AIProviders
from utils.validation import validate_analysis_type, validate_ai_provider
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def require_login(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class WebRoutes:
    """Servicio centralizado para rutas web"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.auth_service = get_auth_service()
        self.file_service = get_file_service()
        self.analysis_service = get_cv_analysis_service()
        self._register_routes()
    
    def _register_routes(self):
        """Registrar todas las rutas"""
        # Rutas de autenticación
        self.app.route('/', methods=['GET'])(self.index)
        self.app.route('/login', methods=['GET', 'POST'])(self.login)
        self.app.route('/register', methods=['GET', 'POST'])(self.register)
        self.app.route('/logout', methods=['POST'])(self.logout)
        
        # Rutas principales
        self.app.route('/dashboard', methods=['GET'])(self.dashboard)
        self.app.route('/upload', methods=['GET', 'POST'])(self.upload_cv)
        self.app.route('/analyze', methods=['POST'])(self.analyze_cv)
        self.app.route('/results/<int:analysis_id>', methods=['GET'])(self.view_results)
        
        # Rutas de gestión de archivos
        self.app.route('/files', methods=['GET'])(self.list_files)
        self.app.route('/files/<int:file_id>', methods=['GET'])(self.view_file)
        self.app.route('/files/<int:file_id>/delete', methods=['POST'])(self.delete_file)
        
        # Rutas de perfil
        self.app.route('/profile', methods=['GET', 'POST'])(self.profile)
        self.app.route('/change-password', methods=['POST'])(self.change_password)
        
        # API endpoints
        self.app.route('/api/validate-file', methods=['POST'])(self.api_validate_file)
        self.app.route('/api/analysis-status/<int:analysis_id>', methods=['GET'])(self.api_analysis_status)
        self.app.route('/api/user-stats', methods=['GET'])(self.api_user_stats)
        
        # Rutas de información
        self.app.route('/about', methods=['GET'])(self.about)
        self.app.route('/help', methods=['GET'])(self.help_page)
    

    
    # Rutas de autenticación
    def index(self):
        """Página principal"""
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    def login(self):
        """Login de usuario"""
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email y contraseña son requeridos', 'error')
                return render_template('login.html')
            
            success, result = self.auth_service.authenticate_user(email, password)
            
            if success:
                session['user_id'] = result['user_id']
                session['user_email'] = result['email']
                session['user_name'] = result['name']
                flash(f'Bienvenido, {result["name"] or result["email"]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(result['error'], 'error')
        
        return render_template('login.html')
    
    def register(self):
        """Registro de usuario"""
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            name = request.form.get('name', '').strip()
            
            # Validaciones básicas
            if not email or not password:
                flash('Email y contraseña son requeridos', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('register.html')
            
            success, result = self.auth_service.register_user(email, password, name)
            
            if success:
                flash('Registro exitoso. Puedes iniciar sesión ahora.', 'success')
                return redirect(url_for('login'))
            else:
                flash(result['error'], 'error')
        
        return render_template('register.html')
    
    def logout(self):
        """Cerrar sesión"""
        session.clear()
        flash('Sesión cerrada exitosamente', 'info')
        return redirect(url_for('index'))
    
    # Rutas principales
    @require_login
    def dashboard(self):
        """Dashboard principal"""
        user_id = session['user_id']
        
        # Obtener archivos recientes
        files = self.file_service.get_user_files(user_id)[:5]  # Últimos 5
        
        # Obtener análisis recientes
        recent_analyses = self.analysis_service.get_user_analysis_history(user_id, limit=5)
        
        # Obtener estadísticas
        file_stats = self.file_service.get_file_statistics(user_id)
        user_stats = self.auth_service.get_user_statistics(user_id)
        
        return render_template('dashboard.html', 
                             files=files,
                             recent_analyses=recent_analyses,
                             file_stats=file_stats,
                             user_stats=user_stats,
                             analysis_types=AnalysisTypes.get_all(),
                             ai_providers=AIProviders.get_all())
    
    @require_login
    def upload_cv(self):
        """Subir CV"""
        if request.method == 'POST':
            if 'cv_file' not in request.files:
                flash('No se seleccionó archivo', 'error')
                return redirect(request.url)
            
            file = request.files['cv_file']
            if file.filename == '':
                flash('No se seleccionó archivo', 'error')
                return redirect(request.url)
            
            user_id = session['user_id']
            success, result = self.file_service.process_uploaded_file(file, user_id)
            
            if success:
                flash(f'Archivo "{result["filename"]}" subido exitosamente', 'success')
                if result.get('warnings'):
                    for warning in result['warnings']:
                        flash(warning, 'warning')
                return redirect(url_for('dashboard'))
            else:
                flash(result['error'], 'error')
        
        supported_formats = self.file_service.get_supported_formats()
        return render_template('upload.html', supported_formats=supported_formats)
    
    @require_login
    def analyze_cv(self):
        """Analizar CV"""
        user_id = session['user_id']
        
        # Obtener parámetros
        file_id = request.form.get('file_id', type=int)
        analysis_type = request.form.get('analysis_type', '')
        ai_provider = request.form.get('ai_provider', '')
        
        # Validaciones
        if not file_id:
            flash('Debe seleccionar un archivo', 'error')
            return redirect(url_for('dashboard'))
        
        if not validate_analysis_type(analysis_type):
            flash('Tipo de análisis inválido', 'error')
            return redirect(url_for('dashboard'))
        
        if not validate_ai_provider(ai_provider):
            flash('Proveedor de IA inválido', 'error')
            return redirect(url_for('dashboard'))
        
        # Obtener contenido del archivo
        cv_content = self.file_service.get_file_content(file_id, user_id)
        if not cv_content:
            flash('Archivo no encontrado', 'error')
            return redirect(url_for('dashboard'))
        
        # Realizar análisis
        success, result = self.analysis_service.analyze_cv(
            cv_content, analysis_type, ai_provider, user_id, file_id
        )
        
        if success:
            flash('Análisis completado exitosamente', 'success')
            return redirect(url_for('view_results', analysis_id=result['analysis_id']))
        else:
            flash(result['error'], 'error')
            return redirect(url_for('dashboard'))
    
    @require_login
    def view_results(self, analysis_id):
        """Ver resultados de análisis"""
        user_id = session['user_id']
        
        analysis_result = self.analysis_service.get_analysis_result(analysis_id, user_id)
        if not analysis_result:
            flash('Análisis no encontrado', 'error')
            return redirect(url_for('dashboard'))
        
        return render_template('results.html', analysis=analysis_result)
    
    # Rutas de gestión de archivos
    @require_login
    def list_files(self):
        """Listar archivos del usuario"""
        user_id = session['user_id']
        files = self.file_service.get_user_files(user_id)
        file_stats = self.file_service.get_file_statistics(user_id)
        
        return render_template('files.html', files=files, stats=file_stats)
    
    @require_login
    def view_file(self, file_id):
        """Ver contenido de archivo"""
        user_id = session['user_id']
        content = self.file_service.get_file_content(file_id, user_id)
        
        if not content:
            flash('Archivo no encontrado', 'error')
            return redirect(url_for('list_files'))
        
        # Obtener información del archivo
        files = self.file_service.get_user_files(user_id)
        file_info = next((f for f in files if f['id'] == file_id), None)
        
        return render_template('view_file.html', content=content, file_info=file_info)
    
    @require_login
    def delete_file(self, file_id):
        """Eliminar archivo"""
        user_id = session['user_id']
        
        success = self.file_service.delete_file(file_id, user_id)
        if success:
            flash('Archivo eliminado exitosamente', 'success')
        else:
            flash('Error eliminando archivo', 'error')
        
        return redirect(url_for('list_files'))
    
    # Rutas de perfil
    @require_login
    def profile(self):
        """Perfil de usuario"""
        user_id = session['user_id']
        
        if request.method == 'POST':
            updates = {
                'name': request.form.get('name', '').strip(),
                'email': request.form.get('email', '').strip()
            }
            
            success, result = self.auth_service.update_user_profile(user_id, updates)
            
            if success:
                # Actualizar sesión
                if 'email' in updates:
                    session['user_email'] = updates['email']
                if 'name' in updates:
                    session['user_name'] = updates['name']
                
                flash('Perfil actualizado exitosamente', 'success')
            else:
                flash(result['error'], 'error')
        
        user = self.auth_service.get_user_by_id(user_id)
        user_stats = self.auth_service.get_user_statistics(user_id)
        
        return render_template('profile.html', user=user, stats=user_stats)
    
    @require_login
    def change_password(self):
        """Cambiar contraseña"""
        user_id = session['user_id']
        
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden', 'error')
            return redirect(url_for('profile'))
        
        success, result = self.auth_service.change_password(user_id, current_password, new_password)
        
        if success:
            flash('Contraseña actualizada exitosamente', 'success')
        else:
            flash(result['error'], 'error')
        
        return redirect(url_for('profile'))
    
    # API endpoints
    @require_login
    def api_validate_file(self):
        """API para validar archivo antes de subir"""
        if 'file' not in request.files:
            return jsonify({'is_valid': False, 'errors': ['No se proporcionó archivo']})
        
        file = request.files['file']
        validation = self.file_service.validate_file_before_upload(file)
        
        return jsonify(validation)
    
    @require_login
    def api_analysis_status(self, analysis_id):
        """API para obtener estado de análisis"""
        user_id = session['user_id']
        analysis = self.analysis_service.get_analysis_result(analysis_id, user_id)
        
        if not analysis:
            return jsonify({'error': 'Análisis no encontrado'}), 404
        
        return jsonify({
            'id': analysis.id,
            'status': 'completed',
            'analysis_type': analysis.analysis_type,
            'ai_provider': analysis.ai_provider,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None
        })
    
    @require_login
    def api_user_stats(self):
        """API para obtener estadísticas del usuario"""
        user_id = session['user_id']
        
        file_stats = self.file_service.get_file_statistics(user_id)
        user_stats = self.auth_service.get_user_statistics(user_id)
        
        return jsonify({
            'files': file_stats,
            'user': user_stats
        })
    
    # Rutas de información
    def about(self):
        """Página acerca de"""
        return render_template('about.html')
    
    def help_page(self):
        """Página de ayuda"""
        supported_formats = self.file_service.get_supported_formats()
        analysis_types = AnalysisTypes.get_all()
        ai_providers = AIProviders.get_all()
        
        return render_template('help.html',
                             supported_formats=supported_formats,
                             analysis_types=analysis_types,
                             ai_providers=ai_providers)

def register_web_routes(app: Flask) -> WebRoutes:
    """Registrar rutas web en la aplicación Flask"""
    return WebRoutes(app)