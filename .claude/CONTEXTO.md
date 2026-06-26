# CONTEXTO — Bitácora de continuidad entre dispositivos

> **Propósito.** Este archivo viaja con el repo (git). Es la fuente de verdad para retomar el trabajo en cualquier PC.
> No depende de `/resume` ni de archivos `.jsonl` locales (esos NO se sincronizan entre máquinas).
>
> **Al EMPEZAR a trabajar (en cualquier dispositivo):** `git pull`, abrir Claude Code en el repo y pedirle "leé `.claude/CONTEXTO.md` y seguimos".
> **Al TERMINAR:** pedirle a Claude "actualizá `.claude/CONTEXTO.md` y commiteá". Después `git push`.
>
> **Regla de oro:** trabajar en UN dispositivo a la vez. Siempre `git pull` antes de empezar y `git push` al terminar, así evitás divergencias.

---

## Estado actual del proyecto

`bookmark-curator-agent`: MVP local (FastAPI + CLI) que cura marcadores del navegador y los convierte en un plan accionable (links rotos, duplicados, categoría, score, acción recomendada, cronograma de 7 días). Detalle de arquitectura en `CLAUDE.md`.

- **Stack:** Python ≥3.11, FastAPI + Jinja2 (web), Typer (CLI), Pydantic, httpx, BeautifulSoup, SQLite.
- **Pipeline central:** `app/services/analyzer.py::run_analysis` orquesta todas las etapas.
- **Estado:** funcional. Tests en `tests/` pasan. Clasificación por reglas de keywords (sin IA todavía; `ai_classifier.py` es un stub).

## Última sesión

**Fecha:** 2026-06-25 · **Dispositivo:** PC principal (`C:\Zsimia\Agente_Marcadores`)

- **Upgrade de UX de la web (3 cosas):**
  1. **Tema oscuro** en toda la web (paleta reescrita en `app/templates/base.html`; el resto de templates heredan).
  2. **Sugerencia de carpetas:** nuevo `app/services/folder_tree.py::extract_folder_tree` (carpetas 1er/2do nivel con conteo, limpia el prefijo de perfil `Default`/`Profile N`) + endpoint `POST /folders` (JSON) en `web_router.py`. El `index.html` detecta el origen y muestra *chips* clickeables que rellenan la carpeta objetivo.
  3. Se aclaró que la subida del HTML **ya** funciona desde la web (el `data/input/` era solo para el CLI); se reordenó el form (origen → carpeta → opciones).
- Verificado con TestClient (`GET /`, `POST /folders`) y `pytest` (12 passed). Se creó `.venv` local.

## En qué estábamos / próximos pasos

- [x] **IA conectada a la web** (2026-06-26): checkbox "Usar IA" en `index.html` (con aviso de privacidad y disabled si no hay key), `use_ai` cableado en `web_router.py` (`/analyze` + `home` pasa `ai_available`), banner + info IA por link en `summary.html` (badge `pill-ai`, motivo, confianza, ⚠ baja conf). Tests web mockeados en `tests/test_web_ai.py`. Total **31 passed**.
- [x] **Blending de score** (2026-06-26): `effective_score = (1-w)·local + w·IA_priority` con `w=AI_BLEND_WEIGHT` (0.6), gated por `AI_MIN_CONFIDENCE` (subido a **0.70**). Re-ordena top + cronograma y recalcula acción vía `priority_scorer.action_from_score()`. Score local intacto/visible. Propagado a reportes (md/cronograma/CSV `effective_score`) y web (columna "Prioridad" + desglose `local · IA`). Probado en vivo: LinkedIn subió, Transformers cayó 55→28→archivar. Total 32 tests.
- [x] **Cronograma con datos IA**: ya usa `effective_score` (orden blended) — el item 7 queda cubierto por el blending.
- [ ] **Vista árbol de carpetas** (item 8): hoy hay chips sugeridos, falta el árbol visual navegable.
- [ ] **Probar IA real**: copiar `.env.example`→`.env`, poner `OPENAI_API_KEY` y correr `--use-ai` con la API real (hasta ahora probado solo con mocks + fallback sin key).
- [ ] **(Opcional, evaluado) Blending de score IA**: hoy la IA es aditiva (no toca score/orden, para no meter ruido). Próximo paso posible: que la prioridad IA influya en el orden/acción.
- [ ] **Rediseñar la visualización de niveles de carpeta** (los chips 1er/2do nivel "no se entienden"). El usuario va a mandar una captura para acertar el diseño. PENDIENTE de su imagen.
- [ ] **Decidir la acción final del agente** (qué hace con el resultado más allá de reportes). Opciones evaluadas: (a) solo recomendar [hoy], (b) generar export reorganizado para reimportar, (c) manipular navegador. El usuario eligió "decidir después", cuando lo vea funcionando mejor. Hoy `archivar`/`borrar_probable` son solo etiquetas advisory; no se mueve/borra nada real.
- [ ] Commit + push de este upgrade (pendiente de pedido del usuario).
- [ ] Probar el flujo de continuidad: `git push` desde acá y `git pull` + retomar en otra PC.
- [ ] (Roadmap "Fase 2" del README): IA opcional para clasificación fina, mejor heurística de duplicados, integraciones Pocket/Readwise/Notion, soporte Firefox.

## IA con perfil + taxonomía cerrada + freno por confianza (2026-06-26)

Paso "1" del plan acordado: personalizar la IA con el contexto del usuario sin alucinar.

