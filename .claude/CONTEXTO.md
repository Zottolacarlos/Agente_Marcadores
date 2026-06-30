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

**Fecha:** 2026-06-30 · **Dispositivo:** PC de escritorio (tenía una copia MUY vieja del repo) · **se reinicia Windows ahora.**

**Esta sesión fue de sincronización, no de features.** Esta PC estaba **10 commits atrás**. Se hizo:
- `git pull` con fast-forward (bajaron los 10 commits: capa IA, dashboard, chat, árbol, tests, docs).
- Conflictos resueltos: `.gitignore` **combinado** (exclusiones de datos personales del remoto + `.env.*`/cachés/IDEs locales); `README.md` → se tomó el **del remoto (español)** y se descartó un rewrite local en inglés.
- `ROADMAP.md` (inglés, sin trackear) **eliminado** (la dirección vive en README "Próximos pasos" + `docs/ESTADO_ACTUAL.md`). `examples/sample_report.md` agregado. **Commit `d49e1b8`**.
- Venv actualizado: le faltaba `openai` (era previo a la capa IA) → `pip install -r requirements.txt` (openai 2.44). `.env` creado desde la plantilla con **OPENAI_API_KEY vacío** (el usuario la pone a mano; `.env` está gitigorado).
- Backend probado OK: `/`, `/nuevo`, `/informe` → 200. **Logging del chat CONFIRMADO funcionando** (`[INFO] app.web: POST /chat ...` en consola/stderr).

**PRÓXIMO PASO AL RETOMAR (lo más importante):** **diagnosticar el chat-agente.** El logging ya está confirmado; falta que el usuario ponga su `OPENAI_API_KEY` en `.env`, levante el backend y pruebe una consulta real, pasando (a) qué preguntó + qué respondió, (b) las líneas `app.chat`/`app.web` del log. **Sospecha fuerte (sin cambiar):** el chat consulta `bookmarks_analysis`, que guarda la **categoría de REGLAS, no la de la IA** (ni `effective_score`). Si se confirma, el fix es **persistir `ai_category` + `effective_score` en las filas** (`save_analysis` + esquema). Eso deja la base para la capa de decisiones.

**Pendientes inmediatos:** (1) `git push` del commit `d49e1b8` — se hizo en esta sesión (ver más abajo). (2) chat necesita la API key para testearse. Más pendientes de features anotados abajo.

**Nota de seguridad:** `tests/resultados/` se filtró sin querer a GitHub (commit 582f51d) pero eran solo datos del **sample** (benigno). Ya está ignorada y fuera del HEAD. Purga de historial = opcional/pendiente. `perfil.md`, `.env`, `pruebas de diseño/` siguen protegidos.

## En qué estábamos / próximos pasos

- [x] **IA conectada a la web** (2026-06-26): checkbox "Usar IA" en `index.html` (con aviso de privacidad y disabled si no hay key), `use_ai` cableado en `web_router.py` (`/analyze` + `home` pasa `ai_available`), banner + info IA por link en `summary.html` (badge `pill-ai`, motivo, confianza, ⚠ baja conf). Tests web mockeados en `tests/test_web_ai.py`. Total **31 passed**.
- [x] **Blending de score** (2026-06-26): `effective_score = (1-w)·local + w·IA_priority` con `w=AI_BLEND_WEIGHT` (0.6), gated por `AI_MIN_CONFIDENCE` (subido a **0.70**). Re-ordena top + cronograma y recalcula acción vía `priority_scorer.action_from_score()`. Score local intacto/visible. Propagado a reportes (md/cronograma/CSV `effective_score`) y web (columna "Prioridad" + desglose `local · IA`). Probado en vivo: LinkedIn subió, Transformers cayó 55→28→archivar. Total 32 tests.
- [x] **Cronograma con datos IA** (2026-06-26): el plan de 7 días ahora se **renderiza en la web** (`summary.html`, antes solo `.md` descargable), ordenado por `effective_score` (blended) y mostrando el "por qué" de la IA (intención + razón) por link. `AnalysisSummary.schedule` expone el cronograma. Reporte `.md` también enriquecido. +1 test web. Total 33.
- [x] **Vista árbol de carpetas** (2026-06-27): `folder_tree.build_folder_tree` (árbol anidado completo con conteo recursivo); `/folders` devuelve `tree`; `index.html` lo renderiza navegable (▸ expandir, colapsado x defecto, clic en nombre = elige subárbol). Reemplaza los chips. +tests `test_folder_tree.py`.
- [x] **Bugfix filtro de carpeta** (2026-06-27): `target_folder` con barra final (ej "Games/") excluía los items directos. Se normaliza con `.strip("/")` en ambos lados. +`test_analyzer_folder.py`.
- [x] **Logging backend** (2026-06-27): `app/logging_config.py` (logger "app", ASCII, vía `LOG_LEVEL`), activado en `main.py` y `cli.py`. `analyzer` loguea filtro/alcance/carpetas/categorías/acciones/rangos de score/IA; `web_router` loguea origen y árbol. Clave para diagnosticar sin capturas.
- [x] **`run.ps1`**: atajo para levantar la web (`.\run.ps1`).
- [ ] **Probar IA real**: ✅ hecho — corridas reales con OpenAI OK (gasto sesión IA ~$0.008).

