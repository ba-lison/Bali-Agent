# PRD: {NOME_DO_PROJETO}

> **Autor:** {AUTOR} | **Data:** {DATA} | **Versão:** {VERSÃO} | **Status:** Rascunho | Em Revisão | Aprovado

---

## 1. Resumo Executivo

{3 frases: problema → solução → impacto esperado}

---

## 2. Problema

### 2.1 Descrição do Problema

{Qual dor do usuário ou oportunidade de negócio motivou isso?}

### 2.2 Evidências

{Dados, feedback de usuários, pesquisa de mercado que sustentam o problema}

### 2.3 Impacto de Não Resolver

{O que acontece se não fizermos nada?}

---

## 3. Objetivo

{O que o produto/feature deve atingir? Objetivos SMART.}

---

## 4. Usuários Alvo

### 4.1 Persona Primária

- **Nome:** {Nome da persona}
- **Perfil:** {Descrição}
- **Necessidade principal:** {O que precisa}
- **Jornada atual:** {Como resolve hoje}

### 4.2 Persona Secundária (se houver)

- **Nome:** {Nome da persona}
- **Perfil:** {Descrição}
- **Necessidade principal:** {O que precisa}
- **Jornada atual:** {Como resolve hoje}

---

## 5. Hipóteses

| #  | Hipótese    | Como Validar        | Status           |
|----|-------------|---------------------|------------------|
| H1 | {Suposição} | {Método de validação} | ⬜ Não testada   |
| H2 | {Suposição} | {Método de validação} | ⬜ Não testada   |
| H3 | {Suposição} | {Método de validação} | ⬜ Não testada   |

---

## 6. Requisitos Funcionais

### RF-001: {Nome do Requisito}

- **Como** {persona}, **quero** {ação}, **para que** {benefício}
- **Critérios de Aceitação:**
  - [ ] {Critério 1}
  - [ ] {Critério 2}
- **Prioridade:** 🔴 Must Have | 🟡 Should Have | 🟢 Could Have

### RF-002: {Nome do Requisito}

- **Como** {persona}, **quero** {ação}, **para que** {benefício}
- **Critérios de Aceitação:**
  - [ ] {Critério 1}
  - [ ] {Critério 2}
- **Prioridade:** 🔴 Must Have | 🟡 Should Have | 🟢 Could Have

### RF-003: {Nome do Requisito}

- **Como** {persona}, **quero** {ação}, **para que** {benefício}
- **Critérios de Aceitação:**
  - [ ] {Critério 1}
  - [ ] {Critério 2}
- **Prioridade:** 🔴 Must Have | 🟡 Should Have | 🟢 Could Have

> **Instrução para o agente:** Adicionar quantos RF forem necessários. Cada requisito deve seguir o formato de user story e ter critérios de aceitação verificáveis.

---

## 7. Requisitos Não-Funcionais

| ID      | Categoria       | Requisito     | Métrica                    |
|---------|-----------------|---------------|----------------------------|
| RNF-001 | Performance     | {Descrição}   | {SLO: ex: p99 < 200ms}    |
| RNF-002 | Segurança       | {Descrição}   | {Critério}                 |
| RNF-003 | Acessibilidade  | {Descrição}   | {Padrão: WCAG 2.1 AA}     |
| RNF-004 | Escalabilidade  | {Descrição}   | {Métrica}                  |
| RNF-005 | Disponibilidade | {Descrição}   | {SLA: ex: 99.9% uptime}   |
| RNF-006 | Conformidade    | {Descrição}   | {Regulação: LGPD, GDPR}   |

---

## 8. Métricas de Sucesso

| Métrica   | Baseline Atual | Meta          | Prazo   |
|-----------|----------------|---------------|---------|
| {KPI 1}   | {Valor atual}  | {Valor meta}  | {Data}  |
| {KPI 2}   | {Valor atual}  | {Valor meta}  | {Data}  |
| {KPI 3}   | {Valor atual}  | {Valor meta}  | {Data}  |

