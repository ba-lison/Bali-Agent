# Guia de Testes do Bali-Agent

O **Bali-Agent** possui uma suite abrangente de testes automatizados rodando sob o framework `pytest`. Isso garante a estabilidade de código e a imunidade a regressões durante novos aprimoramentos.

## Estrutura da Suite de Testes

Os testes estão localizados na pasta `tests/` e são estruturados da seguinte forma:

```txt
tests/
  conftest.py                # Fixtures globais (como diretório de projeto temporário)
  test_agent_manager.py      # Testes de manifesto e carregamento de especialistas
  test_cli.py                # Testes de comandos CLI (init, verify)
  test_context_packer.py     # sliding window, redactions e geração de context manifest
  test_handoff.py            # Validação do HandoffBus
  test_integration.py        # Integração ponta-a-ponta com LLM mockado
  test_memory.py             # Busca, indexação SQLite FTS5 e proteção a segredos na gravação
  test_observability.py      # Verificação de arquivos de trace e patches gerados
  test_policy.py             # Testes de ToolPolicy (R0-R4, path traversal e sandboxing)
  test_security.py           # Validações de baixo nível contra path traversal e shell perigoso
```

## Executando os Testes

Para rodar toda a suite de testes, certifique-se de que o pacote está no `PYTHONPATH` ou instalado no modo editável:

```bash
# Configura o PYTHONPATH
$env:PYTHONPATH="."  # No Windows PowerShell
export PYTHONPATH=.  # No Linux/macOS

# Executa o pytest
pytest
```

## Diretrizes para Novos Testes

Qualquer nova funcionalidade adicionada ao núcleo (`core/`), ferramentas (`tools/`), segurança (`security/`) ou adaptadores (`adapters/`) deve vir acompanhada de um teste unitário correspondente na suite.

- **Evite chamadas reais de rede**: Use o sistema de mock ou monkeypatch do `pytest` para simular APIs de LLMs comerciais.
- **Utilize caminhos temporários**: Use a fixture `temp_project_dir` definida em `tests/conftest.py` para testes que criam ou leem arquivos físicos no disco.
