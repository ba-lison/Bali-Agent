# Heurísticas de Detecção de Stack

> Guia para o Setup Agent identificar as tecnologias e o escopo do projeto lendo os arquivos locais.

## Regras de Detecção por Arquivos-Sinal

Para mapear a stack tecnológica do projeto, o Setup Agent deve buscar pelos seguintes sinais na raiz e subdiretórios:

### 1. Frontend & Web
*   **Next.js**: Presença de `next.config.js`, `next.config.mjs` ou dependência `next` em `package.json`.
    *   *Especialista sugerido:* `spec-nextjs` (escopo: React, App Router, RSC, Server Actions).
*   **React (Single Page App)**: Dependência `react` em `package.json` sem Next.js.
    *   *Especialista sugerido:* `spec-react` (escopo: hooks, client components, state management).
*   **Vue / Nuxt**: Dependência `vue` ou `nuxt` em `package.json` ou arquivo `nuxt.config.js`/`vite.config.js` com plugins Vue.
    *   *Especialista sugerido:* `spec-vue` (escopo: Composition API, Vue Router, Pinia).
*   **CSS / Styling**: Dependência `tailwindcss` em `package.json`, arquivo `tailwind.config.js`, ou estilos puros.

### 2. Backend & Server-Side
*   **Node.js / Express**: Arquivo `package.json` com dependências como `express`, `koa`, `fastify`, `nest`.
    *   *Especialista sugerido:* `spec-nodejs` (escopo: APIs REST, middlewares, async handlers).
*   **Python (FastAPI / Flask)**: Presença de `requirements.txt` com `fastapi`/`flask`, `pyproject.toml`, `poetry.lock` ou `Pipfile`.
    *   *Especialista sugerido:* `spec-python` (escopo: FastAPI/Flask, Pydantic, asyncio).
*   **C# / .NET (AutoCAD Plugins)**: Arquivos `*.csproj`, `*.sln`, ou dependências referenciando `Autodesk.AutoCAD.Runtime`, `Autodesk.AutoCAD.DatabaseServices`.
    *   *Especialista sugerido:* `spec-autocad-csharp` (escopo: Plugins AutoCAD, Autodesk API, Windows forms/WPF, .NET).
*   **PHP (WordPress / WooCommerce)**: Presença de `wp-config.php`, `wp-content/`, `composer.json` com deps `wordpress`/`woocommerce`, ou plugins WP.
    *   *Especialista sugerido:* `spec-wordpress` (escopo: Hooks/Filters do WP, custom post types, WooCommerce APIs).

### 3. Banco de Dados & Serviços
*   **Supabase**: Presença de pasta `supabase/` contendo `config.toml`, `migrations/`, ou dependência `@supabase/supabase-js`.
    *   *Especialista sugerido:* `spec-supabase` (escopo: Schema PostgreSQL, RLS - Row Level Security, Edge Functions).
*   **PostgreSQL (Geral)**: Arquivos de migração SQL (`*.sql`), ou dependências como `pg`, `prisma` (com provider `postgresql`), `sequelize`.
    *   *Especialista sugerido:* `spec-database-postgres` (escopo: Schemas, SQL queries, otimização de indexes, migrations).
*   **MongoDB**: Dependência `mongoose` ou `mongodb` em `package.json`.
    *   *Especialista sugerido:* `spec-database-mongo` (escopo: Schemas NoSQL, aggregation pipelines).

### 4. Infraestrutura & DevOps
*   **Docker**: Presença de `Dockerfile` ou `docker-compose.yml`.
    *   *Especialista sugerido:* `spec-devops` (escopo: Containerização, multi-stage builds, compose).
*   **GitHub Actions**: Presença de arquivos YAML dentro de `.github/workflows/`.
    *   *Especialista sugerido:* `spec-devops` (escopo: CI/CD workflows, automated testing gates).

---

## Mapeamento de Especialistas

A detecção de stack **direciona** quais arquétipos locais de `.agent/agents/_specialists/` devem ser gerados.
Por exemplo, se o projeto for Next.js + Supabase:
- O Setup Agent propõe instanciar o arquétipo `frontend.md` preenchido com as regras de Next.js (`spec-nextjs.md`).
- O Setup Agent propõe instanciar o arquétipo `database.md` preenchido com as regras e o schema do Supabase/PostgreSQL (`spec-supabase.md`).
