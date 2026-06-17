# PRD: TaskFlow AI

> **Autor:** Marina Santos & Ricardo Oliveira | **Data:** 06/06/2026 | **Versão:** 1.0 | **Status:** Em Revisão

---

## 1. Resumo Executivo

Equipes de tecnologia perdem em média 4,5 horas por semana priorizando tarefas manualmente — tempo que poderia ser investido em trabalho de alto impacto. O **TaskFlow AI** resolve esse problema utilizando inteligência artificial para analisar deadlines, dependências entre tarefas e contexto de projeto, priorizando automaticamente o backlog da equipe com critérios objetivos e transparentes. O impacto esperado é uma **redução de 30% no tempo gasto com triagem e priorização**, liberando aproximadamente 1,35 horas por semana por membro da equipe para trabalho produtivo e reduzindo significativamente entregas atrasadas.

---

## 2. Problema

### 2.1 Descrição do Problema

Equipes de engenharia de software gastam tempo desproporcional decidindo **o que fazer** versus **fazendo**. Sprint plannings que deveriam durar 30 minutos se estendem por 2 horas. Tech leads e product managers passam manhãs inteiras reorganizando backlogs com base em intuição e pressão de stakeholders, sem critérios objetivos de priorização. A falta de visibilidade sobre dependências entre tarefas causa bloqueios inesperados, retrabalho em funcionalidades de baixa prioridade e entregas atrasadas em funcionalidades críticas. O resultado é uma equipe que trabalha muito, mas entrega pouco valor no tempo certo — gerando frustração, desalinhamento com stakeholders e burnout generalizado.

### 2.2 Evidências

- **Pesquisa interna TaskFlow Labs (Q1 2026):** Entrevistas com 500 Product Managers e Tech Leads de empresas de tecnologia brasileiras revelaram que **78% consideram a priorização de backlog a atividade mais frustrante da semana**, e **63% admitem que mudam prioridades mais de 3 vezes por sprint** por falta de critérios claros.
- **Relatório "State of Engineering Productivity 2025" (DevMetrics Inc.):** Equipes sem ferramentas de priorização automatizada gastam em média **4,5 horas por semana** por pessoa em triagem, contra **1,8 horas** em equipes com suporte de IA — uma diferença de 60%.
- **Dados internos de beta testers:** 12 equipes que testaram o protótipo do TaskFlow AI por 4 semanas reportaram redução média de **35% no tempo de sprint planning** e aumento de **22% na taxa de conclusão de tarefas dentro do sprint**.
- **Relatório Gartner "AI-Augmented Software Engineering" (2025):** Prevê que até 2028, **75% das equipes de desenvolvimento** utilizarão alguma forma de IA para priorização e planejamento, contra apenas 15% em 2025.

### 2.3 Impacto de Não Resolver

Se o problema não for endereçado:

- **Perda de competitividade:** Concorrentes que adotarem IA para priorização entregarão valor ao mercado mais rápido, capturando market share enquanto equipes manuais perdem velocidade.
- **Turnover elevado:** A pesquisa TaskFlow Labs indicou que **42% dos desenvolvedores** citam "processos de priorização ineficientes" como um dos top 3 motivos para considerar trocar de empresa. O custo médio de reposição de um engenheiro sênior é de R$80.000–R$120.000.
- **Custos de retrabalho:** Equipes que priorizam por intuição têm taxa de retrabalho 3x maior que equipes com critérios objetivos, representando um custo estimado de R$15.000/mês para uma equipe de 8 pessoas.
- **Desalinhamento com negócio:** Sem priorização objetiva, equipes tendem a trabalhar no que é mais recente (viés de recência) ou mais barulhento (pressão de stakeholders), em vez do que gera mais valor para o negócio.

---

## 3. Objetivo

**Objetivo Principal:** Reduzir o tempo gasto por equipes de engenharia em triagem e priorização de tarefas em pelo menos 30%, aumentando a assertividade da priorização e a predictabilidade de entregas.

**Objetivos SMART:**

1. **Específico:** Automatizar a priorização de tarefas em backlogs de equipes de engenharia utilizando IA que analisa deadlines, dependências e contexto do projeto.
2. **Mensurável:** Reduzir o tempo médio de triagem de 4,5h/semana para ≤ 3,15h/semana por membro da equipe, alcançar taxa de aceitação da priorização IA ≥ 75%, e reduzir tasks atrasadas em ≥ 20%.
3. **Atingível:** Baseado nos resultados do beta test com 12 equipes que já demonstraram redução de 35% no tempo de sprint planning, o objetivo de 30% é conservador e realista.
4. **Relevante:** Alinhado com a estratégia da empresa de se posicionar como líder em ferramentas de produtividade com IA para equipes de engenharia no mercado brasileiro e latino-americano.
5. **Temporal:** Atingir todas as métricas dentro de 3 meses após o lançamento público (meta: Dezembro 2026), com NPS > 70 em 6 meses (meta: Março 2027).

