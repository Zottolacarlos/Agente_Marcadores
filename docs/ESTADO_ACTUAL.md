# ESTADO ACTUAL - Agente_Marcadores / Bookmark Curator Agent

## 1. Propósito del proyecto

**Agente_Marcadores / Bookmark Curator Agent** es una aplicación local-first para ayudar a revisar, limpiar y priorizar marcadores/favoritos del navegador.

La idea central no es crear un simple gestor de favoritos, sino un **curador de pendientes digitales**: una herramienta que toma carpetas llenas de links guardados "para después" y las convierte en información accionable.

El producto debería ayudar a responder preguntas como:

- Qué links están rotos.
- Qué links están duplicados.
- Qué links siguen teniendo valor.
- Qué links conviene revisar primero.
- Qué links pueden archivarse o borrarse.
- Cómo transformar una carpeta de pendientes en una agenda de revisión.
- Cómo reducir la acumulación de favoritos sin depender solamente del criterio manual del usuario.

## 2. Estado actual del producto

El proyecto hoy funciona como un **MVP local determinístico**.

Esto significa que ya tiene una base funcional para leer, analizar y reportar bookmarks, pero todavía no debe presentarse como un agente IA completo. Actualmente la "inteligencia" principal viene de reglas locales, validación de links, detección de duplicados, scoring y generación de reportes.

La dirección correcta es conservar esta base como infraestructura y luego sumar IA opcional para interpretación semántica, clasificación, priorización y armado de agenda.

## 3. Qué ya funciona

Actualmente el proyecto tiene, o debería tener, estas capacidades principales:

- App Python con FastAPI.
- UI web con templates Jinja2.
- CLI para ejecutar análisis desde terminal.
- Lectura de bookmarks exportados desde navegador en formato HTML.
- Lectura local desde Chrome/Edge, si la función está disponible en el entorno.
- Parser robusto para archivos Netscape bookmarks HTML.
- Filtro por carpeta objetivo.
- Límite de cantidad de links a analizar.
- Opción para omitir validación online.
- Validación de URLs.
- Detección básica de links rotos o redireccionados.
- Detección de duplicados.
- Clasificación local por reglas.
- Scoring de prioridad.
- Generación de reportes Markdown y CSV.
- Cronograma básico de 7 días.
- Tests mínimos con pytest.
- README, ROADMAP y ejemplos iniciales para hacerlo presentable como portfolio.

## 4. Qué NO es todavía

El proyecto todavía no debería venderse como:

- SaaS.
- App multiusuario.
- Gestor completo de favoritos.
- Extensión de navegador.
- Agente IA autónomo.
- Herramienta que reorganiza automáticamente bookmarks reales.
- Sistema que entiende perfectamente el valor de cada link.

La forma honesta de describirlo hoy es:

> MVP local-first para analizar, priorizar y convertir carpetas de bookmarks en reportes accionables. La capa IA está planificada como evolución opcional.

## 5. Visión deseada

La visión final es más ambiciosa que el estado actual.

El usuario debería poder:

1. Ver el árbol de carpetas de sus favoritos.
2. Elegir visualmente una carpeta o subconjunto de links.
3. Pedirle al agente que evalúe esos links.
4. Recibir una agenda concreta de revisión.
5. Ver recomendaciones explicadas.
6. Decidir qué leer, archivar, borrar o reorganizar.
7. Mantener siempre control humano sobre cualquier acción destructiva.

La IA debería participar principalmente en:

- Entender la intención del bookmark.
- Detectar si es compra, lectura, curso, documentación, ocio, trabajo, referencia, etc.
- Clasificar semánticamente.
- Priorizar con criterio contextual.
- Explicar por qué algo vale o no vale la pena.
- Agrupar links similares.
- Sugerir una agenda semanal realista.
- Contestar consultas del usuario sobre sus pendientes.

## 6. Arquitectura conceptual actual

Flujo actual aproximado:

```text
Archivo bookmarks.html o fuente Chrome/Edge
        ↓
Parser de bookmarks
        ↓
Filtro por carpeta
        ↓
Validación de links / detección de duplicados
        ↓
Clasificación por reglas
        ↓
Scoring
        ↓
Reportes Markdown / CSV / cronograma
        ↓
UI web o CLI
```

Flujo deseado con IA opcional:

```text
Archivo bookmarks.html o fuente Chrome/Edge
        ↓
Parser de bookmarks
        ↓
Filtro por carpeta
        ↓
Validación técnica local
        ↓
Clasificación inicial por reglas
        ↓
IA opcional: intención, categoría, prioridad, razón, agenda
        ↓
Scoring final enriquecido
        ↓
Reportes y agenda accionable
```

## 7. Módulos importantes

