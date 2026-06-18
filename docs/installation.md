# Guia de Instalação do Bali-Agent

Este guia orienta na instalação e configuração do **Bali-Agent** como pacote Python global ou local em seu ambiente de desenvolvimento.

## Requisitos

- Python 3.11 ou superior.
- Git.

## Instalação do Pacote CLI

Você pode instalar o CLI `bali` diretamente do repositório clonado localmente no modo editável (recomendado para desenvolvimento):

```bash
git clone https://github.com/ba-lison/Bali-Agent.git
cd Bali-Agent
pip install -e .
```

Ou usando o `pipx` para instalá-lo de forma isolada como CLI global no sistema:

```bash
pipx install .
```

## Inicializando o Bali-Agent em um Projeto Alvo

Navegue até o diretório do seu projeto (alvo) onde deseja configurar a orquestração de subagentes e execute o comando `init`:

```bash
# Inicializa no diretório atual
bali init

# Ou especifica um caminho alternativo
bali init --root /caminho/do/seu/projeto
```

Isso criará a pasta `.agent/` com toda a estrutura necessária:
- `agents/`: Definição de subagentes espinhos (`orchestrator`, `planner`, `reviewer`).
- `protocols/`: Contratos e regras operacionais.
- `team/`: Lista de agentes especialistas (`discovery`, `prd-writer`, etc.).
- `subagent.config.yaml`: Manifesto de subagentes e suas permissões locais.
- Git Pre-commit hook instalado para escanear segredos automaticamente antes do commit.

## Verificando o Setup

Após a inicialização, você pode verificar se todos os arquivos e adaptadores foram instalados corretamente executando:

```bash
bali verify
```

Se tudo estiver configurado com sucesso, o console exibirá:
`[VERIFY] OK: time e adaptadores instalados corretamente.`
