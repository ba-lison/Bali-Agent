# Dry-run de validação end-to-end

> Roteiro para provar que o time funciona de ponta a ponta num projeto real.
> A parte do **instalador** é coberta automaticamente por `tests/test_base_structure.py::test_installer_flow`.
> Os passos com LLM (geração do time + disparo do hook) são manuais.

## 1. Instalar num projeto-exemplo
```bash
# crie um projeto fake (ex.: Next.js + Supabase de mentira)
mkdir /tmp/demo && cd /tmp/demo && git init
mkdir supabase && echo '{}' > package.json && echo 'next' >> package.json && touch supabase/config.toml

# instale o framework
python /caminho/para/Bali-Agent/init.py   # informe /tmp/demo como destino
```
**Esperado:** `.agent/` criado com `agents/`, `protocols/`, `templates/`, `hooks/prevent_secrets.py`,
`hooks/claude_hook.py`, `verify_setup.py`, `task.md`, `working-context.md`; `.claude/settings.json`
instalado; `AGENTS.md` na raiz; pre-commit do Git injetado.

## 2. Rodar o Setup do time (LLM)
Abra o `/tmp/demo` no Claude Code (ou Cursor/Gemini) e digite no chat:
```
Setup do time
```
**Esperado:** o Setup Agent detecta Next.js + Supabase, faz a entrevista curta, propõe o time
(espinha + `spec-nextjs`/`spec-supabase`), e após aprovação gera `.agent/team/*.md`,
`.agent/subagent.config.yaml`, espelha `.claude/agents/*.md` e roda `verify_setup.py`.

## 3. Verificar o setup (determinístico)
```bash
cd /tmp/demo && python .agent/verify_setup.py
```
**Esperado:** `[VERIFY-SETUP] OK: time e adaptadores instalados corretamente.`

## 4. Confirmar o enforcement (Claude Code)
Inicie uma nova sessão no Claude Code dentro de `/tmp/demo` e faça um pedido qualquer.
**Esperado:** o hook `UserPromptSubmit`/`SessionStart` re-injeta a constituição (você vê o bloco
"SYSTEM REMINDER: TIME BALI-AGENT") e o assistente roteia pelo time (linha `🎯 Roteando: ...`),
nunca respondendo sozinho.

## 5. Confirmar o Agent Shield
```bash
echo "STRIPE_KEY=sk_live_<cole-24+-caracteres-ficticios-aqui>" > .env && git add .env && git commit -m teste
```
**Esperado:** commit **bloqueado** pelo pre-commit com a mensagem do `[AGENT SHIELD]`.
