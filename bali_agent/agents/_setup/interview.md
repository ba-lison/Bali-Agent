# Roteiro da Entrevista Adaptativa de Setup

> Como o Setup Agent deve conduzir a entrevista rápida com o usuário para complementar as informações do perfilamento de stack.

## Diretrizes de Condução

1.  **Seja Curto e Focado**: O usuário não quer responder um questionário longo. Faça no máximo 3 a 4 perguntas diretas e claras.
2.  **Seja Adaptativo**: Se a stack-detection já identificou Next.js e Supabase, **nunca** pergunte "Qual framework você usa?". Em vez disso, diga: *"Detectei Next.js e Supabase. Deseja adicionar mais alguma tecnologia ao time?"*.
3.  **Use Markdown Limpo**: Apresente as perguntas com boa legibilidade.

---

## Estrutura de Perguntas (Roteiro)

O Setup Agent deve adaptar este roteiro com base nas informações coletadas no perfilamento automático:

### 1. Validação da Stack
*   **Se detectou tecnologias**:
    > *"Olá! Analisei o projeto e identifiquei a seguinte stack: **[Lista de stacks detectadas]**. Isto está correto ou deseja adicionar/remover alguma tecnologia da lista?"*
*   **Se o projeto está vazio (Greenfield)**:
    > *"Olá! Percebi que este é um projeto novo (do zero). Quais serão as principais tecnologias que utilizaremos? (ex: Next.js + Supabase, AutoCAD plugin em C#, etc.)"*

### 2. Definição do Escopo e Convenções
*   **Pergunta**:
    > *"Qual o objetivo principal deste projeto no momento? (ex: 'Estou corrigindo bugs em produção', 'Quero implementar a feature X', 'Estou desenvolvendo o MVP do zero')?"*

### 3. Restrições e Governança ("Não Mexer")
*   **Pergunta**:
    > *"Existem pastas, arquivos ou comportamentos específicos no código que o time **NÃO** deve alterar sob nenhuma hipótese? (ex: 'Não mexer na pasta db/legacy/', 'Não atualizar a biblioteca X')?"*

### 4. Preferências de Convenção de Código
*   **Pergunta**:
    > *"Você possui alguma convenção de código específica que o time deva seguir? (ex: 'Escrever nomes de funções em inglês e comentários em português', 'Sempre usar TypeScript estrito', 'Seguir commits semânticos')?"*

---

## Processamento das Respostas

Após o usuário responder, o Setup Agent consolida as informações em variáveis e gera os artefatos locais:
- As restrições de "Não mexer" são gravadas no bloco `nao_mexer:` do manifesto `subagent.config.yaml`.
- O objetivo e as convenções são injetados nas regras dos especialistas em `.agent/team/spec-*.md` e na constituição `AGENTS.md`.
