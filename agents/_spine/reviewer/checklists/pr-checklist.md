# Checklist de Pull Request

## Escopo
- [ ] PR é pequeno e focado (< 400 linhas de mudanças reais)
- [ ] Uma mudança lógica por PR (não misturar refatoração com features)
- [ ] Título descritivo seguindo padrão: tipo(escopo): descrição

## Descrição
- [ ] Explica O QUÊ mudou
- [ ] Explica POR QUÊ mudou (motivação)
- [ ] Referencia issue/task relacionada
- [ ] Lista breaking changes (se houver)

## Código
- [ ] Segue style guide do projeto
- [ ] Nomes descritivos para variáveis, funções e classes
- [ ] Sem código comentado
- [ ] Sem hardcoded secrets, URLs ou credentials
- [ ] Tratamento de erros adequado
- [ ] Sem warnings/errors no linter

## Testes
- [ ] Testes incluídos no mesmo PR
- [ ] Testes cobrem o happy path
- [ ] Testes cobrem edge cases e erros
- [ ] Todos os testes passam
- [ ] Build completa sem erros

## Segurança
- [ ] Input validation em todas as entradas de usuário
- [ ] Sem vulnerabilidades OWASP óbvias
- [ ] Packages verificados (existem no registry oficial)
- [ ] Dados sensíveis tratados adequadamente
