# Checklist de Segurança

## Autenticação e Autorização
- [ ] Autenticação implementada para rotas protegidas
- [ ] Autorização verifica permissões por recurso
- [ ] Tokens têm expiração adequada
- [ ] Senhas armazenadas com hash + salt (bcrypt/argon2)
- [ ] Rate limiting em endpoints de auth

## Validação de Input
- [ ] Todas as entradas de usuário são validadas
- [ ] Queries parametrizadas (prevenção SQL Injection)
- [ ] Output encoding (prevenção XSS)
- [ ] Upload de arquivos validado (tipo, tamanho)
- [ ] Desserialização segura

## Dados Sensíveis
- [ ] Sem hardcoded secrets no código
- [ ] Dados em trânsito via HTTPS/TLS
- [ ] Dados em repouso criptografados
- [ ] PII tratada conforme LGPD/GDPR
- [ ] Logs não expõem dados sensíveis

## Dependências
- [ ] Packages verificados (anti-slopsquatting)
- [ ] Sem vulnerabilidades conhecidas (npm audit / pip audit)
- [ ] Versões fixas no lockfile

## Infraestrutura
- [ ] CORS configurado corretamente
- [ ] Headers de segurança (CSP, X-Frame-Options, etc.)
- [ ] Rate limiting configurado
- [ ] Error responses não expõem stack traces

## Específico para IA/LLM (se aplicável)
- [ ] Prompts não expõem dados do sistema
- [ ] Input sanitizado antes de enviar ao LLM
- [ ] Output do LLM validado antes de exibir ao usuário
- [ ] Custo por request monitorado
- [ ] Prompt injection mitigado
