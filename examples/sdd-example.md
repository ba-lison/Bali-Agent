# SDD: TaskFlow AI

> **Autor:** Marina Santos (Tech Lead) | **Data:** 06/06/2026 | **Versão:** 1.0 | **PRD:** [Link para PRD](./prd-example.md) | **Status:** Em Revisão

---

## 1. Contexto e Motivação

### 1.1 Problema Técnico
Este SDD descreve a arquitetura técnica para resolver o problema de priorização manual e ineficiente de backlogs detalhado na seção 2 do [PRD do TaskFlow AI](./prd-example.md). O principal desafio técnico consiste em construir um sistema que processe backlogs de até 500 tarefas em menos de 3 segundos (p99) utilizando Modelos de Linguagem (LLMs), garantindo explicabilidade transparente e mantendo o custo por request abaixo de $0,02.

### 1.2 Contexto
O TaskFlow AI está sendo desenvolvido do zero (projeto Greenfield). Não há sistemas legados ou migrações de dados complexas para a v1, exceto a necessidade de suportar importação via APIs do Jira, Trello e Asana. 

A equipe técnica é composta por:
- 1 Tech Lead (Marina Santos)
- 5 Engenheiros Backend
- 2 Engenheiros Frontend
- 1 QA Lead (Juliana Almeida)
- 1 SRE (Carlos Eduardo Lima)
- 1 ML Engineer (Ana Beatriz Costa)

O prazo de desenvolvimento é de 4 meses com deploy final em AWS.

---

## 2. Objetivos e Não-Objetivos Técnicos

### ✅ Objetivos
- Projetar uma API RESTful de alta performance que exponha serviços de gerenciamento de tarefas, priorização assistida por IA, dashboards e integrações.
- Desenvolver um pipeline de IA robusto que utilize GPT-4o e Claude 3.5 Sonnet (como fallback) com baixa latência e técnicas de redução de custo (caching, prompts incrementais).
- Garantir segurança ponta-a-ponta, criptografia de dados sob a LGPD e anonimização de PII antes de enviar dados a provedores externos de LLM.
- Estabelecer uma arquitetura de dados e indexação que suporte consultas analíticas rápidas para dashboards sem degradar operações CRUD.

### ❌ Não-Objetivos
- Desenvolver infraestrutura de chat ou mensageria síncrona.
- Suportar integrações com ERPs legados nesta fase.
- Construir aplicativos móveis nativos (Android/iOS).
- Implementar análise de performance de equipe para fins de recursos humanos (ranking de desenvolvedores).

---

## 3. Design Proposto

### 3.1 Arquitetura de Alto Nível

```mermaid
graph TD
    Client["Cliente (Web/PWA)"] -->|HTTPS / WSS| Gateway["AWS API Gateway (Reverse Proxy / Rate Limiting)"]
    Gateway -->|HTTP| Backend["FastAPI Monolito (ECS Fargate)"]
    
    Backend -->|SQL| Database[("PostgreSQL (RDS Aurora Multi-AZ)")]
    Backend -->|Caching & Queues| Cache[("Redis (ElastiCache)")]
    Backend -->|Integrations| GitHub["GitHub / GitLab API"]
    
    Backend -->|HTTPS| LLMService["OpenAI API (GPT-4o)"]
    Backend -->|HTTPS Fallback| LLMFallback["Anthropic API (Claude 3.5 Sonnet)"]
    
    %% Background Job Worker
    Cache -->|Consume Jobs| Worker["Celery Worker (Background tasks)"]
    Worker -->|Process Import/Sync| GitHub
    Worker -->|Batch Prioritization| LLMService
    Worker -->|Write Results| Database
```

### 3.2 Componentes

