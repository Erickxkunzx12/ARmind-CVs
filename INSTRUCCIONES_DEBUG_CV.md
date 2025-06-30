# 🔍 Instrucciones para Debug del Problema de CVs

## Problema Reportado
Algunos CVs se cargan exitosamente, pero en vez de pasar a la selección de IA, regresan al inicio con el error "Primero debes subir un CV".

## 🚀 Sistema de Debug Implementado

He agregado logging detallado en las siguientes funciones:

### 1. Función `analyze_cv` (Carga de CV)
- ✅ Información del archivo (nombre, tamaño, extensión)
- ✅ Resultado de extracción de texto (caracteres extraídos)
- ✅ Validaciones de contenido (longitud mínima, palabras clave)
- ✅ Estado de la sesión (guardado exitoso)
- ✅ Redirección a selección de IA

### 2. Función `select_ai_provider` (Selección de IA)
- ✅ Verificación de usuario en sesión
- ✅ Verificación de contenido CV en sesión
- ✅ Información detallada del CV (archivo, caracteres)
- ✅ Diagnóstico de problemas de sesión

## 📋 Pasos para Reproducir y Capturar Debug

### Paso 1: Acceder al Sistema
1. Abre tu navegador y ve a: **http://127.0.0.1:5000**
2. Inicia sesión con tu cuenta
3. Ve al analizador de CV

### Paso 2: Probar CVs Problemáticos
1. **Sube un CV que sabes que funciona correctamente**
   - Observa que pasa a la selección de IA sin problemas
   - Esto confirma que el sistema funciona normalmente

2. **Sube un CV que causa el problema**
   - Observa si regresa al inicio con el error
   - **IMPORTANTE**: Mantén abierta la consola del servidor Flask

### Paso 3: Capturar Logs de Debug

Cuando subas un CV problemático, verás en la consola del servidor información como:

```
[DEBUG CV] Archivo: ejemplo.pdf, Tamaño: 245760 bytes, Extensión: pdf
[DEBUG CV] ✅ Extracción exitosa: 1250 caracteres
[DEBUG CV] Vista previa: 'Juan Pérez\nIngeniero de Software...'
[DEBUG CV] ✅ Contenido parece ser CV (8 palabras clave)
[DEBUG CV] Guardando en sesión - Usuario: 123, Archivo: ejemplo.pdf
[DEBUG CV] ✅ Sesión actualizada correctamente
[DEBUG CV] Contenido en sesión: 1250 caracteres
[DEBUG CV] 🔄 Redirigiendo a select_ai_provider

[DEBUG AI_SELECT] Acceso a select_ai_provider - Usuario: usuario123 (ID: 123)
[DEBUG AI_SELECT] Verificando contenido de sesión...
[DEBUG AI_SELECT] Claves en sesión: ['user_id', 'username', 'cv_content', 'cv_filename']
[DEBUG AI_SELECT] ✅ CV encontrado en sesión
[DEBUG AI_SELECT] Archivo: ejemplo.pdf
[DEBUG AI_SELECT] Contenido: 1250 caracteres
```

### Paso 4: Identificar el Problema

Busca en los logs uno de estos patrones de error:

#### ❌ **Error de Extracción de Texto**
```
[DEBUG CV] ❌ ERROR: No se extrajo texto del archivo
[DEBUG CV] ❌ Error: No se pudo extraer texto del archivo
```

#### ❌ **Error de Sesión**
```
[DEBUG CV] ❌ ERROR CRÍTICO: No se guardó en sesión
[DEBUG AI_SELECT] ❌ ERROR CRÍTICO: cv_content no está en sesión
[DEBUG AI_SELECT] ❌ ERROR: cv_content está vacío
```

#### ⚠️ **Advertencias de Contenido**
```
[DEBUG CV] ⚠️ ADVERTENCIA: Texto muy corto (25 caracteres)
[DEBUG CV] ⚠️ ADVERTENCIA: Solo 1 palabras clave de CV encontradas
```

## 🔧 Script de Debug Adicional

También puedes usar el script `debug_session_cv_issue.py` para analizar archivos específicos:

```bash
python debug_session_cv_issue.py mi_cv_problematico.pdf
```

Este script te dirá exactamente qué está pasando con el archivo:
- ✅ Si se puede leer correctamente
- ✅ Si se extrae texto exitosamente
- ✅ Si el contenido parece ser un CV válido
- ❌ Qué problemas específicos tiene

## 📊 Posibles Causas Identificadas

### 1. **PDFs Escaneados**
- **Síntoma**: Extracción exitosa pero 0 caracteres
- **Solución**: Implementar OCR o rechazar PDFs sin texto

### 2. **Archivos Corruptos**
- **Síntoma**: Error durante la extracción
- **Solución**: Mejor validación de archivos

### 3. **Contenido Insuficiente**
- **Síntoma**: Menos de 50 caracteres extraídos
- **Solución**: Validación de contenido mínimo

### 4. **Problemas de Sesión**
- **Síntoma**: CV se guarda pero se pierde inmediatamente
- **Solución**: Investigar configuración de sesiones Flask

### 5. **Archivos No-CV**
- **Síntoma**: Archivo válido pero sin palabras clave de CV
- **Solución**: Validación de contenido relevante

## 📝 Información a Recopilar

Cuando encuentres un CV problemático, recopila:

1. **Información del archivo**:
   - Nombre del archivo
   - Tamaño en bytes
   - Tipo (PDF, DOC, DOCX)
   - Cómo fue creado (escaneado, generado digitalmente, etc.)

2. **Logs completos** de la consola del servidor

3. **Comportamiento específico**:
   - ¿Se muestra algún mensaje de error?
   - ¿Regresa inmediatamente o después de un tiempo?
   - ¿Pasa algo en la interfaz de usuario?

## 🎯 Próximos Pasos

Una vez que identifiquemos la causa específica, implementaremos:

1. **Validaciones mejoradas** para rechazar archivos problemáticos
2. **Mensajes de error específicos** para cada tipo de problema
3. **OCR opcional** para PDFs escaneados
4. **Validación de contenido** para asegurar que son CVs reales
5. **Logging permanente** para monitoreo continuo

---

**¡El sistema está listo para debug! Prueba subir CVs y observa los logs detallados en la consola del servidor.**