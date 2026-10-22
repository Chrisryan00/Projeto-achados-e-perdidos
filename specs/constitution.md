# Constituição do projeto — CESMAC Achados & Perdidos

**Versão:** 1.1  
**Situação:** princípios gerais do projeto; detalhes técnicos estão no plano da funcionalidade.

Esta constituição define as regras de implementação para o projeto atual. O escopo e os critérios funcionais estão em [`001-achados-e-perdidos/spec.md`](001-achados-e-perdidos/spec.md), o modelo de persistência em [`001-achados-e-perdidos/data-model.md`](001-achados-e-perdidos/data-model.md), a API em [`001-achados-e-perdidos/contracts/openapi.yaml`](001-achados-e-perdidos/contracts/openapi.yaml) e a execução em [`001-achados-e-perdidos/quickstart.md`](001-achados-e-perdidos/quickstart.md).

## Princípios

1. **Relatos transparentes:** o mural mostra informações enviadas por quem publica; o sistema não confirma identidade, propriedade ou devolução.
2. **Privacidade por padrão:** usar cenários fictícios em demonstrações e minimizar dados pessoais. Um contato real só pode aparecer em uma demonstração com autorização explícita de quem é titular; avisar que o mural o torna visível. Enviar a serviços externos somente os dados estritamente necessários e nunca segredos ou códigos de gerenciamento.
3. **Controle da publicação:** somente quem apresenta o código de gerenciamento válido pode resolver ou excluir o anúncio; o código não deve ser armazenado em formato recuperável.
4. **Validação no servidor:** todas as entradas da API são verificadas no domínio, mesmo quando a interface também valida os campos.
5. **Documentação acompanha o código:** mudanças de comportamento devem atualizar a especificação, o contrato e os guias afetados.

## Limites

Não há contas, autenticação de identidade, recuperação de código, moderação, notificações ou sincronização entre dispositivos. Os anúncios fictícios servem para demonstrar a interface e não devem ser interpretados como relatos reais. As escolhas de linguagem, armazenamento, execução local e limites operacionais pertencem ao plano técnico, não são princípios gerais.