---

## 4. Usuários Alvo

### 4.1 Persona Primária

- **Nome:** Marina Santos
- **Perfil:** Tech Lead, 32 anos, graduada em Ciência da Computação pela UNICAMP. Trabalha em uma startup de fintech em São Paulo com 45 funcionários. Gerencia uma equipe de 8 desenvolvedores (5 backend, 2 frontend, 1 QA). Usa Jira, GitHub e Slack diariamente. Tem 7 anos de experiência em desenvolvimento e 2 como líder técnica.
- **Necessidade principal:** Priorizar o backlog da equipe de forma rápida, objetiva e justificável, eliminando debates subjetivos em sprint plannings e garantindo que a equipe trabalhe sempre nas tarefas de maior impacto.
- **Jornada atual:** Marina passa toda segunda-feira de manhã (2-3 horas) revisando o backlog no Jira, tentando equilibrar urgência, importância e dependências. Usa uma planilha pessoal no Google Sheets com fórmulas de pontuação RICE que precisa atualizar manualmente. Nas sprint plannings (quartas-feiras, 1-2 horas), frequentemente discute prioridades com o PM e a equipe sem consenso claro. Ao final, muitas decisões são tomadas "no feeling" e renegociadas durante o sprint.

### 4.2 Persona Secundária

- **Nome:** Ricardo Oliveira
- **Perfil:** Product Manager, 28 anos, formado em Engenharia de Produção pela USP com MBA em Product Management. Trabalha na mesma fintech que Marina, responsável por 2 subagents (16 devs total). Reporta para o VP de Produto e apresenta prioridades para stakeholders de negócio semanalmente. Tem 4 anos de experiência em produto.
- **Necessidade principal:** Ter dados objetivos e rastreáveis para justificar prioridades perante stakeholders de negócio (CEO, diretores), reduzindo conflitos políticos na definição de roadmap e demonstrando que as decisões de priorização são baseadas em critérios mensuráveis.
- **Jornada atual:** Ricardo mantém um roadmap no Productboard que é atualizado manualmente toda semana. Gasta cerca de 3 horas por semana em reuniões com stakeholders defendendo prioridades com argumentos qualitativos ("acho que X é mais importante que Y"). Frequentemente perde essas discussões para quem fala mais alto, resultando em mudanças de prioridade que frustram a equipe de engenharia. Não possui métricas objetivas de priorização além do framework RICE que aplica inconsistentemente.

---

## 5. Hipóteses

| #  | Hipótese | Como Validar | Status |
|----|----------|--------------|--------|
| H1 | Tech leads aceitarão sugestões de priorização de uma IA se a explicação dos critérios for transparente e clara (exibindo fatores como deadline, dependências e complexidade). | A/B test: grupo com explicação detalhada vs. grupo com apenas a sugestão. Medir taxa de aceitação em cada grupo. Meta: ≥ 75% de aceitação no grupo com explicação. | ⬜ Não testada |
| H2 | O modo sugestão (IA sugere, humano confirma) terá adoção ≥ 3x maior que o modo autônomo (IA decide sozinha) nos primeiros 3 meses, à medida que usuários constroem confiança no sistema. | Análise de dados de uso: comparar % de usuários em cada modo ao longo de 12 semanas. Realizar pesquisa qualitativa quinzenal com 20 usuários de cada grupo. | ⬜ Não testada |
| H3 | A qualidade da priorização IA será percebida como "boa" ou "excelente" por ≥ 70% dos usuários quando o sistema tiver pelo menos 30 dias de dados históricos da equipe (tarefas anteriores, velocidade, padrões de conclusão). | Pesquisa in-app (CSAT) após 30, 60 e 90 dias de uso. Correlacionar NPS/CSAT com volume de dados históricos disponíveis. Comparar com golden set de priorizações feitas por Tech Leads experientes. | ⬜ Não testada |
| H4 | Equipes que integram o TaskFlow AI com GitHub/GitLab terão taxa de conclusão de tasks ≥ 15% maior que equipes sem integração, pois o sistema poderá identificar bloqueios e dependências automaticamente via PRs e commits. | Cohort analysis: equipes com integração vs. sem integração. Medir taxa de conclusão de tasks por sprint em ambos os grupos ao longo de 8 semanas. | ⬜ Não testada |
| H5 | Product Managers que usam o dashboard de métricas de equipe para apresentações a stakeholders reduzirão em ≥ 40% o tempo gasto em preparação de relatórios de progresso semanais. | Survey pré e pós-adoção: medir tempo auto-reportado de preparação de relatórios. Complementar com dados de uso do dashboard (frequência de acesso, exports, compartilhamentos). | ⬜ Não testada |

---

## 6. Requisitos Funcionais

### RF-001: Criar e Gerenciar Tarefas