Los nombres pueden variar levemente según el estado del repo, pero los módulos centrales esperados son:

```text
app/main.py
app/cli.py
app/config.py

app/routers/web_router.py
app/routers/api_router.py

app/models/bookmark.py
app/models/analysis.py

app/services/html_bookmark_parser.py
app/services/chromium_bookmark_reader.py
app/services/analyzer.py
app/services/rule_classifier.py
app/services/priority_scorer.py
app/services/link_validator.py
app/services/report_generator.py
app/services/scheduler.py

app/templates/base.html
app/templates/index.html
app/templates/summary.html
app/templates/report.html

tests/
examples/
docs/
```

## 8. Decisiones técnicas tomadas

### Local-first

El proyecto debe correr localmente. Los bookmarks pueden revelar intereses, hábitos, trabajo, compras, proyectos, problemas personales y estudios del usuario. Por eso el diseño debe privilegiar privacidad.

### IA opcional

La IA externa no debe estar activada por defecto. El usuario debe decidir cuándo enviar datos a un proveedor externo.

### No modificar bookmarks automáticamente

El sistema puede recomendar, pero no debe borrar ni mover bookmarks reales sin aprobación explícita.

### Reglas locales no se eliminan

Aunque se agregue IA, las reglas locales siguen teniendo valor para:

- Fallback sin API key.
- Análisis rápido y barato.
- Validación técnica.
- Duplicados.
- Estados de links.
- Tests reproducibles.

### No leer contenido completo de páginas todavía

En la primera integración IA, conviene enviar solo metadata mínima:

- título;
- URL;
- carpeta;
- estado técnico;
- categoría preliminar;
- score preliminar.

Leer contenido de páginas puede venir después.

## 9. Comandos útiles

Instalación:

```bash
poetry install --no-root
```

Tests:

```bash
poetry run pytest
```

Servidor web:

```bash
poetry run uvicorn app.main:app --reload
```

CLI con archivo exportado:

```bash
poetry run python -m app.cli analyze data/input/bookmarks.html --folder "Pendientes" --limit 20 --skip-validation
```

CLI con validación online:

```bash
poetry run python -m app.cli analyze data/input/bookmarks.html --folder "Pendientes" --limit 20
```

## 10. Limitaciones conocidas

- La clasificación por reglas puede equivocarse mucho.
- Algunas categorías pueden salir absurdas si una palabra clave aparece fuera de contexto.
- El scoring todavía es rígido.
- La agenda de 7 días todavía no entiende realmente la intención del usuario.
- La UI todavía debería mejorar para mostrar un árbol visual de carpetas.
- El usuario todavía debe escribir o seleccionar manualmente la carpeta objetivo.
- La IA aún no está integrada o no está integrada como capa principal.
- No hay persistencia histórica fuerte de análisis.
- No hay reorganización/exportación de bookmarks corregidos.
- No hay agrupación semántica avanzada.

## 11. Qué conviene conservar

Conviene conservar:

- Parser de bookmarks.
- Validación técnica de links.
- Detección de duplicados.
- Reportes.
- CLI.
- UI web básica.
- Tests.
- Enfoque local-first.
- Reglas como fallback.
- Roadmap incremental.

## 12. Qué conviene mejorar primero

Orden recomendado:

1. Confirmar repo limpio y tests pasando.
2. Agregar IA opcional desde CLI.
3. Mantener fallback determinístico.
4. Agregar salida estructurada JSON de IA.
5. Agregar tests para el contrato de IA sin llamar al proveedor real.
6. Conectar checkbox "Usar IA" en UI.
7. Mejorar agenda generada con datos IA.
8. Agregar vista árbol de carpetas.

## 13. Qué NO conviene tocar todavía

Por ahora no conviene invertir tiempo en:

- SaaS.
- Login.
- Multiusuario.
- Docker complejo.
- Deploy cloud.
- Extensión de navegador.
- Base de datos pesada.
- Reorganización automática destructiva.
- Scraping profundo de cada página.
- Agente conversacional complejo con memoria larga.

## 14. Definición de MVP presentable

El proyecto está presentable como MVP local si cumple:

- README claro.
- Instalación reproducible.
- Tests ejecutables.
- Ejemplo de bookmarks.
- Reporte de ejemplo.
- Screenshots o al menos instrucciones para generarlos.
- ROADMAP realista.
- Privacidad explicada.
- Limitaciones conocidas.
- Demo web funcionando.
- CLI funcionando.

## 15. Próximo gran bloque

El próximo bloque de valor debe ser:

```text
feature/ai-classification
```

Objetivo:

> Agregar una capa IA opcional que mejore categoría, intención, prioridad, acción recomendada y razón de cada bookmark analizado.

La implementación debe empezar por CLI para reducir complejidad, y recién después pasar a UI.
