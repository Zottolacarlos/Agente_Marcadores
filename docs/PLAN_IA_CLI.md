# PLAN IA CLI - Agente_Marcadores / Bookmark Curator Agent

## 1. Objetivo de esta etapa

Agregar una primera capa de IA opcional al proyecto **Agente_Marcadores / Bookmark Curator Agent**, empezando por la CLI.

La meta no es construir todavía un agente autónomo complejo. La meta es que el análisis deje de depender únicamente de reglas rígidas y pueda interpretar mejor la intención de cada bookmark.

La feature debe permitir ejecutar algo como:

```bash
poetry run python -m app.cli analyze data/input/bookmarks.html --folder "Pendientes" --limit 20 --skip-validation --use-ai
```

Y obtener resultados más inteligentes para:

- categoría;
- subcategoría;
- intención;
- prioridad;
- acción recomendada;
- explicación breve;
- posible valor para el usuario;
- posible agenda de revisión.

## 2. Principios de diseño

### IA apagada por defecto

El sistema debe seguir funcionando sin IA.

```bash
poetry run python -m app.cli analyze data/input/bookmarks.html --folder "Pendientes"
```

Debe usar el flujo actual.

### IA activada explícitamente

La IA solo debe usarse si el usuario pasa:

```bash
--use-ai
```

Más adelante, en UI, se agregará un checkbox:

```text
[ ] Usar IA para mejorar clasificación y agenda
```

### Privacidad primero

Los bookmarks pueden contener información sensible. La IA externa debe ser opcional y explícita.

La primera versión IA no debe enviar contenido completo de páginas. Solo metadata mínima.

### Fallback obligatorio

Si no hay API key, si falla la llamada o si el proveedor devuelve JSON inválido, el sistema debe seguir funcionando con reglas locales.

### Límite recomendado

No usar IA sobre miles de links de golpe. En la primera versión, conviene limitar a 20 o 50 links.

## 3. Alcance de la primera versión

La primera versión debe hacer esto:

1. Tomar bookmarks ya parseados y filtrados.
2. Ejecutar análisis local existente.
3. Para cada bookmark elegido, enviar metadata mínima a IA.
4. Recibir una respuesta JSON estructurada.
5. Usar esa respuesta para enriquecer categoría, score, acción y razón.
6. Generar reportes usando el resultado enriquecido.

No debe hacer todavía:

- conversación libre;
- lectura completa de páginas;
- embeddings;
- RAG;
- memoria persistente;
- reordenamiento automático de bookmarks;
- escritura sobre archivos reales del navegador;
- integración con extensión.

## 4. Comando CLI esperado

Comando base sin IA:

```bash
poetry run python -m app.cli analyze data/input/bookmarks.html --folder "Pendientes" --limit 20 --skip-validation
```

Comando con IA:

```bash
poetry run python -m app.cli analyze data/input/bookmarks.html --folder "Pendientes" --limit 20 --skip-validation --use-ai
```

Variante con validación online:

```bash
poetry run python -m app.cli analyze data/input/bookmarks.html --folder "Pendientes" --limit 20 --use-ai
```

## 5. Variables de entorno

Agregar `.env.example` si no existe, o actualizarlo:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
AI_MAX_BOOKMARKS=30
AI_TIMEOUT_SECONDS=30
```

Notas:

- `OPENAI_API_KEY` debe quedar vacío en el ejemplo.
- `.env` real debe estar ignorado por Git.
- Si no hay API key, `--use-ai` no debe romper todo: debe mostrar aviso y usar fallback local.

## 6. Dependencias

Agregar cliente oficial si el proyecto usará OpenAI:

```bash
poetry add openai
```

Si se prefiere evitar dependencia al inicio, se puede usar `httpx`, pero el cliente oficial simplifica salida estructurada.

Recomendación actual:

```bash
poetry add openai
```

## 7. Archivos a tocar

Primera etapa CLI:

```text
app/config.py
app/cli.py
app/services/analyzer.py
app/services/ai_classifier.py
app/models/analysis.py
tests/
.env.example
README.md
```

Segunda etapa UI:

```text
app/routers/web_router.py
app/routers/api_router.py
app/templates/index.html
app/templates/summary.html
```

## 8. Modelo de respuesta IA

Crear un modelo Pydantic para representar la clasificación IA.

Ejemplo conceptual:

```python
from pydantic import BaseModel, Field

