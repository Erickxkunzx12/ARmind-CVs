# Configuración de APIs para Análisis de CV

Este documento explica cómo configurar las APIs de OpenAI, Anthropic y Google Gemini para el sistema de análisis de CV.

## APIs Disponibles

### 1. OpenAI (Ya configurado)
- **Modelo**: GPT-4
- **Estado**: ✅ Configurado y funcionando
- **Variable de entorno**: `OPENAI_API_KEY`

### 2. Anthropic Claude (Requiere configuración)
- **Modelo**: Claude 3 Sonnet
- **Estado**: ⚠️ Requiere API Key
- **Variable de entorno**: `ANTHROPIC_API_KEY`

### 3. Google Gemini (Requiere configuración)
- **Modelo**: Gemini 1.5 Pro
- **Estado**: ⚠️ Requiere API Key
- **Variable de entorno**: `GEMINI_API_KEY`

## Configuración de Anthropic Claude

### Paso 1: Obtener API Key
1. Ve a [Anthropic Console](https://console.anthropic.com/)
2. Crea una cuenta o inicia sesión
3. Ve a la sección "API Keys"
4. Crea una nueva API Key
5. Copia la clave generada

### Paso 2: Configurar en el proyecto
1. Abre el archivo `.env` en la raíz del proyecto
2. Reemplaza `your_anthropic_api_key_here` con tu API Key real:
   ```
   ANTHROPIC_API_KEY=tu_clave_real_aqui
   ```

### Paso 3: Verificar configuración
- La librería `anthropic==0.7.8` ya está instalada
- El código de integración ya está implementado en `app.py`

## Configuración de Google Gemini

### Paso 1: Obtener API Key
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Crea una nueva API Key
4. Copia la clave generada

### Paso 2: Configurar en el proyecto
1. Abre el archivo `.env` en la raíz del proyecto
2. Reemplaza `your_gemini_api_key_here` con tu API Key real:
   ```
   GEMINI_API_KEY=tu_clave_real_aqui
   ```

### Paso 3: Verificar configuración
- La librería `google-generativeai==0.3.2` ya está instalada
- El código de integración ya está implementado en `app.py`

## Tipos de Análisis Disponibles

Cada API puede realizar los siguientes tipos de análisis:

1. **Revisión general del estado del currículum** (`general_health_check`)
2. **Análisis de calidad del contenido** (`content_quality_analysis`)
3. **Adaptación de puestos de trabajo y optimización de palabras clave** (`job_tailoring_optimization`)
4. **Verificación de compatibilidad de ATS** (`ats_compatibility_verification`)
5. **Evaluación de tonos y estilos** (`tone_style_evaluation`)
6. **Retroalimentación específica de la industria y del rol** (`industry_role_feedback`)
7. **Benchmarking y Comparación** (`benchmarking_comparison`)
8. **Sugerencias de mejora basadas en IA** (`ai_improvement_suggestions`)
9. **Evaluación de diseño visual y maquetación** (`visual_design_assessment`)
10. **Puntuación completa del currículum** (`comprehensive_score`) - Recomendado

## Flujo de Uso

1. **Subir CV**: El usuario sube su archivo de currículum
2. **Seleccionar IA**: Elegir entre OpenAI, Anthropic o Gemini
3. **Seleccionar Análisis**: Elegir el tipo de análisis deseado
4. **Obtener Resultados**: Recibir el análisis detallado

## Solución de Problemas

### Error: "API Key no configurada"
- Verifica que hayas configurado correctamente la variable de entorno en `.env`
- Asegúrate de que no haya espacios extra en la clave
- Reinicia el servidor Flask después de cambiar el `.env`

### Error: "Librería no instalada"
- Ejecuta: `pip install -r requirements.txt`
- Verifica que las librerías `anthropic` y `google-generativeai` estén instaladas

### Error: "Cuota excedida" o "Rate limit"
- Verifica los límites de tu plan de API
- Considera usar una API diferente temporalmente

## Costos Estimados

### OpenAI GPT-4
- ~$0.03 por análisis (dependiendo del tamaño del CV)

### Anthropic Claude
- ~$0.02 por análisis (dependiendo del tamaño del CV)

### Google Gemini
- Gratis hasta cierto límite, luego ~$0.01 por análisis

## Seguridad

⚠️ **IMPORTANTE**: 
- Nunca compartas tus API Keys
- No subas el archivo `.env` a repositorios públicos
- Rota tus claves regularmente
- Monitorea el uso de tus APIs

## Soporte

Si tienes problemas con la configuración:
1. Verifica que todas las dependencias estén instaladas
2. Revisa los logs del servidor para errores específicos
3. Asegúrate de que las API Keys sean válidas y tengan permisos