# Guía de Contribución - CV Analyzer Pro

¡Gracias por tu interés en contribuir a CV Analyzer Pro! 🎉

## 🚀 Cómo Contribuir

### 1. Fork del Repositorio
```bash
# Fork en GitHub y luego clona tu fork
git clone https://github.com/tu-usuario/cv-analyzer-pro.git
cd cv-analyzer-pro
```

### 2. Configurar Entorno de Desarrollo
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de desarrollo
```

### 3. Crear Rama para tu Feature
```bash
git checkout -b feature/nombre-descriptivo
# o
git checkout -b bugfix/descripcion-del-bug
```

### 4. Realizar Cambios
- Sigue las convenciones de código existentes
- Agrega comentarios donde sea necesario
- Actualiza documentación si es relevante

### 5. Probar tus Cambios
```bash
# Ejecutar la aplicación
python app.py

# Probar funcionalidades afectadas
# Verificar que no se rompan funcionalidades existentes
```

### 6. Commit y Push
```bash
git add .
git commit -m "feat: descripción clara del cambio"
git push origin feature/nombre-descriptivo
```

### 7. Crear Pull Request
- Ve a GitHub y crea un Pull Request
- Describe claramente qué cambios realizaste
- Menciona si resuelve algún issue existente

## 📝 Convenciones de Código

### Python
- Seguir PEP 8
- Usar nombres descriptivos para variables y funciones
- Agregar docstrings a funciones importantes
- Máximo 100 caracteres por línea

### Commits
Usar formato convencional:
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` cambios en documentación
- `style:` cambios de formato
- `refactor:` refactorización de código
- `test:` agregar o modificar tests

### Estructura de Archivos
- Mantener organización existente
- Nuevas APIs en `apis_job/`
- Templates en `templates/`
- Archivos estáticos en `static/`

## 🐛 Reportar Bugs

### Antes de Reportar
1. Busca en issues existentes
2. Verifica que sea reproducible
3. Prueba con la última versión

### Información a Incluir
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Screenshots si es relevante
- Información del sistema (OS, Python version, etc.)

## 💡 Sugerir Funcionalidades

### Ideas Bienvenidas
- Nuevos portales de empleo
- Mejoras en análisis de IA
- Optimizaciones de rendimiento
- Mejoras en UI/UX
- Nuevas integraciones

### Formato de Sugerencia
- Descripción clara de la funcionalidad
- Casos de uso
- Beneficios esperados
- Posible implementación (opcional)

## 🔧 Áreas que Necesitan Ayuda

### Prioridad Alta
- [ ] Tests automatizados
- [ ] Optimización de web scraping
- [ ] Mejoras en seguridad
- [ ] Documentación de APIs

### Prioridad Media
- [ ] Nuevos portales de empleo
- [ ] Mejoras en UI
- [ ] Optimización de base de datos
- [ ] Internacionalización

### Prioridad Baja
- [ ] Temas personalizables
- [ ] Integraciones adicionales
- [ ] Funcionalidades avanzadas

## 📚 Recursos Útiles

- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [OpenAI API Docs](https://platform.openai.com/docs/)
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## 🤝 Código de Conducta

- Sé respetuoso con otros contribuidores
- Acepta críticas constructivas
- Enfócate en lo que es mejor para la comunidad
- Ayuda a otros cuando sea posible

## 📞 Contacto

Si tienes preguntas sobre contribuciones:
- Abre un issue en GitHub
- Contacta a los mantenedores
- Únete a las discusiones

---

¡Gracias por hacer CV Analyzer Pro mejor para todos! 🚀