- **Como** Tech Lead, **quero** criar, editar, arquivar e organizar tarefas com campos customizáveis (título, descrição, deadline, labels, assignee, estimativa de esforço, dependências), **para que** eu tenha uma visão completa e atualizada de todo o trabalho da minha equipe em um único lugar.
- **Critérios de Aceitação:**
  - [ ] Usuário pode criar tarefa com campos obrigatórios (título, descrição) e opcionais (deadline, labels, assignee, estimativa, dependências, prioridade manual)
  - [ ] Tarefas suportam Markdown na descrição com preview em tempo real
  - [ ] Usuário pode criar sub-tarefas vinculadas a uma tarefa pai (até 3 níveis de profundidade)
  - [ ] Tarefas podem ser organizadas em boards (Kanban), listas ou timeline (Gantt simplificado)
  - [ ] Busca full-text por título e descrição com filtros combinados (label, assignee, status, deadline, prioridade)
  - [ ] Drag-and-drop funcional em todas as visualizações para reordenação manual
- **Prioridade:** 🔴 Must Have

### RF-002: Auto-Priorização por IA

- **Como** Tech Lead, **quero** que a IA analise automaticamente todas as tarefas do backlog e sugira uma ordenação de prioridade baseada em deadlines, dependências entre tarefas, complexidade estimada e contexto do sprint atual, **para que** eu economize horas de análise manual e tenha uma priorização objetiva e consistente.
- **Critérios de Aceitação:**
  - [ ] A IA gera uma lista priorizada do backlog completo em até 3 segundos (p99) para backlogs de até 500 tarefas
  - [ ] Cada tarefa priorizada exibe uma explicação textual do racional da priorização (ex: "Priorizada por: deadline em 3 dias + bloqueia 2 outras tarefas + alta complexidade estimada")
  - [ ] A priorização considera pelo menos 5 fatores: deadline, dependências, complexidade estimada, impacto no sprint goal, e histórico de atrasos do assignee
  - [ ] O usuário pode aceitar, rejeitar ou ajustar a sugestão da IA com um clique, e o feedback é usado para melhorar priorizações futuras
  - [ ] A re-priorização acontece automaticamente quando uma nova tarefa é adicionada, uma deadline muda, ou uma dependência é resolvida
- **Prioridade:** 🔴 Must Have

### RF-003: Dashboard de Visão Geral com Métricas de Equipe

- **Como** Product Manager, **quero** visualizar em um dashboard métricas como velocidade do sprint, taxa de conclusão, distribuição de carga por membro, e previsão de entrega baseada em dados históricos, **para que** eu possa comunicar progresso para stakeholders com dados concretos e identificar gargalos antes que causem atrasos.
- **Critérios de Aceitação:**
  - [ ] Dashboard exibe pelo menos 6 widgets: velocidade do sprint (burndown), taxa de conclusão (% de tasks concluídas vs. planejadas), distribuição de carga por membro, previsão de entrega (data estimada com intervalo de confiança), tarefas bloqueadas, e tendência de atrasos
  - [ ] Todos os gráficos atualizam em tempo real (polling máximo de 30 segundos) sem necessidade de refresh manual
  - [ ] Dashboard é exportável em PDF e PNG para uso em apresentações
  - [ ] Filtros por período (sprint, semana, mês, trimestre), equipe e membro individual
  - [ ] Comparativo histórico: sprint atual vs. média dos últimos 5 sprints
- **Prioridade:** 🔴 Must Have

### RF-004: Notificações Inteligentes de Reprioritização

- **Como** Tech Lead, **quero** receber notificações quando a IA detectar mudanças significativas que afetam a priorização (nova tarefa urgente, deadline alterada, bloqueio identificado, membro da equipe sobrecarregado), **para que** eu possa agir rapidamente sem precisar monitorar o board constantemente.
- **Critérios de Aceitação:**
  - [ ] Notificações são entregues via in-app (bell icon), email e integração Slack/Teams
  - [ ] Cada notificação inclui: o que mudou, por quê a IA está sugerindo reprioritização, e ação recomendada com botão de "aceitar" direto na notificação
  - [ ] Usuário pode configurar frequência (imediata, digest diário, digest semanal) e canais preferidos por tipo de notificação
  - [ ] Sistema agrupa notificações relacionadas para evitar notification fatigue (máximo 5 notificações/hora por usuário, exceto alertas críticos)
  - [ ] Notificações de bloqueio incluem sugestão de tarefa alternativa para o membro bloqueado
- **Prioridade:** 🔴 Must Have

### RF-005: Integração com GitHub/GitLab

