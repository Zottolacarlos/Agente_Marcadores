# Privacidad y protección de datos

> Los bookmarks son **datos sensibles**: revelan trabajo, intereses, finanzas, salud, proyectos y
> hábitos de una persona. Este documento fija cómo se tratan hoy (MVP local) y cómo deberán tratarse
> cuando el proyecto sea una **app pública multiusuario**.

## 1. Estado actual (MVP local-first)

- Todo corre **localmente**. No hay servidor multiusuario ni envío de datos salvo IA opcional.
- **Datos sensibles y dónde viven** (todos fuera de git):
  - `bookmarks.html` / perfiles de Chrome-Edge → `data/input/` (gitignored).
  - Reportes generados → `data/reports/` (gitignored).
  - `perfil.md` (contexto laboral real) → **gitignored** (el repo es público). Solo se versiona `perfil.example.md`.
  - `.env` (API keys) → gitignored.
- **IA opcional y explícita** (`--use-ai`): apagada por defecto, fallback local sin key.
- **Minimización**: a la IA se envía solo metadata (título, URL, carpeta, estado). **Nunca** el contenido de la página.

## 2. Riesgos a tener presentes

- Commitear datos personales a un repo **público** es difícil de revertir (quedan en el historial, se indexan/cachean).
- Enviar bookmarks a un proveedor IA (OpenAI) implica un **tercero que procesa** datos del usuario.
- Logs/reportes pueden filtrar contenido sensible si no se cuidan.

## 3. Plan para la app pública (futuro — NO implementar todavía)

Cuando se pase de MVP local a app con usuarios reales:

### Datos por usuario
- Perfiles y bookmarks dejan de vivir en el repo: van a una **base de datos por usuario**, con
  **autenticación** y **aislamiento estricto** (un usuario nunca ve datos de otro; row-level security).
- **Cifrado** en tránsito (TLS) y en reposo (DB/secretos cifrados).
- **Retención y borrado**: el usuario puede exportar y **eliminar todos sus datos** (derecho al olvido).

### IA y terceros
- **Consentimiento explícito** antes de mandar nada a un proveedor externo.
- Acuerdo de procesamiento de datos (**DPA**) con el proveedor; preferir endpoints que **no entrenen** con los datos.
- Ofrecer un **modo sin IA** y, a futuro, opción de **modelo local/open-source** para usuarios sensibles.
- Seguir mandando solo metadata mínima; lectura de contenido de páginas solo con opt-in claro.

### Operación
- Secretos en un **vault/gestor** (no en `.env` en producción).
- **No loguear** contenido sensible (títulos/URLs) en texto plano; anonimizar/recortar.
- Rate limiting y límites de costo IA por usuario (ya existe `AI_MAX_BOOKMARKS` como semilla).

### Marco legal
- Considerar **Ley 25.326** (Argentina, protección de datos personales) y **GDPR** si hay usuarios UE.
- Política de privacidad y términos claros antes de abrir registro.

## 4. Regla de oro mientras tanto

Nunca commitear datos reales (bookmarks ni `perfil.md`) al repo público. Para sincronizar `perfil.md`
entre tus PCs sin exponerlo: usá un canal privado (OneDrive/Drive, un gist privado, o copiarlo a mano).