class AIBookmarkClassification(BaseModel):
    category: str
    subcategory: str | None = None
    intent: str
    priority: int = Field(ge=0, le=100)
    recommended_action: str
    reason: str
    confidence: float = Field(ge=0, le=1)
```

Categorías sugeridas:

```text
ia
python
aws
backend
frontend
devops
database
git
english
jobs
finanzas
gaming
compras
comics
deportes
noticias
entretenimiento
familia
salud
educacion
documentacion
curso
tutorial
referencia
desconocido
```

Acciones sugeridas:

```text
leer_hoy
ver_esta_semana
ver_luego
archivar
borrar_probable
revisar_manual
```

## 9. Input mínimo para IA

Por cada bookmark, enviar algo como:

```json
{
  "title": "COMPRA GAMER | Compra Gamer",
  "url": "https://compragamer.com",
  "folder_path": "Barra de marcadores/Games/Lista Deseados",
  "status": "OK",
  "rule_category": "ia",
  "rule_score": 70
}
```

No enviar todavía:

- HTML de la página.
- Texto completo de la página.
- Historial del navegador.
- Cookies.
- Datos personales innecesarios.

## 10. Output esperado de IA

Ejemplo:

```json
{
  "category": "compras",
  "subcategory": "hardware_gaming",
  "intent": "posible compra futura",
  "priority": 45,
  "recommended_action": "ver_luego",
  "reason": "Parece una tienda de hardware o gaming guardada como referencia de compra. Puede revisarse más adelante, no parece urgente.",
  "confidence": 0.86
}
```

## 11. Prompt base sugerido

El prompt debe ser breve, estricto y orientado a JSON.

Ejemplo:

```text
Sos un asistente que ayuda a ordenar bookmarks/favoritos guardados por un usuario.

Tu tarea es clasificar un bookmark y decidir qué tan importante parece revisarlo.

Respondé SOLO JSON válido con este esquema:
{
  "category": "...",
  "subcategory": "...",
  "intent": "...",
  "priority": 0-100,
  "recommended_action": "leer_hoy|ver_esta_semana|ver_luego|archivar|borrar_probable|revisar_manual",
  "reason": "...",
  "confidence": 0.0-1.0
}

Criterios:
- No sobreestimes la prioridad.
- Si parece compra futura, usá categoría "compras".
- Si parece juego, guía de juego o tienda de juegos, usá "gaming".
- Si parece documentación técnica, tutorial o curso, usá categoría técnica correspondiente.
- Si el link está roto, priorizá "revisar_manual" o "borrar_probable".
- La razón debe ser breve y útil.
- No inventes detalles que no estén en título, URL o carpeta.
```

## 12. Diseño de `ai_classifier.py`

Responsabilidades:

- Detectar si IA está disponible.
- Preparar payload.
- Llamar al proveedor.
- Validar JSON.
- Devolver clasificación estructurada.
- Manejar errores sin romper análisis.

Funciones sugeridas:

```python
def is_ai_available() -> bool:
    ...

def classify_bookmark_with_ai(bookmark, local_result) -> AIBookmarkClassification | None:
    ...

def classify_bookmarks_with_ai(results, max_items: int) -> list:
    ...
```

También puede convenir una clase:

```python
class AIBookmarkClassifier:
    def classify(self, bookmark, local_result):
        ...
```

Para la primera versión, una implementación funcional simple alcanza.

## 13. Cambios en `analyzer.py`

Agregar parámetros:

```python
def run_analysis(
    bookmarks,
    target_folder,
    *,
    limit=None,
    skip_validation=False,
    use_ai=False,
):
    ...
