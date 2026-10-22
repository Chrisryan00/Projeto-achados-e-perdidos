# Roteiro manual de aceitação — 001-achados-e-perdidos

**Status:** pendente de execução manual. Use somente dados fictícios; marque resultados apenas depois de observar cada cenário.

| Cenário | Estado inicial e ação | Resultado esperado | Resultado observado |
|---|---|---|---|
| SC-01 Publicar, localizar e contatar | Servidor ativo; publicar relato fictício único; encontrar o cartão; acionar e-mail ou WhatsApp de teste | API responde HTTP 201; cartão aparece no mural, contém o contato informado e o botão abre o destino esperado; código de gerenciamento é mostrado após publicar | Pendente |
| SC-02 Publicação inválida | Enviar formulário sem campo obrigatório ou com data futura | Interface informa o problema e não cria anúncio; API rejeita os dados inválidos | Pendente |
| SC-03 Sem resultados | Pesquisar termo inexistente | Estado vazio aparece, sem mensagem de falha de conexão | Pendente |
| SC-04 Filtros válidos | Selecionar tipo, categoria e situação com anúncios correspondentes e não correspondentes | Só anúncios que correspondem aos filtros aparecem | Pendente |
| SC-05 Código inválido | Tentar resolver ou remover anúncio com código incorreto | API responde 403; anúncio permanece inalterado | Pendente |
| SC-06 Resolver | Usar código correto em anúncio perdido e encontrado | API responde 200; anúncio fica resolvido com o rótulo adequado | Pendente |
| SC-07 Foto e urgência | Publicar item fictício com foto permitida e urgência marcada | Foto aparece no cartão; rota da foto responde imagem; marca de urgência é visível | Pendente |
| SC-08 Serviço indisponível | Parar o servidor e abrir/recarregar a página | Interface orienta iniciar o servidor local | Pendente |
| SC-09 Filtro inválido | Consultar a API com tipo, categoria ou situação não permitidos | API responde HTTP 400 com mensagem; valor inválido não é tratado como filtro ausente | Pendente |
| SC-10 Demonstração pública | Depois de publicar no Render, abrir a URL HTTPS de uma janela anônima/dispositivo externo; abrir `/api/v1/health` e `/openapi.yaml` | Página responde; health retorna `{"status":"ok"}`; contrato OpenAPI é exibido. Anotar eventual demora de inicialização do plano gratuito | Pendente — serviço ainda não publicado |
| SC-11 Correspondências sugeridas | Publicar um item; após a confirmação, conferir sugestões. Em outro cartão aberto, clicar em **Ver possíveis correspondências** | Até três anúncios abertos do tipo oposto, com razões legíveis e links; Pode ser marca a sugestão, Não é meu item oculta; lista vazia sem candidatos; funciona sem chave e faz fallback se Gemini falhar; dados enviados ao provedor são mínimos. Sugestões não confirmam o objeto | Pendente — reiniciar servidor e executar roteiro |
| SC-12 Origem dos anúncios | Com seed fictício e uma publicação de teste no mural, selecionar todos, comunidade e exemplos fictícios | Cada opção mostra somente a origem selecionada; os cartões têm rótulo claro; apenas a publicação do formulário mostra contato | Pendente |
| SC-13 Situação e cores | Abrir o formulário; escolher perdido e encontrado; publicar dados fictícios e resolver uma publicação própria com código válido | Perdido aparece vermelho, encontrado amarelo; resolução muda para a aba verde Resolvidos; Todos/Em aberto/Resolvidos mostram os estados esperados; código inválido não resolve anúncio | Pendente |

## Ambiente e evidências

- Data e hora:
- Sistema operacional:
- Navegador e versão:
- Viewports verificados: 360 px / 768 px / 1366 px
- Pessoa que executou:
- Comandos/URLs usados:
- Observações ou defeitos:
- Resultado geral: pendente
- IA de correspondência: Gemini opcional; nunca registrar a chave. Registro de consentimento para contato de terceiros: pendente.