- **Como** Tech Lead, **quero** vincular Pull Requests e branches do GitHub ou GitLab às tarefas do TaskFlow AI, **para que** o sistema detecte automaticamente quando uma tarefa está em progresso (branch criada), em review (PR aberto), ou concluída (PR mergeado), eliminando a atualização manual de status.
- **Critérios de Aceitação:**
  - [ ] Integração via OAuth com GitHub e GitLab (self-hosted e cloud)
  - [ ] Vinculação automática de PRs a tarefas por convenção de branch naming (ex: `taskflow-123/feature-name`) ou menção no PR description (`TaskFlow: #123`)
  - [ ] Status da tarefa atualiza automaticamente: branch criada → "Em Progresso", PR aberto → "Em Review", PR mergeado → "Concluída"
  - [ ] Dashboard exibe link direto para o PR e status do CI/CD (passing/failing) ao lado da tarefa
  - [ ] Webhook bidirecionais: ações no GitHub/GitLab refletem no TaskFlow e vice-versa (comentários sincronizados)
- **Prioridade:** 🟡 Should Have

### RF-006: Modo Sugestão vs. Modo Autônomo

- **Como** Tech Lead, **quero** escolher entre um "modo sugestão" (a IA sugere priorização e eu confirmo) e um "modo autônomo" (a IA re-prioriza automaticamente sem minha intervenção), **para que** eu possa começar com supervisão total e, à medida que confio no sistema, delegar mais autonomia à IA.
- **Critérios de Aceitação:**
  - [ ] Modo sugestão (padrão): IA gera priorização sugerida que fica em estado "pendente" até o Tech Lead aprovar, rejeitar ou modificar. Priorização atual não muda até aprovação.
  - [ ] Modo autônomo (opt-in): IA aplica re-priorização automaticamente com registro de auditoria completo (antes vs. depois, motivo, timestamp). Requer confirmação do admin da workspace para ativar.
  - [ ] Transição entre modos pode ser feita a qualquer momento sem perda de dados ou histórico
  - [ ] No modo autônomo, ações de alto impacto (mover tarefa para "cancelada", remover assignee, alterar deadline) ainda requerem confirmação humana
  - [ ] Log de auditoria acessível com todas as decisões da IA, filtráveis por data, tarefa e tipo de ação
- **Prioridade:** 🟢 Could Have

### RF-007: Importação e Exportação de Dados

- **Como** Tech Lead, **quero** importar tarefas existentes de ferramentas como Jira, Trello e Asana via CSV ou API, e exportar meus dados a qualquer momento, **para que** eu possa migrar facilmente sem perder histórico e não fique preso à plataforma (lock-in).
- **Critérios de Aceitação:**
  - [ ] Importação suporta CSV (com mapeamento de colunas), JSON e API direta do Jira (Cloud e Server)
  - [ ] Importação preserva: título, descrição, status, assignee, labels, datas de criação/conclusão, e comentários
  - [ ] Exportação completa em CSV, JSON e formato Jira-compatible para migração reversa
  - [ ] Importação de até 10.000 tarefas em uma única operação com progress bar e relatório de erros
- **Prioridade:** 🟡 Should Have

---

## 7. Requisitos Não-Funcionais

| ID      | Categoria       | Requisito | Métrica |
|---------|-----------------|-----------|---------|
| RNF-001 | Performance     | Todos os endpoints da API devem responder dentro do SLO definido para garantir experiência fluida do usuário | p99 < 500ms para qualquer endpoint CRUD; p99 < 3s para endpoints de priorização IA |
| RNF-002 | Segurança       | Autenticação multi-fator (MFA) obrigatória para admins, opcional para membros. Dados criptografados em trânsito (TLS 1.3) e em repouso (AES-256). Tokens JWT com rotação automática a cada 15 minutos. | MFA ativo para 100% dos admins; zero dados em texto plano em banco ou logs |
| RNF-003 | Acessibilidade  | Interface deve ser utilizável por pessoas com deficiência visual, motora e cognitiva, seguindo as diretrizes internacionais de acessibilidade | WCAG 2.1 AA em 100% das páginas; score Lighthouse Accessibility ≥ 95 |
| RNF-004 | Conformidade    | Sistema deve estar em conformidade com a Lei Geral de Proteção de Dados (LGPD), incluindo consentimento, portabilidade e direito ao esquecimento | Implementação completa de consent management; API de portabilidade (export) e exclusão de dados em até 72h |
| RNF-005 | Disponibilidade | Sistema deve estar disponível continuamente com janelas de manutenção planejadas mínimas | 99,9% uptime mensal (máximo 43 minutos de downtime/mês); zero downtime deploys |
| RNF-006 | Escalabilidade  | Arquitetura deve suportar crescimento orgânico de usuários sem degradação de performance perceptível | Suportar 10.000 usuários simultâneos; auto-scaling horizontal de 2 a 20 instâncias; banco de dados com sharding por workspace |

---

## 8. Métricas de Sucesso