### Hallazgos del análisis (diagnóstico con logs reales, 2026-06-28) — PRÓXIMOS FIXES
El usuario corrió Landings (797 scopeados, IA on) y Games (100, todo "gaming"). Diagnóstico:
- [x] **Fix scorer false-positives** (2026-06-28, commit 605b2b1): word boundaries en el scorer. "dev" ya no matchea "Devastator" (70→50).
- [x] **Cobertura IA (batch)** (2026-06-28): `ai_classifier.classify_bookmarks_batch` manda varios bookmarks por llamada (con "id" para alinear). El analyzer clasifica TODOS los analizados (tope `AI_MAX_BOOKMARKS` subido a 200, `AI_BATCH_SIZE`=20). Prompt: la carpeta es "pista débil, no decisiva" (ataca el punto 3). Probado: 6 bookmarks en 1 llamada, enriquecidos=6. **PENDIENTE: que el usuario lo pruebe en su carpeta real grande (Landings/Games) — la alineación multi-lote por id no se probó en vivo aún.**
- [ ] **Lectura de páginas (2do paso del plan acordado)**: la validación es superficial (solo status). Sumar fetch del contenido real (httpx liviano: título/description/encabezados/texto; Playwright como upgrade JS) para alimentar a la IA. Decisión del usuario: empezamos por "IA-todos sin leer página" (hecho), la lectura va después. NO es MCP (su app usa OpenAI directo); es Playwright/httpx como librería.
- [ ] **Velocidad validación**: usuario dijo "calidad > velocidad, no me importa que tarde". Paralelizar queda como mejora opcional, no prioritaria.
- [ ] **Score plano para ocio** (rules-only): mitigado cuando IA on (ahora cubre todos).

### Features de UX pedidas (2026-06-28)
- [x] **Mostrar más (top 25)**: el resumen muestra hasta 25 (antes 10); las filas 11-25 ocultas con botón "Ver más". `top_recommended[:25]` + toggle JS en `summary.html`.
- [x] **Multi-selección de carpetas** (2026-06-28): `run_analysis` parsea `target_folder` por líneas → varios filtros (matchea cualquiera). UI: el campo es textarea (una carpeta por línea) y el árbol hace multi-toggle (clic agrega/saca). +tests `test_analyzer_folder`. Probado e2e: "Games\\nIMSA" → 2/2.
- **Análisis acumulativo / continuable + revisión humana** (GRANDE, en curso). Aclaración del usuario: el foco es un **DASHBOARD persistente** — al abrir la app, ver qué se hizo último + el plan de hoy, para retomar un trabajo de varios días. NO un diario día-a-día (solo el estado actual). NO crear carpetas nuevas en los marcadores; las acciones serán borrar / mover a carpeta EXISTENTE.
  - [x] **3a — Persistencia + dashboard read-only** (2026-06-28): tabla `analysis_state` (1 fila, última corrida), `SQLiteRepository.save_state/load_state` (guarda el `AnalysisSummary` como JSON). `run_analysis` persiste estado al terminar. Rutas: `/` = dashboard si hay estado (si no, el form), `/nuevo` = form, `/informe` = re-muestra el último informe. `dashboard.html` (última corrida, métricas, Plan de hoy = Día 1 del cronograma, top 10). 44 tests.
  - [ ] **3b — Decisiones humanas persistidas**: borrar/conservar/mover-a-carpeta-existente/revisado por marcador (override sobre IA/reglas), con progreso (pendiente/revisado). Requiere columnas nuevas + UPSERT por normalized_url (acumular al sumar carpetas otro día).
  - [ ] **3c — Export reorganizado**: aplicar las decisiones a un `bookmarks.html` nuevo para reimportar (no destructivo, sin carpetas nuevas).
  - **Chat-agente** (la visión nueva del usuario: 3b se absorbe acá — el agente hace las acciones conversando; se habilita DESPUÉS de un análisis, no siempre).
    - [x] **Chat read-only v1** (2026-06-28): `chat_agent.py` con tool-calling de OpenAI (tools `buscar_marcadores`, `estadisticas` sobre las filas persistidas). Endpoint `POST /chat`. Partial `_chat.html` incluido en dashboard e informe. SOLO consulta, no modifica. Probado real: responde con datos y es honesto si no hay match. 50 tests.
    - [ ] **Capa de decisiones** (backend): persistir por marcador borrado/mover_a/categoria_humana (UPSERT por normalized_url para acumular). Es sobre lo que actuará el agente.
    - [ ] **Herramientas de acción + confirmación**: `marcar_borrar`, `mover_a_carpeta` (existente), `cambiar_categoria`, con preview/confirmación antes de aplicar.
    - [ ] **Export reorganizado** (3c): aplica decisiones a un bookmarks.html nuevo. No crea carpetas nuevas. No toca el browser vivo.
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
