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

**Fecha:** 2026-06-24 · **Dispositivo:** PC principal (`C:\Zsimia\Agente_Marcadores`)

- Se generó `CLAUDE.md` (guía de arquitectura para futuras instancias de Claude).
- Se diseñó este sistema de continuidad entre dispositivos (esta bitácora + instrucciones en `CLAUDE.md`).

## En qué estábamos / próximos pasos

- [ ] Probar el flujo de continuidad: hacer `git push` desde acá y `git pull` + retomar en otra PC.
- [ ] (Pendiente de roadmap del proyecto, ver README "Fase 2"): IA opcional para clasificación fina, mejor heurística de duplicados, integraciones Pocket/Readwise/Notion, soporte Firefox.

## Decisiones tomadas

- **Continuidad entre dispositivos = git, no `/resume`.** Las rutas del repo difieren entre las 3 PCs, así que `/resume` no encontraría las sesiones (la carpeta de sesiones se deriva de la ruta absoluta). Se elige una bitácora versionada que funciona en cualquier ruta/PC.

## Notas / pendientes sueltos

- `bookmark_web_ui.patch` quedó suelto en la raíz del repo — revisar si se aplica o se borra.
- Privacidad: nunca commitear marcadores reales (`data/input/` y `data/reports/` están en `.gitignore`).

---

### Cómo mantener este archivo

Mantenelo corto y útil. Cada vez que cierres una sesión, actualizá **Última sesión**, **En qué estábamos** y, si corresponde, **Decisiones**. Borrá lo que ya no aplica — no es un log histórico infinito, es un "handoff" del estado vivo.