| Métrica | Baseline Atual | Meta | Prazo |
|---------|---------------|------|-------|
| Tempo médio semanal de triagem e priorização por membro | 4,5 horas/semana | ≤ 3,15 horas/semana (redução de 30%) | 3 meses após lançamento (Dez 2026) |
| NPS (Net Promoter Score) | N/A (produto novo) | > 70 | 6 meses após lançamento (Mar 2027) |
| Taxa de aceitação da priorização IA | N/A (produto novo) | ≥ 75% das sugestões aceitas sem modificação | 3 meses após lançamento (Dez 2026) |
| Taxa de tarefas atrasadas por sprint | 35% (média do mercado, pesquisa DevMetrics 2025) | ≤ 28% (redução de 20%) | 3 meses após lançamento (Dez 2026) |
| Retenção mensal (MAU/MAU mês anterior) | N/A (produto novo) | ≥ 85% retenção mensal | 6 meses após lançamento (Mar 2027) |
| Tempo médio de sprint planning | 90 minutos (média reportada em pesquisa interna) | ≤ 60 minutos (redução de 33%) | 3 meses após lançamento (Dez 2026) |

---

## 9. Fora de Escopo

- ❌ **Chat e mensageria entre membros da equipe** — O TaskFlow AI não é uma ferramenta de comunicação. Integrações com Slack/Teams cobrem essa necessidade. Um módulo de chat nativo diluiria o foco do produto e competiria com ferramentas estabelecidas.
- ❌ **Time tracking / controle de ponto** — Funcionalidade de RH que foge ao propósito do produto. Ferramentas como Toggl e Clockify já resolvem isso. Pode ser avaliado para v2 se houver demanda comprovada (> 30% dos usuários solicitarem).
- ❌ **Integração com ERPs (SAP, Oracle, TOTVS)** — Complexidade de integração desproporcional ao valor gerado para o público-alvo (equipes de engenharia). Seria relevante apenas para enterprise com > 500 funcionários, que não é o ICP da v1.
- ❌ **App mobile nativo (iOS/Android)** — A v1 será exclusivamente web responsivo, otimizado para uso em desktop e tablet. Um PWA será disponibilizado para acesso mobile básico. Apps nativos serão avaliados para v2 com base em dados de uso mobile.
- ❌ **Relatórios de RH e people analytics** — O dashboard de métricas foca em produtividade da equipe e progresso de entregas, não em avaliação individual de performance para fins de RH. Dados individuais são apresentados apenas para balanceamento de carga, nunca para ranking ou avaliação.

---

## 10. Riscos e Dependências

| #  | Risco/Dependência | Tipo | Probabilidade | Impacto | Mitigação |
|----|-------------------|------|---------------|---------|-----------|
| R1 | Qualidade da priorização IA pode não atender expectativas dos usuários, gerando desconfiança e abandono da feature principal do produto | Risco | Alta | Alto | (1) Lançar inicialmente apenas no modo sugestão para construir confiança gradual; (2) Implementar explicabilidade detalhada de cada decisão de priorização; (3) Manter golden set de 200 cenários de teste com avaliação humana contínua; (4) Coletar feedback granular (thumbs up/down + comentário) em cada sugestão para fine-tuning |
| R2 | Adoção lenta por resistência a mudança — Tech Leads podem preferir manter processos manuais estabelecidos por inércia ou desconfiança em IA | Risco | Média | Alto | (1) Oferecer onboarding assistido com Customer Success dedicado para os primeiros 50 clientes; (2) Criar programa de "Early Adopters" com benefícios (12 meses grátis) para gerar cases de sucesso; (3) Implementar modo de "shadow" onde a IA roda em paralelo sem afetar o fluxo existente por 2 semanas |
| R3 | Custo de API de IA (OpenAI/Anthropic) pode escalar além do orçamento projetado à medida que o número de usuários e re-priorizações cresce | Risco | Média | Médio | (1) Implementar caching agressivo de priorizações (invalidar apenas quando dados de input mudam); (2) Usar modelo mais leve (GPT-4o-mini/Claude Haiku) para re-priorizações incrementais e modelo completo apenas para priorização full do backlog; (3) Fallback para algoritmo determinístico (WSJF — Weighted Shortest Job First) se custo exceder budget em 20% |
| R4 | Concorrência (Linear, Jira, Asana) pode lançar feature similar de priorização IA antes do TaskFlow AI, diluindo o diferencial competitivo | Risco | Baixa | Alto | (1) Acelerar time-to-market priorizando MVP com foco na qualidade da explicabilidade (diferencial vs. "caixa-preta"); (2) Construir moat via dados — quanto mais uma equipe usa, melhor a priorização fica; (3) Investir em integrações abertas para ser complementar a ferramentas existentes em vez de substituto direto |
| D1 | API do GitHub e GitLab para integração de PRs, branches e webhooks | Dependência | - | - | Equipe de backend (responsável: Lucas Ferreira, Tech Lead Backend). Manter fallback manual (vinculação por link) caso APIs estejam instáveis. Monitorar status pages do GitHub/GitLab via automatização. |
| D2 | Provedor de IA — OpenAI (GPT-4o) como modelo primário, Anthropic (Claude 3.5 Sonnet) como fallback | Dependência | - | - | Equipe de IA/ML (responsável: Ana Beatriz Costa, ML Engineer). Abstrair chamadas de modelo com camada de abstração que permite trocar provedor em < 1 hora. Manter contrato com ambos os provedores. Budget mensal aprovado: R$15.000 (OpenAI) + R$5.000 (Anthropic reserva). |
| D3 | Infraestrutura cloud — AWS (ECS, RDS, ElastiCache) para produção | Dependência | - | - | Equipe de DevOps (responsável: Carlos Eduardo Lima, SRE). Conta AWS já provisionada. IaC via Terraform com ambientes de staging e produção isolados. |

