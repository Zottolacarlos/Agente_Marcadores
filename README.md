# bookmark-curator-agent

MVP local para curar marcadores del navegador y convertirlos en un plan accionable.

## Qué problema resuelve
Ayuda a limpiar acumulación de links guardados (por ejemplo carpeta **Pendientes**) y entrega:
- links activos / rotos
- duplicados
- categoría
- score y acción recomendada
- cronograma simple de 7 días

## Privacidad
- Ejecuta localmente por defecto.
- No subas bookmarks reales al repositorio.
- No envía datos a IA externa salvo activación explícita futura.

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso web
```bash
uvicorn app.main:app --reload
```
Abrir `http://localhost:8000`.

## Uso CLI
```bash
python -m app.cli analyze examples/sample_bookmarks.html --folder Pendientes
python -m app.cli analyze-browser chrome --folder Pendientes
python -m app.cli analyze-browser edge --folder Pendientes
# Flags útiles: --limit/-l N, --skip-validation (sin red), --use-ai (IA opcional)
```

## IA opcional
Apagada por defecto; el análisis funciona 100% con reglas locales. Para activarla:
1. Copiá `.env.example` a `.env` y completá `OPENAI_API_KEY` (no se commitea).
2. Agregá `--use-ai` al comando:
   ```bash
   python -m app.cli analyze examples/sample_bookmarks.html --folder Pendientes --skip-validation --use-ai
   ```
La IA es **aditiva**: enriquece cada bookmark (categoría/intención/razón) sin pisar la clasificación local, que queda siempre como fallback. Solo se envía metadata mínima (título, URL, carpeta, estado) — nunca el contenido de la página. Si no hay API key o algo falla, sigue con reglas locales. Variables: `OPENAI_MODEL`, `AI_MAX_BOOKMARKS`, `AI_TIMEOUT_SECONDS`.

## Exportar bookmarks manualmente
Desde tu navegador exporta a `bookmarks.html` y guárdalo en `data/input/`.

## Lectura automática Chrome/Edge
Busca perfiles `Default`, `Profile 1`, `Profile 2`, etc. en Windows para Chrome/Edge.

## Reportes generados
Se guardan en `data/reports/`:
- pendientes_priorizados.md
- links_rotos.md
- duplicados.md
- cronograma_7_dias.md
- resultado.csv

## Limitaciones
- Firefox: pendiente (TODO).
- Duplicados: solo por URL normalizada.
- IA: disponible vía `--use-ai` (etapa CLI). En la web todavía no está conectada.

## Próximos pasos (Fase 2)
- IA opcional para clasificación fina y resumen por link.
- Mejor heurística de duplicados (dominio + path similar).
- Integraciones Pocket/Readwise/Notion.
