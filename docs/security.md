# Guia de Segurança e Controles de Permissão

Este documento detalha o funcionamento e configuração do sistema de segurança do **Bali-Agent**.

## O Manifesto de Permissões (`subagent.config.yaml`)

O controle de segurança de cada subagente é definido no arquivo `subagent.config.yaml` localizado na raiz do projeto alvo.

### Exemplo de Configuração de Subagente

```yaml
id: spec-frontend
role: frontend-engineer
model: default
allowed_tools:
  - read_file
  - write_file
denied_paths:
  - .env
  - .git/
  - secrets/
max_iterations: 6
max_tokens: 12000
requires_review_by: reviewer
can_spawn_agents: false
```

- **allowed_tools**: Lista de ferramentas que o subagente pode invocar. Se tentar chamar uma ferramenta fora da lista, a execução é abortada pela engine.
- **denied_paths**: Lista de subdiretórios ou arquivos específicos que são bloqueados para leitura/escrita.
- **can_spawn_agents**: Indica se este subagente tem permissão de criar dinamicamente novos subagentes.

## Fluxo de Aprovação Humana (Approval System)

Quando uma ferramenta tenta realizar uma ação crítica:
1. O runtime avalia o comando contra a classe de risco.
2. Se for detectado um comando fora da lista de permitidos R2 (como builds/testes básicos) ou se houver tentativa de modificar arquivos de configuração críticos (`pyproject.toml`, `package.json`, etc.), o Bali-Agent aciona a ferramenta de aprovação interativa.
3. A execução é congelada, e o terminal do usuário exibe um prompt contendo:
   - Ação solicitada.
   - Justificativa do subagente.
   - Riscos detectados.
   - Um diff de alterações no caso de escritas.
4. O usuário deve aceitar ou recusar formalmente. Se recusar, o subagente recebe um retorno de erro de permissão e deve tentar uma abordagem alternativa.