---

## 9. Fora de Escopo

- ❌ {Item 1 que NÃO fazemos nesta iteração}
- ❌ {Item 2}
- ❌ {Item 3}

> **Instrução para o agente:** Listar explicitamente funcionalidades ou características que foram discutidas mas deliberadamente excluídas. Isso evita scope creep e alinha expectativas.

---

## 10. Riscos e Dependências

| #  | Risco/Dependência | Tipo         | Probabilidade     | Impacto          | Mitigação       |
|----|-------------------|--------------|-------------------|------------------|-----------------|
| R1 | {Descrição}       | Risco        | Alta/Média/Baixa  | Alto/Médio/Baixo | {Plano}         |
| R2 | {Descrição}       | Risco        | Alta/Média/Baixa  | Alto/Médio/Baixo | {Plano}         |
| D1 | {Descrição}       | Dependência  | -                 | -                | {Responsável}   |
| D2 | {Descrição}       | Dependência  | -                 | -                | {Responsável}   |

---

## 11. Critérios de Aceitação Globais

- [ ] {Critério 1: condição verificável que se aplica ao projeto inteiro}
- [ ] {Critério 2}
- [ ] {Critério 3}
- [ ] {Critério 4}

---

## 12. Cronograma Estimado

| Fase            | Início  | Fim     | Responsável |
|-----------------|---------|---------|-------------|
| Discovery       | {Data}  | {Data}  | {Nome}      |
| Design          | {Data}  | {Data}  | {Nome}      |
| Desenvolvimento | {Data}  | {Data}  | {Nome}      |
| Testes          | {Data}  | {Data}  | {Nome}      |
| Lançamento      | {Data}  | {Data}  | {Nome}      |

---

## Apêndice A: Seções para Projetos com IA/LLM

> **Instrução para o agente:** Incluir este apêndice apenas quando o projeto envolver componentes de Inteligência Artificial, modelos de linguagem (LLM), ou sistemas baseados em geração de texto/decisões automatizadas.

### A.1 Intent Scope

- **Intenções suportadas:** {Lista de intenções que o sistema responde}
- **Intenções fora de escopo:** {Lista com fallback definido}

### A.2 Data Boundary

- **Dados permitidos nos prompts:** {Lista de categorias de dados que podem ser enviadas ao modelo}
- **Dados BLOQUEADOS:** {Lista de dados que NUNCA devem ser enviados + método de redação/sanitização}

### A.3 Evidence Requirements

- {Respostas precisam de citações? Links para fontes? Output estruturado?}
- {Qual o nível de confiança mínimo aceitável?}
- {Como erros/alucinações são tratados?}

### A.4 Cost & Latency Budgets

- **Custo máximo por request:** {$X.XX}
- **SLO de latência:** {p99 < Xms}
- **Budget mensal estimado:** {$X.XXX}
- **Modelo de fallback em caso de estouro:** {Modelo mais barato ou regra determinística}

### A.5 Automation Level

- {Somente leitura — IA apenas sugere, humano executa}
- {Rascunho para aprovação — IA gera, humano revisa e aprova}
- {Ação autônoma — IA executa sem intervenção humana}

### A.6 Quality Plan

- **Testes offline:** {Suite de testes com golden answers, rubrica de avaliação}
- **Regressão de prompt:** {Como testar que mudanças de prompt não degradam qualidade}
- **Métricas online:** {Feedback loop: thumbs up/down, taxa de aceitação, edições do usuário}

### A.7 Telemetria Mínima

- Versão do prompt utilizada
- Rota de modelo (qual modelo respondeu)
- Fontes de retrieval (se RAG — quais documentos foram recuperados)
- Resultados de ferramentas (se function calling — quais tools foram chamadas e resultados)
- Latência e tokens consumidos
- Feedback do usuário (se coletado)