---

## 11. Critérios de Aceitação Globais

- [ ] Todos os endpoints da API respondem em p99 < 500ms (exceto endpoints de IA que devem responder em p99 < 3s), verificado por testes de carga com k6 simulando 10.000 usuários simultâneos
- [ ] Cobertura de testes automatizados ≥ 80% em todas as camadas (unitários, integração e E2E), com CI/CD bloqueando merge em caso de queda de cobertura
- [ ] Score de acessibilidade Lighthouse ≥ 95 em todas as páginas públicas e autenticadas, validado por audit automatizado no pipeline de CI
- [ ] Zero vulnerabilidades de severidade "Alta" ou "Crítica" em scan SAST (SonarQube) e DAST (OWASP ZAP) antes do lançamento, com evidência de remediação documentada
- [ ] Sistema de consentimento LGPD implementado e funcional: opt-in para coleta de dados, API de portabilidade (exportação) e exclusão completa de dados do usuário em até 72 horas após solicitação
- [ ] Documentação técnica completa (API docs via OpenAPI 3.1, guia de integração, runbook de operações) e documentação de usuário (help center com ≥ 20 artigos cobrindo todos os fluxos principais) publicadas antes do lançamento
- [ ] Smoke tests automatizados executados com sucesso em ambiente de produção em até 15 minutos após cada deploy, com rollback automático em caso de falha

---

## 12. Cronograma Estimado

| Fase | Início | Fim | Responsável |
|------|--------|-----|-------------|
| Discovery & Pesquisa de Usuário | 01/07/2026 | 14/07/2026 | Ricardo Oliveira (PM) e Ana Beatriz Costa (UX Research) |
| Design (UX/UI) | 15/07/2026 | 04/08/2026 | Fernanda Rodrigues (Product Designer) e Thiago Mendes (UI Designer) |
| Desenvolvimento — Sprint 1-2 (Infra + CRUD de Tasks) | 05/08/2026 | 18/08/2026 | Marina Santos (Tech Lead) e equipe de engenharia (8 devs) |
| Desenvolvimento — Sprint 3-4 (IA Priorização + Dashboard) | 19/08/2026 | 01/09/2026 | Marina Santos e Ana Beatriz Costa (ML Engineer) |
| Desenvolvimento — Sprint 5-6 (Notificações + Integração GitHub) | 02/09/2026 | 15/09/2026 | Marina Santos e equipe de engenharia |
| Desenvolvimento — Sprint 7-8 (Modo Sugestão/Autônomo + Import/Export) | 16/09/2026 | 29/09/2026 | Marina Santos e equipe de engenharia |
| Testes (QA, carga, segurança, acessibilidade) | 30/09/2026 | 13/10/2026 | Juliana Almeida (QA Lead) e Carlos Eduardo Lima (SRE) |
| Beta fechado (50 equipes) | 14/10/2026 | 27/10/2026 | Ricardo Oliveira (PM) e Customer Success |
| Ajustes pós-beta e hardening | 28/10/2026 | 03/11/2026 | Marina Santos e equipe de engenharia |
| Lançamento público (GA) | 04/11/2026 | 10/11/2026 | Ricardo Oliveira (PM) e equipe de Marketing |

---

## Apêndice A: Seções para Projetos com IA/LLM

### A.1 Intent Scope

- **Intenções suportadas:**
  - **Priorização de tarefas:** Analisar backlog completo e gerar ordenação baseada em múltiplos fatores (deadline, dependências, complexidade, sprint goal, histórico)
  - **Sugestão de deadline:** Para tarefas sem deadline definida, sugerir uma data com base na complexidade estimada, velocidade da equipe e carga atual
  - **Identificação de bloqueios:** Detectar dependências circulares, tarefas bloqueadas sem responsável designado, e gargalos de carga por membro
  - **Estimativa de esforço:** Sugerir story points ou horas com base em tarefas históricas similares (título, descrição, labels) da mesma equipe
  - **Detecção de anomalias:** Alertar quando uma tarefa está parada há mais tempo que a média histórica, ou quando a velocidade do sprint está significativamente abaixo do previsto