| Componente | Responsabilidade | Tecnologia | Justificativa |
|------------|------------------|------------|---------------|
| **Cliente Web** | Interface gráfica SPA responsiva. | React, Next.js, Tailwind CSS | SEO amigável por Server Side Rendering, performance e produtividade com ecossistema de componentes robusto. |
| **API Gateway** | Roteamento de tráfego, autenticação JWT inicial, CORS e mitigação de DDoS/Rate Limiting. | AWS API Gateway | Solução gerenciada, integrada à AWS com custo-benefício escalável e zero manutenção de servidor. |
| **FastAPI Monolito** | Executar regras de negócio, expor endpoints REST, gerenciar sessões de banco de dados e autenticação. | Python, FastAPI | Alta performance por assincronismo (async/await), auto-geração de OpenAPI docs e integração fluida com ferramentas de IA em Python. |
| **Database** | Persistência relacional de usuários, workspaces, tarefas, dependências e logs. | PostgreSQL (AWS Aurora RDS) | Consistência ACID rigorosa para dados transacionais, suporte nativo a JSONB e extensões de alta performance para queries analíticas e concorrência. |
| **Cache & Queue** | Caching de priorizações de IA, sessões ativas de usuários, rate limit distribuído e broker de tarefas Celery. | Redis (AWS ElastiCache) | Latência sub-milissegundo para leitura/escrita e excelente compatibilidade com Celery para background jobs. |
| **Celery Workers** | Processamento assíncrono de importações (Jira/Trello), webhooks do GitHub e repriorização de backlogs gigantes. | Celery (Python) | Desacoplamento de operações pesadas da thread principal da API, prevenindo timeouts de requisição HTTP. |

### 3.3 Fluxo de Dados

#### Fluxo: Execução de Priorização com IA (Modo Sugestão)

```mermaid
sequenceDiagram
    participant TL as Tech Lead
    participant FE as Frontend (Next.js)
    participant API as FastAPI Backend
    participant Redis as Redis Cache
    participant DB as PostgreSQL
    participant AI as OpenAI (GPT-4o)
    
    TL->>FE: Clique em "Priorizar Backlog"
    FE->>API: POST /api/v1/backlog/prioritize (workspace_id)
    API->>Redis: Check lock "prioritizing:{workspace_id}"
    Note over API,Redis: Evita concorrência e requests duplicados
    API->>DB: Obter tarefas ativas, dependências e histórico do sprint
    DB-->>API: Dados do backlog
    API->>API: Anonimizar dados PII (substituir nomes por IDs, remover emails)
    
    API->>Redis: Get cached prompt/prioritization (MD5 de input)
    alt Cache Hit
        Redis-->>API: Priorização em cache
    else Cache Miss
        API->>AI: Enviar prompt estruturado (backlog anonimizado)
        Note over API,AI: p99 < 3s para 500 tasks
        AI-->>API: Priorização em JSON (IDs ordenados + racional explicativo)
        API->>Redis: Cachear resultado (TTL: 1 hora)
    end
    
    API->>DB: Gravar sugestão em rascunho (status: PENDENTE)
    API-->>FE: Retorna ID da sugestão + backlog ordenado + racional explicativo
    FE-->>TL: Exibe diff visual (Board Atual vs Sugestão IA) + Sidebar com racional
```

### 3.4 Stack Tecnológica

| Camada | Tecnologia | Versão | Justificativa |
|--------|-----------|--------|---------------|
| Frontend | Next.js (App Router) | 14.x | Framework robusto com suporte a Server Components, rotas de API integradas e otimização automática de assets. |
| Backend | FastAPI | 0.110.x | Framework assíncrono rápido, tipagem estática via Pydantic e facilidade de escrita de testes automatizados. |
| Database | PostgreSQL | 16.x | Excelente performance em consultas relacionais complexas (necessárias para resolver dependências de tarefas) e tipos JSONB. |
| Cache/Queue | Redis | 7.x | Armazenamento chave-valor de altíssima performance para cache de queries e filas de background jobs. |
| Tasks Worker | Celery | 5.3.x | Gerenciamento de tarefas em segundo plano confiável, compatível com Redis e FastAPI. |
| Infraestrutura | AWS ECS (Fargate) | - | Containers serverless. Reduz custos de infraestrutura e sobrecarga de gerenciamento de OS para ECS/Kubernetes. |

---

## 4. APIs e Contratos

### 4.1 Solicitar Priorização de Backlog por IA