- **`perfil.md`** (creado por el usuario a partir de `perfil.example.md`): contexto real (rol backend Python/AWS/IA, IMSA/PRODUCCION WinDev, proyecto Danone React/Supabase, jobs alta prioridad, ocio comics/gaming), jerga de carpetas, taxonomía cerrada (sección 7) y reglas personales (sección 8).
- **`ai_classifier.py`**: `load_profile()` lee `perfil.md` (si no existe → IA genérica), `_parse_taxonomy()`/`load_taxonomy()` extraen la lista cerrada de la sección 7, `build_system_prompt()` inyecta instrucciones + taxonomía + perfil en el mensaje `system` (estático → OpenAI lo cachea). `enforce_taxonomy()` fuerza a `desconocido` cualquier categoría inventada fuera de la lista (backstop anti-alucinación).
- **Freno por confianza**: `AI_MIN_CONFIDENCE` (default 0.5). `run_analysis` cuenta `ai_low_confidence`; CLI y reportes marcan los dudosos (⚠).
- **config/.env.example**: `AI_MIN_CONFIDENCE`, `PERFIL_PATH`.
- Tests: +7 (parseo taxonomía, fallback sin perfil, inyección en prompt, coerción, baja confianza). Total **28 passed**, ruff limpio.
- **Probado en vivo**: con perfil, Transformers→entretenimiento prio 10 (era ver_luego 40), FastAPI→python leer_hoy 90, LinkedIn→jobs conf 1.00. Categorías ya salen de la taxonomía (no más "tecnologia/empleo" inventadas).
- **Costo medido (gpt-4.1-mini, perfil cacheado)**: ~$0.003 / 6 bookmarks · proyección ~$0.015/30 · ~$0.50/1000. Gasto total de pruebas IA de la sesión ≈ $0.005.
- **DECIDIDO: `perfil.md` NO se versiona** (agregado a `.gitignore`). El repo es **público** (github.com/Zottolacarlos/Agente_Marcadores), así que versionarlo expondría datos laborales (IMSA/Danone/PRODUCCION). Solo se versiona la plantilla `perfil.example.md`. Para sincronizar entre PCs: canal privado (OneDrive/Drive/gist privado), no git.
- **Nuevo `docs/PRIVACIDAD.md`**: principios actuales (local-first, IA opt-in, metadata mínima, gitignore de datos) + plan para la futura app pública (datos por usuario, auth+aislamiento, cifrado, retención/borrado, DPA con proveedor IA, modo sin-IA/modelo local, Ley 25.326/GDPR). NO implementar todavía, es guía.

## IA opcional — etapa CLI (2026-06-25, parte 3)

Implementada la **etapa 1 del plan `docs/PLAN_IA_CLI.md`** (provider OpenAI `gpt-4.1-mini`, solo CLI, aditiva, apagada por defecto). Decisiones: el usuario eligió OpenAI (su `.env` ya tenía la key cableada) y alcance solo-CLI.

- **Nuevo**: `app/models/ai.py` (`AIBookmarkClassification`), `ai_classifier.py` real (`is_ai_available`, `build_payload`, `classify_bookmark_with_ai` con fallback total a None ante cualquier error).
- `BookmarkAnalysis.ai` (campo aditivo opcional). `AnalysisSummary.ai_used`/`ai_enriched`.
- `run_analysis(..., use_ai=False)`: enriquece top-N (`AI_MAX_BOOKMARKS`) tras el análisis local SIN tocar categoría/score/orden (local = fallback siempre presente). Si IA no disponible y se pidió, deja warning.
- `cli.py`: flag `--use-ai` en ambos comandos.
- `config.py` + `.env.example`: `OPENAI_MODEL`, `AI_MAX_BOOKMARKS`, `AI_TIMEOUT_SECONDS`.
- Reportes (md + csv) muestran la info IA cuando existe.
- Dep `openai>=1.40.0` (requirements + pyproject). `examples/sample_bookmarks.html` para demo.
- Tests: `tests/test_ai_classifier.py` (6, con mocks, sin llamar a OpenAI). Total **22 passed**. Ruff limpio.
- **No persiste IA en SQLite** todavía (columnas fijas; es "evolución posterior" del plan).

## Arreglos de esta sesión (2026-06-25, parte 2)

- **Clasificación reescrita** (`rule_classifier.py`): bug grave de falsos positivos. Causa: `keyword in title+url+folder` sin límites de palabra y con la URL cruda → keywords cortas (`s3`,`lambda`) matcheaban dentro de IDs de YouTube, y `rag`⊂"storage". Fix: regex `\b…\b`, se sacó la URL del match de contenido (solo título+carpeta), y `DOMAIN_RULES` (host→categoría) como respaldo. Ej: video de Transformers pasó de aws/85 a comics/55. +4 tests.
- **Score transparente** (`priority_scorer.py` + `summary.html`): cada factor lleva su delta (`base 30, categoría clave (+30)…`), visible inline y como tooltip sobre el número.
- **Confirmación de archivo** (`index.html` + `base.html`): cartel verde con nombre/tamaño/cantidad de marcadores al subir el `.html`.
- Tests: 16 passed.

## Decisiones tomadas

- **Continuidad entre dispositivos = git, no `/resume`.** Las rutas del repo difieren entre las 3 PCs, así que `/resume` no encontraría las sesiones (la carpeta de sesiones se deriva de la ruta absoluta). Se elige una bitácora versionada que funciona en cualquier ruta/PC.

## Notas / pendientes sueltos

- `bookmark_web_ui.patch` quedó suelto en la raíz del repo — revisar si se aplica o se borra.
- Privacidad: nunca commitear marcadores reales (`data/input/` y `data/reports/` están en `.gitignore`).

---

### Cómo mantener este archivo

Mantenelo corto y útil. Cada vez que cierres una sesión, actualizá **Última sesión**, **En qué estábamos** y, si corresponde, **Decisiones**. Borrá lo que ya no aplica — no es un log histórico infinito, es un "handoff" del estado vivo.