```

Flujo:

```text
1. Ejecutar análisis local.
2. Si use_ai=False, devolver resultado local.
3. Si use_ai=True:
   - verificar API key;
   - tomar máximo N resultados;
   - enriquecer cada resultado;
   - conservar fallback si falla.
4. Generar summary/reportes con datos finales.
```

## 14. Cambios en `cli.py`

Agregar opción:

```python
use_ai: bool = typer.Option(False, "--use-ai", help="Usar IA opcional para mejorar clasificación y prioridad.")
```

Ejemplo Typer conceptual:

```python
@app.command()
def analyze(
    file: Path,
    folder: str = typer.Option("Pendientes", "--folder"),
    limit: int | None = typer.Option(None, "--limit", "-l"),
    skip_validation: bool = typer.Option(False, "--skip-validation"),
    use_ai: bool = typer.Option(False, "--use-ai"),
):
    ...
```

## 15. Manejo de errores

Casos esperados:

### Sin API key

Mensaje:

```text
IA solicitada, pero OPENAI_API_KEY no está configurada. Se usará análisis local.
```

### Timeout

Mensaje:

```text
La clasificación IA tardó demasiado para algunos bookmarks. Se conservaron resultados locales.
```

### JSON inválido

Mensaje:

```text
La IA devolvió una respuesta inválida. Se conservó clasificación local para ese bookmark.
```

### Rate limit

Mensaje:

```text
El proveedor IA limitó las solicitudes. Se analizaron algunos bookmarks con IA y el resto quedó con análisis local.
```

## 16. Tests mínimos

No llamar a OpenAI real en tests.

Tests sugeridos:

```text
test_ai_disabled_by_default
test_use_ai_without_api_key_falls_back_to_local
test_ai_response_updates_category_priority_and_reason
test_invalid_ai_json_keeps_local_result
test_run_analysis_accepts_use_ai_parameter
```

Usar mocks/fakes.

Ejemplo conceptual:

```python
def test_ai_result_enriches_local_result(monkeypatch):
    ...
```

## 17. Criterios de terminado

La feature CLI IA está lista cuando:

- `poetry run pytest` pasa.
- El análisis sin IA sigue funcionando igual.
- El análisis con `--use-ai` no rompe si no hay API key.
- Con API key configurada, al menos algunos bookmarks reciben categoría y razón IA.
- Los reportes muestran la razón enriquecida.
- README explica que IA es opcional.
- `.env.example` documenta variables.
- No se sube `.env` real.
- No se envía contenido completo de páginas.
- No se eliminan bookmarks automáticamente.

## 18. Ejemplo de demo esperada

Comando:

```bash
poetry run python -m app.cli analyze examples/sample_bookmarks.html --folder "Pendientes" --limit 10 --skip-validation --use-ai
```

Salida esperada conceptual:

```text
Analizando carpeta: Pendientes
Bookmarks encontrados: 10
IA: activada
IA aplicada a: 10 bookmarks
Reportes generados en: data/reports
```

Resultado mejorado:

```text
Compra Gamer
Categoría local: ia
Categoría IA: compras
Acción: ver_luego
Razón: Tienda de hardware/gaming guardada como referencia de compra futura.
```

## 19. Después de CLI

Una vez validada la CLI, llevar IA a UI:

- Checkbox "Usar IA".
- Aviso de privacidad.
- Campo de límite recomendado.
- Mostrar "IA activada/desactivada" en summary.
- Mostrar motivo IA en tabla.
- Indicar cuántos bookmarks fueron enriquecidos.

## 20. Evolución posterior

Después de esta feature, se puede avanzar hacia:

- Agenda IA de 7 días.
- Agrupación semántica.
- Vista árbol de carpetas.
- Preguntas tipo "qué debería leer primero".
- Export de bookmarks reorganizado.
- Integración local con modelos open-source.
- Persistencia histórica de análisis.