- **Método:** `POST`
- **Path:** `/api/v1/workspaces/{workspace_id}/backlog/prioritize`
- **Autenticação:** Bearer Token
- **Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```
- **Request Body:**
```json
{
  "force_recalculate": false,
  "focus_tag": "backend"
}
```

- **Response (202 — Accepted):**
```json
{
  "request_id": "8f9a2b5c-d3e7-4c12-a9b8-f5e6d7c8b9a0",
  "status": "processing",
  "estimated_time_seconds": 3,
  "created_at": "2026-06-06T13:00:00Z"
}
```

- **Response (200 — Success, se processado síncrono ou retornado do cache):**
```json
{
  "request_id": "8f9a2b5c-d3e7-4c12-a9b8-f5e6d7c8b9a0",
  "status": "completed",
  "workspace_id": "110e8400-e29b-11d4-a716-446655440000",
  "suggested_order": [
    {
      "task_id": "task-789",
      "new_index": 0,
      "old_index": 4,
      "priority_score": 98.5,
      "rational": "Bloqueia 3 tarefas críticas do Sprint Goal. Deadline em 2 dias. Complexidade estimada: Baixa."
    },
    {
      "task_id": "task-101",
      "new_index": 1,
      "old_index": 0,
      "priority_score": 85.2,
      "rational": "Vinculada a feature flag ativa. Alta complexidade estimada. Deadline em 5 dias."
    }
  ],
  "cost_usd": 0.0125,
  "execution_time_ms": 1420,
  "source": "openai-gpt-4o"
}
```

- **Erros:**

| Código | Descrição | Quando ocorre |
|--------|-----------|---------------|
| 400 | Bad Request | Se o payload estiver inválido ou sem campos requeridos. |
| 401 | Unauthorized | Se o JWT token for inválido, ausente ou expirado. |
| 403 | Forbidden | Se o usuário autenticado não pertencer à workspace informada. |
| 429 | Rate Limited | Se exceder 5 requisições de priorização por minuto por workspace. |
| 503 | Service Unavailable | Se o serviço de LLM da OpenAI estiver offline e o fallback falhar. |

---

## 5. Modelo de Dados

### 5.1 Diagrama ER

```mermaid
erDiagram
    WORKSPACE ||--o{ USER : contains
    WORKSPACE ||--o{ TASK : manages
    USER ||--o{ TASK : assigned_to
    TASK ||--o{ TASK_DEPENDENCY : parent
    TASK_DEPENDENCY }o--|| TASK : blocks
    TASK ||--o{ PRIORITY_SUGGESTION : evaluated_in
    
    WORKSPACE {
        uuid id PK
        string name
        string slug
        timestamp created_at
    }
    
    USER {
        uuid id PK
        string email
        string hashed_password
        string role
        uuid workspace_id FK
        timestamp created_at
    }
    
    TASK {
        uuid id PK
        string title
        string description
        string status
        date deadline
        integer story_points
        uuid assignee_id FK
        uuid workspace_id FK
        integer current_order
        timestamp created_at
    }
    
    TASK_DEPENDENCY {
        uuid id PK
        uuid parent_task_id FK
        uuid blocked_task_id FK
        timestamp created_at
    }
    
    PRIORITY_SUGGESTION {
        uuid id PK
        uuid workspace_id FK
        jsonb suggested_order_json
        string status
        timestamp created_at
        uuid approved_by_id FK
    }
```

### 5.2 Descrição das Entidades

#### TASK
Guarda o estado transacional das tarefas criadas por usuários no TaskFlow AI.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| **id** | UUID | PK, NOT NULL | Identificador único da tarefa. |
| **title** | VARCHAR(255) | NOT NULL | Título da tarefa. |
| **description** | TEXT | NULL | Descrição detalhada da tarefa em Markdown. |
| **status** | VARCHAR(50) | NOT NULL, DEFAULT 'backlog' | Status atual (backlog, todo, in_progress, review, done). |
| **deadline** | DATE | NULL | Prazo final para conclusão. |
| **story_points** | INT | NULL | Estimativa de esforço (fibonacci). |
| **assignee_id** | UUID | FK -> USER, NULL | Membro da equipe atribuído à tarefa. |
| **workspace_id** | UUID | FK -> WORKSPACE, NOT NULL | Workspace proprietária da tarefa. |
| **current_order** | INT | NOT NULL | Posição física no backlog. |
| **created_at** | TIMESTAMP | NOT NULL, DEFAULT now() | Data de criação. |
| **updated_at** | TIMESTAMP | NOT NULL, DEFAULT now() | Data de última atualização. |

### 5.3 Índices

| Tabela | Colunas | Tipo | Justificativa |
|--------|---------|------|---------------|
| `task` | `workspace_id, current_order` | B-tree | Otimizar a reordenação física de tarefas e leitura do backlog de um workspace específico. |
| `task` | `assignee_id` | B-tree | Otimizar listagem de tarefas de um desenvolvedor para cálculo de carga. |
| `task_dependency` | `parent_task_id, blocked_task_id` | B-tree (Unique) | Garantir integridade de dependências e buscas rápidas de bloqueios. |
| `priority_suggestion` | `workspace_id, status` | B-tree | Acesso rápido aos rascunhos de sugestões pendentes por workspace. |

### 5.4 Estratégia de Migração
- Utilizar **Alembic** (Python migration tool) integrado ao ciclo de CD.
- Migrações executadas em ambiente de staging antes de produção.
- Rollback plan: scripts automáticos de downgrade validados via testes automatizados localmente e em staging.

---

## 6. Segurança

### 6.1 Autenticação
- Implementado via **OAuth2 com fluxos de JWT (JSON Web Tokens)**.
- Token JWT expira em **15 minutos**. Refresh token armazenado em cookie seguro `HttpOnly, Secure, SameSite=Strict` com expiração de 7 dias.
- MFA obrigatório para administradores e opcional para desenvolvedores via TOTP (Autenticador Google/Microsoft).

### 6.2 Autorização
Adotado o modelo **RBAC (Role-Based Access Control)** no nível de Workspace:

| Role | Permissões | Escopo |
|------|------------|--------|
| **Workspace Admin / Owner** | Gerenciar usuários, faturamento, conexões de integrações e ativar Modo Autônomo. | Workspace completo. |
| **Tech Lead / PM** | Criar/editar tarefas, acionar e aplicar priorização IA, criar sprints. | Workspace completo. |
| **Developer / QA** | Mover tarefas de status, atribuir-se a tarefas, visualizar dashboards. | Workspace completo. |
| **Guest / Stakeholder** | Apenas visualização de dashboards e leitura de tarefas. | Workspace completo. |

### 6.3 Proteção de Dados
- **Dados em trânsito:** HTTPS obrigatório em 100% dos endpoints usando TLS 1.3. Criptografia no Application Load Balancer.
- **Dados em repouso:** Bancos de dados RDS Aurora e backups criptografados via KMS com chave AES-256 gerenciada pela AWS.
- **PII Handling:** Anonimização obrigatória antes de qualquer envio de payload para OpenAI/Anthropic. Nomes são trocados por hashes (ex: `USER-829b`) e e-mails de descrições são removidos por regex.

---

## 7. Observabilidade

### 7.1 Logs
- Formato padrão: **JSON Estruturado** enviado ao AWS CloudWatch Logs.
- Campos obrigatórios: `timestamp`, `request_id`, `user_id`, `workspace_id`, `action`, `level`, `execution_time_ms`.
- Níveis de logging: `DEBUG` em dev, `INFO` em produção para rotas padrão, `WARNING`/`ERROR` para exceções.

### 7.2 Métricas

| Métrica | Tipo | Labels | Alerta |
|---------|------|--------|--------|
| `http_requests_total` | Counter | method, path, status | Alerta se status `5xx` > 1% em 5 minutos |
| `http_request_duration_seconds` | Histogram | method, path | Alerta se p99 > 500ms por 10 minutos |
| `ai_prioritization_duration_seconds` | Histogram | model | Alerta se p99 > 3.5s por 10 minutos |
| `ai_prioritization_cost_total` | Counter | model | Alerta se custo diário exceder $100 USD |

### 7.3 Traces
- Instrumentação nativa da FastAPI e Celery com **OpenTelemetry** enviando dados para Datadog.
- Sampling rate: 100% para requisições de erro (HTTP 5xx / exceções Celery); 5% para requisições com sucesso.

### 7.4 Alertas e Runbooks

| Alerta | Condição | Severidade | Ação / Runbook |
|--------|----------|------------|----------------|
| **Elevada Taxa de Erro 5xx** | > 1% em 5 minutos | P1 | Reiniciar pods FastAPI / Check conexões de banco. |
| **Falha Crítica no Provedor IA** | 2 retries falhos seguidos no endpoint OpenAI | P1 | ML API executa chaveamento de modelo para Claude 3.5. |
| **Uso de CPU Aurora Database** | > 85% por 10 minutos | P2 | SRE escala RDS horizontalmente criando nova Read Replica. |

---

## 8. Escalabilidade e Performance

### 8.1 SLOs

| Métrica | Target |
|---------|--------|
| **Disponibilidade** | 99.9% de uptime mensal. |
| **Latência endpoints CRUD** | p50 < 80ms, p99 < 400ms. |
| **Latência priorização IA** | p50 < 1s, p99 < 3s. |
| **Tempo de resposta webhook GitHub** | p99 < 1.5s. |

### 8.2 Estratégia de Escalabilidade
- **FastAPI / Workers:** AWS ECS Fargate configurado com auto-scaling automático baseado em CPU e RAM (mínimo 2 pods, máximo 15 pods por serviço). Trigger de escala em > 65% de utilização.
- **RDS Database:** Multi-AZ ativado em Aurora PostgreSQL para alta disponibilidade com 1 instância Master para escritas e 1 instância réplica escalável para leituras analíticas do dashboard.
- **Cache:** Redis em cluster mode gerenciado via AWS ElastiCache.

---

## 9. Trade-offs e Alternativas Consideradas

### Decisão 1: Escolha do Banco de Dados Principal

| Opção | Prós | Contras | Veredicto |
|-------|------|---------|-----------|
| **PostgreSQL (Relacional)** | - Integridade referencial forte para dependências de tarefas.<br/>- Performance sólida em consultas relacionais complexas.<br/>- Suporte maduro a transações ACID. | - Escalar escritas horizontalmente é complexo (requer sharding no futuro). | **✅ Escolhida** |
| **MongoDB (NoSQL)** | - Schema flexível de tarefas.<br/>- Facilidade de escrita rápida. | - Falta de suporte nativo nativo de alta performance para joins complexos de grafos de dependências de tarefas. | **❌ Rejeitada** (Risco de queries lentas ao processar bloqueios em árvore) |

### Decisão 2: Arquitetura Monolítica Modulada vs Microserviços

- **Veredicto:** **Escolha do Monolito Modulado**.
  - *Prós:* Menor overhead operacional para equipe pequena (10 pessoas), facilidade de refatoração rápida, custo inicial de infraestrutura reduzido.
  - *Contras:* Aumento do tempo de build conforme codebase cresce.
  - *Mitigação:* Estruturar o código com separação clara de módulos (IA, tasks, users, integrations) para facilitar separação futura caso necessário.

### Dívida Técnica Aceita
- **Mapeamento bidirecional incompleto do Jira na importação:** Sincronização em tempo real de comentários Jira -> TaskFlow AI não estará disponível na v1. 
  - *Justificativa:* Reduz tempo de desenvolvimento de integrações complexas de webhook de terceiros para o MVP.
  - *Plano de resolução:* Implementar sync a cada 3 horas via background worker. v2 trará webhook ativo.

---

## 10. Plano de Rollout

### 10.1 Fases

| Fase | Escopo | Duração | Critério de Avanço |
|------|--------|---------|-------------------|
| **1. Alpha Interno** | Testes na própria equipe de engenharia do TaskFlow. | 2 semanas | Zero bugs críticos (P1). |
| **2. Beta Fechado** | Lançamento para as 50 empresas selecionadas. | 3 semanas | Taxa de aceitação da IA ≥ 75%. |
| **3. GA (Geral)** | Abertura do SaaS para o público geral. | Contínuo | Monitoramento ativo de custos de API. |

### 10.2 Feature Flags

| Flag | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `enable-autonomous-mode` | Boolean | `false` | Habilita o opt-in do Modo Autônomo da IA no console do Admin. |
| `use-claude-primary` | Boolean | `false` | Redireciona requests de priorização principais para o Claude da Anthropic (teste de performance e custo). |

### 10.3 Rollback Plan
- **Trigger:** Aumento de erros HTTP 5xx em produção > 1.5% pós-release.
- **Ação:** Reverter deploy na AWS via Pipeline do GitHub Actions em 1 clique (tempo estimado de rollback: 3 minutos).

---

## 11. Estratégia de Testes

- **Unitários:** Cobertura mínima de 85% da lógica de priorização e cálculo de pesos e dependências no Backend via `pytest`.
- **Integração:** Validação de payload de APIs locais e queries complexas usando base de dados Postgres limpa em Docker a cada run de CI.
- **E2E:** Happy paths do board Kanban e geração de relatórios testados no Next.js usando `Playwright`.
- **Carga:** Testes de estresse com `k6` simulando 2.000 requisições simultâneas em endpoints CRUD e 50 requisições simultâneas no endpoint de IA.

---

## Apêndice A: Seções para Sistemas com IA/LLM

### A.1 Estratégia RAG
A priorização de tarefas não é feita em contexto aberto, mas baseada em um algoritmo RAG leve que provê dados estruturados de contexto ao LLM.
- **Dados coletados:** Sprints recentes finalizados (velocidade real da equipe), labels mais frequentes por assignee, e objetivos cadastrados do roadmap de negócio.
- **Context injection:** Injeção direta no prompt de sistema em formato estruturado (Markdown e JSON), limitando o contexto aos últimos 3 sprints para evitar estouro da context window.

### A.2 Gestão de Prompts
- **Armazenamento:** Prompts são versionados como código no diretório `/prompts/` do backend FastAPI (ex: `/prompts/prioritize_backlog_v1.txt`).
- **Testes de Regressão:** Suite automatizada de 200 cenários históricos salvos em `/tests/golden_sets/`. O teste compara o output do prompt alterado com o resultado experiente do golden set. Variações semânticas bruscas no ranking geram falha na CI.

### A.3 Fallbacks
Em caso de indisponibilidade da OpenAI (error rate > 5% ou timeout > 3s):
1. **Fallback Automático (Nível 1):** Backend chaveia rota para Anthropic API utilizando Claude 3.5 Sonnet.
2. **Fallback Determinístico (Nível 2):** Caso ambos estejam indisponíveis, a API executa um algoritmo determinístico baseado no framework WSJF (Weighted Shortest Job First) com pesos pré-definidos no banco do cliente, avisando o usuário na UI com banner amarelo de "Indisponibilidade Temporária da IA".

### A.4 Custo Projetado

Com base em um backlog médio de 80 tarefas e equipe de 8 desenvolvedores:

| Cenário | Workspaces Ativas | Requests/dia | Custo por Request (avg) | Custo Mensal |
|---------|-------------------|--------------|-------------------------|--------------|
| **Baixo (Lançamento)** | 100 | 200 | $0.015 | $90.00 USD |
| **Médio (3 meses pós)**| 1.000 | 2.500 | $0.015 | $1,125.00 USD |
| **Alto (Previsão v1.5)**| 5.000 | 15.000 | $0.015 | $6,750.00 USD |

### A.5 Logging de IA
- **Entradas e Saídas:** São salvas no banco de dados na tabela `priority_suggestion` usando criptografia no campo `suggested_order_json` para preservar PII caso vazado.
- **Metadados:** Tempo de execução da LLM, tokens de input, tokens de output, ID do request da OpenAI, e modelo utilizado são gravados na tabela para auditoria e controle de custos de billing por workspace.

### A.6 Avaliação de Saídas
O ML Engineer avalia quinzenalmente uma amostra aleatória de 5% das priorizações rejeitadas pelos usuários. O score de aceitação (sugestões aceitas / sugestões totais) é exibido no dashboard operacional de saúde do sistema com meta de manter-se acima de **75%**.