- **Intenções fora de escopo (com fallback definido):**
  - **Geração ou revisão de código:** Fallback → Exibir mensagem: "O TaskFlow AI foca em gestão e priorização. Para assistência com código, recomendamos [GitHub Copilot / Cursor]."
  - **Deploy e operações de infraestrutura:** Fallback → Exibir mensagem: "Para deploy, consulte seu pipeline de CI/CD configurado."
  - **Revisão de Pull Requests:** Fallback → Redirecionar para integração GitHub/GitLab com link direto para o PR
  - **Respostas a perguntas genéricas não relacionadas a tarefas:** Fallback → Exibir mensagem: "Posso ajudar com priorização e gestão de tarefas. Para outras perguntas, consulte o help center."

### A.2 Data Boundary

- **Dados permitidos nos prompts:**
  - Títulos de tarefas
  - Descrições de tarefas (sanitizadas — vide bloqueio abaixo)
  - Datas de criação, deadline e conclusão
  - Labels e tags
  - Dependências entre tarefas (IDs)
  - Estimativas de esforço (story points ou horas)
  - Status de tarefas (backlog, em progresso, concluída, etc.)
  - Métricas agregadas da equipe (velocidade média, taxa de conclusão — nunca individualizadas por nome)
  - Nome do sprint e sprint goal

- **Dados BLOQUEADOS (NUNCA enviados ao modelo):**
  - **Nomes reais de pessoas** (substituídos por IDs anonimizados: `MEMBER-001`, `MEMBER-002`). Mapeamento mantido apenas no backend, nunca exposto ao modelo.
  - **Endereços de email** — Removidos via regex antes do envio ao modelo. Padrão: `[EMAIL_REDACTED]`.
  - **Dados financeiros** (valores de contrato, salários, custos de projeto) — Removidos via NER (Named Entity Recognition) + regex.
  - **Código-fonte** — Mesmo que presente em descrições de tarefas, trechos de código são substituídos por `[CODE_BLOCK_REDACTED]` antes do envio.
  - **Tokens, secrets e credenciais** — Detectados via regex (padrões de API keys, JWTs, connection strings) e substituídos por `[SECRET_REDACTED]`.
  - **Dados de saúde, origem étnica ou informações sensíveis sob LGPD** — Bloqueados por política de sanitização e auditados trimestralmente.

### A.3 Evidence Requirements

- **Citações obrigatórias:** Toda decisão de priorização da IA deve incluir uma explicação estruturada com os fatores considerados e seus pesos relativos. Formato padrão:
  ```
  Priorização: #1 (de 47 tarefas)
  Fatores:
  - Deadline: em 2 dias (peso: 35%)
  - Dependências: bloqueia 3 outras tarefas (peso: 30%)
  - Sprint Goal: alinhada com objetivo principal do sprint (peso: 20%)
  - Complexidade: baixa (2 story points) — rápida de finalizar (peso: 15%)
  ```
- **Nível de confiança mínimo:** O sistema interno deve ter score de confiança ≥ 0.7 (em escala de 0 a 1) para emitir uma sugestão. Para scores entre 0.5 e 0.7, a sugestão é marcada como "baixa confiança" com alerta visual. Para scores < 0.5, a sugestão não é exibida e o sistema solicita mais dados.
- **Tratamento de erros/alucinações:** Se o modelo retornar uma priorização que referencia tarefas inexistentes (IDs não encontrados no banco) ou fatores inconsistentes (ex: citar deadline para tarefa sem deadline), o sistema descarta a resposta, registra o incidente no log de qualidade, e faz retry com prompt reformulado. Após 2 retries falhados, fallback para algoritmo determinístico WSJF com notificação ao usuário: "Priorização assistida por IA temporariamente indisponível. Usando priorização por critérios padrão (WSJF)."

### A.4 Cost & Latency Budgets

- **Custo máximo por request:** $0,02 (média). Priorizações full de backlog grande (> 200 tarefas) podem chegar a $0,08 por request. Re-priorizações incrementais (1-5 tarefas alteradas) devem custar ≤ $0,005.
- **SLO de latência:** p99 < 3 segundos para priorização completa de backlog de até 500 tarefas. p50 < 1 segundo. Para backlogs > 500 tarefas, exibir progress indicator e processar em background com notificação ao concluir.
- **Budget mensal estimado:** R$15.000 (~$3.000 USD) para o modelo primário (OpenAI GPT-4o). R$5.000 (~$1.000 USD) reservado para modelo fallback (Anthropic Claude 3.5 Sonnet). Total: R$20.000/mês.
- **Modelo de fallback em caso de estouro de budget:**
  1. **Nível 1 (custo > 80% do budget):** Migrar re-priorizações incrementais para GPT-4o-mini (custo ~10x menor). Manter modelo completo apenas para priorização full.
  2. **Nível 2 (custo > 100% do budget):** Migrar todas as chamadas para GPT-4o-mini. Alertar PM e CTO.
  3. **Nível 3 (custo > 120% do budget):** Fallback completo para algoritmo determinístico WSJF. Desativar IA até próximo ciclo de billing. Notificar todos os usuários afetados.

