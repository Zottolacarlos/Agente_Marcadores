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
python -m app.cli analyze --file data/input/bookmarks.html --folder Pendientes
python -m app.cli analyze-browser --browser chrome --folder Pendientes
python -m app.cli analyze-browser --browser edge --folder Pendientes
```

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
- IA: interfaz preparada, sin clasificación activa aún.

## Próximos pasos (Fase 2)
- IA opcional para clasificación fina y resumen por link.
- Mejor heurística de duplicados (dominio + path similar).
- Integraciones Pocket/Readwise/Notion.