### A.5 Automation Level

- **Modo Sugestão (padrão — ativado para todos os novos usuários):**
  - A IA analisa o backlog e gera uma lista priorizada sugerida
  - A sugestão é exibida em uma sidebar com diff visual (antes vs. depois) ao lado do board atual
  - O Tech Lead pode: aceitar tudo, aceitar parcialmente (arrastar itens individuais), ou rejeitar tudo
  - Nenhuma alteração é aplicada ao board até aprovação explícita do usuário
  - Classificação: **Rascunho para aprovação**

- **Modo Autônomo (opt-in — requer ativação pelo admin da workspace):**
  - A IA aplica re-priorizações automaticamente quando detecta mudanças relevantes
  - Todas as ações são registradas em log de auditoria imutável com: estado anterior, estado novo, motivo da mudança, timestamp, modelo utilizado
  - Ações de alto impacto (cancelar tarefa, remover assignee, alterar deadline) SEMPRE requerem confirmação humana, mesmo no modo autônomo
  - O admin pode definir "guardrails": limitar quais tipos de ação a IA pode tomar autonomamente
  - Classificação: **Ação autônoma com guardrails**

### A.6 Quality Plan

- **Testes offline (golden set):**
  - Suite de **200 cenários de teste** cobrindo: backlogs de 10 a 500 tarefas, com e sem dependências, com e sem deadlines, equipes de 3 a 20 membros, diferentes distribuições de carga
  - Cada cenário tem uma "golden answer" definida por um painel de 5 Tech Leads experientes (consenso ≥ 4/5)
  - Rubrica de avaliação: Kendall Tau rank correlation ≥ 0.75 entre priorização IA e golden answer para aprovação
  - Execução automática a cada deploy com report publicado no Slack do time de ML

- **Regressão de prompt:**
  - Toda alteração de prompt ou system message passa por pipeline de regressão automatizado
  - O pipeline executa os 200 cenários do golden set + 50 cenários de edge cases (backlog vazio, todas as tarefas com mesma deadline, dependências circulares)
  - Critério de aprovação: score não pode cair mais que 2% em relação ao prompt anterior. Queda > 2% bloqueia o deploy e notifica ML Engineer
  - Versionamento semântico de prompts: `v1.0.0` → `v1.1.0` (minor = melhoria) → `v2.0.0` (major = mudança estrutural)

- **Métricas online (feedback loop):**
  - **Thumbs up/down** em cada sugestão de priorização, com campo opcional de comentário (max 280 caracteres)
  - **Taxa de aceitação:** % de sugestões aceitas sem modificação (meta: ≥ 75%)
  - **Taxa de edição:** % de sugestões aceitas com modificação (informação para fine-tuning, não é métrica de falha)
  - **Tempo até decisão:** tempo entre exibição da sugestão e ação do usuário (aceitar/rejeitar/editar). Meta: < 30 segundos para > 80% das decisões
  - Dashboard interno de qualidade com alertas automáticos se taxa de aceitação cair abaixo de 70% por 3 dias consecutivos

### A.7 Telemetria Mínima

Todos os eventos de telemetria são coletados de forma anonimizada e armazenados por 12 meses. Cada request de IA registra obrigatoriamente:

- **Versão do prompt utilizada:** ID semântico (ex: `prioritization-v1.3.2`) vinculado ao repositório de prompts versionado
- **Rota de modelo:** Qual modelo respondeu (ex: `gpt-4o-2026-05-13`, `claude-3.5-sonnet-20260601`, `wsjf-deterministic-fallback`) e motivo da seleção (primário, fallback por custo, fallback por latência, fallback por erro)
- **Fontes de retrieval:** Quais dados foram incluídos no contexto (IDs de tarefas, métricas agregadas, histórico de sprints utilizados). Nenhum dado PII é registrado na telemetria.
- **Resultados de ferramentas:** Se function calling foi utilizado (ex: consulta de dependências, cálculo de carga por membro), registrar: ferramenta chamada, input (anonimizado), output, latência da chamada
- **Latência e tokens consumidos:** Latência total (end-to-end), latência do modelo (TTFB + streaming), tokens de input, tokens de output, custo estimado em USD
- **Feedback do usuário:** Thumbs up/down, comentário (se fornecido), ação tomada (aceitar/rejeitar/editar), tempo até decisão
- **Metadados de contexto:** Tamanho do backlog (número de tarefas), número de membros da equipe, número de dependências, tempo desde último re-treinamento/fine-tuning

Toda a telemetria é enviada para pipeline de analytics (Mixpanel + data warehouse interno) com latência máxima de 5 minutos. Dashboards de telemetria são revisados semanalmente pela equipe de ML em reunião de quality review.
