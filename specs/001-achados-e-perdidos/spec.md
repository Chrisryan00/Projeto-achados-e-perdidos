# Especificação — CESMAC Achados & Perdidos

**ID:** 001-achados-e-perdidos  
**Versão:** 1.4  
**Situação:** rascunho para revisão do grupo. Descreve o comportamento local e a demonstração pública na nuvem; não depende de aprovação do professor. O deploy ainda não foi realizado.  
**Constituição:** [`../constitution.md`](../constitution.md)

## Problema e objetivo

Pessoas da comunidade CESMAC precisam divulgar objetos perdidos ou encontrados e localizar quem publicou o relato. O sistema oferece um mural pesquisável, meios de contato e ações para acompanhar o desfecho de cada anúncio.

## Usuários e histórias priorizadas

### P1 — jornada principal demonstrável

- **[US1] Publicar, localizar e permitir contato:** como pessoa que perdeu ou encontrou um objeto, quero publicar um relato que apareça no mural com uma forma de contato para que outra pessoa possa me procurar e ajudar a resolver o caso.
- **[US6] Encontrar possíveis correspondências:** como visitante, quero comparar um anúncio com relatos abertos do tipo oposto e receber sugestões para verificar se alguém encontrou o objeto que perdi ou vice-versa.

### P2 — consulta e acompanhamento

- **[US2] Consultar o mural:** como visitante, quero buscar por texto e filtrar por tipo, categoria e situação para localizar relatos relevantes.
- **[US3] Gerenciar minha publicação:** como pessoa que publicou, quero marcar o caso como resolvido ou remover o anúncio usando o código recebido.
- **[US7] Distinguir origens do mural:** como visitante, quero filtrar publicações da comunidade e exemplos fictícios para saber quais cartões são apenas dados de demonstração.

### P3 — informações adicionais

- **[US5] Enriquecer o anúncio:** como pessoa que publica, quero incluir uma foto e indicar urgência para facilitar a identificação do objeto.

### Entrega da demonstração

- **[US4] Acessar a demonstração pela internet:** como professor ou visitante, quero abrir uma URL pública para conhecer o sistema sem instalar o projeto ou iniciar um servidor no meu computador.

## Jornada P1 e cenários

### SC-01 — Publicar e localizar um item (fluxo principal)

- **Estado inicial:** mural disponível; ainda não existe relato com o título escolhido. Usar dados fictícios no cenário.
- **Ação:** publicar um objeto perdido ou encontrado com título, descrição, categoria, local, data, nome fictício e contato de teste; localizar o cartão no mural e acionar o meio de contato informado.
- **Resultado esperado:** o relato é criado e aparece no mural com o contato correspondente; a ação de contato abre o destino correto; o código de gerenciamento é apresentado a quem publicou.

### SC-02 — Rejeitar publicação inválida

- **Estado inicial:** formulário de publicação aberto.
- **Ação:** enviar dados sem título, sem contato, com categoria inválida ou com data futura.
- **Resultado esperado:** a interface informa o erro e nenhum anúncio inválido é criado; chamadas diretas à API recebem HTTP 422 para dados inválidos.

### SC-03 — Busca sem resultados

- **Estado inicial:** mural carregado.
- **Ação:** pesquisar um termo que não apareça nos anúncios existentes.
- **Resultado esperado:** lista vazia e mensagem de estado vazio; a página continua utilizável e permite limpar a busca.

### SC-04 — Filtro de tipo e categoria

- **Estado inicial:** mural contém anúncios de tipos e categorias diferentes.
- **Ação:** selecionar um tipo e uma categoria.
- **Resultado esperado:** somente anúncios que correspondem aos filtros permanecem visíveis.

### SC-05 — Código de gerenciamento incorreto

- **Estado inicial:** anúncio existente e aberto.
- **Ação:** enviar PATCH ou DELETE com código incorreto.
- **Resultado esperado:** HTTP 403 e anúncio inalterado.

### SC-06 — Resolver com código válido

- **Estado inicial:** anúncio aberto criado pelo usuário, cujo código foi guardado.
- **Ação:** marcar perdido como recuperado ou encontrado como devolvido.
- **Resultado esperado:** HTTP 200, anúncio passa para `resolved` e aparece como resolvido na consulta que inclui todos os estados.

### SC-07 — Carregar foto

- **Estado inicial:** formulário aberto e imagem JPG, PNG ou WebP disponível.
- **Ação:** anexar imagem e publicar.
- **Resultado esperado:** o cartão apresenta a foto; a consulta da imagem respeita o formato e o limite definidos no contrato da API.

### SC-08 — API indisponível

- **Estado inicial:** servidor local parado.
- **Ação:** abrir ou atualizar a página.
- **Resultado esperado:** a interface informa que o mural está indisponível e orienta iniciar o servidor local.

### SC-09 — Rejeitar filtros inválidos

- **Estado inicial:** mural disponível e com anúncios cadastrados.
- **Ação:** consultar a API com um tipo fora de `lost`/`found`, uma categoria fora da lista permitida ou uma situação fora de `open`/`resolved`/`all`.
- **Resultado esperado:** a API retorna HTTP 400 com mensagem de validação e não interpreta silenciosamente o filtro como ausente.

### SC-10 — Abrir a demonstração publicada

- **Estado inicial:** a versão de demonstração está publicada e o serviço está ativo.
- **Ação:** um visitante abre a URL HTTPS em outro computador ou rede e consulta o mural e a rota de saúde.
- **Resultado esperado:** a página e a API respondem sem depender do computador do grupo; o mural apresenta apenas dados de demonstração. O primeiro acesso pode demorar quando o serviço gratuito estiver iniciando.

### SC-11 — Sugerir possíveis correspondências

- **Estado inicial:** o mural contém um anúncio aberto e anúncios abertos do tipo oposto.
- **Ação:** publicar um item ou acionar “Ver possíveis correspondências” no cartão.
- **Resultado esperado:** após a publicação, o sistema compara candidatos e apresenta no máximo três anúncios existentes do tipo oposto, com razões legíveis (categoria, palavras, local ou data) e acesso aos cartões. Quem consulta pode marcar “Pode ser” ou “Não é meu item”; a avaliação fica apenas no navegador e não treina a IA. Com `GEMINI_API_KEY`, Gemini ordena candidatos previamente selecionados; sem chave ou quando o serviço falha, usa pontuação local por título, categoria, local, descrição e proximidade da data. Sem candidatos compatíveis, informa que não encontrou sugestões. Toda sugestão é apenas uma possibilidade e não confirma que se trata do mesmo objeto. Contatos e códigos de gerenciamento não são enviados ao Gemini.

### SC-12 — Separar exemplos e publicações da comunidade

- **Estado inicial:** mural contém pelo menos um exemplo fictício e uma publicação feita pelo formulário.
- **Ação:** alternar entre todos os anúncios, publicações da comunidade e exemplos fictícios.
- **Resultado esperado:** cada filtro mostra apenas sua origem; cartões identificam a origem. Exemplos fictícios sem contato não oferecem contato. Exemplos de demonstração com contato autorizado oferecem o botão correspondente e continuam identificados como fictícios; publicações da comunidade mostram os meios informados por quem publicou.

### SC-13 — Personalizar foto de cartão autorizado

- **Estado inicial:** aplicação executada localmente, mural com um cartão fictício ou o cartão “Mochila preta” de Christian Lopes sem foto e uma imagem JPG, PNG ou WebP disponível.
- **Ação:** selecionar “Adicionar foto” no cartão e escolher a imagem.
- **Resultado esperado:** a imagem é compactada, salva no anúncio e exibida após atualizar o mural. Outros cartões da comunidade não exibem o controle; conexões remotas recebem HTTP 403.

## Escopo funcional

- Criar anúncio do tipo `lost` (perdido) ou `found` (encontrado), com nome do item, descrição, categoria, local, data, nome de contato e ao menos um meio de contato.
- Anexar foto opcional JPG, PNG ou WebP, respeitando o limite definido no contrato.
- Indicar urgência, pesquisar por título, descrição, categoria e local, e filtrar por tipo, categoria e situação.
- Mostrar contadores de anúncios abertos perdidos, abertos encontrados e anúncios resolvidos.
- Abrir contato por e-mail ou WhatsApp quando o respectivo dado estiver disponível.
- Emitir código de gerenciamento aleatório na criação, permitindo resolver ou excluir o anúncio.
- Apresentar anúncios fictícios para demonstração sem apagar publicações existentes ao acrescentar novos dados demonstrativos.
- Identificar exemplos fictícios e publicações da comunidade e permitir filtrar cada grupo.
- Oferecer sugestões de correspondência entre anúncios abertos de tipos opostos, usando Gemini para ordenar candidatos quando disponível e análise local como alternativa; explicar os motivos e guardar a avaliação da sugestão apenas no navegador.
- Disponibilizar operações de consulta, publicação, acesso a fotos, gerenciamento e verificação de disponibilidade conforme o contrato da API.
- Publicar uma versão de demonstração acessível por URL HTTPS, usando itens fictícios e sem incluir contatos reais locais.

## Requisitos funcionais

- **RF-01:** aceitar somente tipos `lost` e `found`.
- **RF-02:** exigir nome do item, descrição, categoria permitida, local, data válida não futura, nome de contato e pelo menos e-mail ou telefone.
- **RF-03:** limitar nome do item a 100 caracteres, descrição a 1.500, categoria a 40, local a 120, nome de contato a 80, e-mail a 254 e telefone a 30 caracteres.
- **RF-04:** permitir foto opcional JPEG, PNG ou WebP, limitada a 700.000 caracteres após a preparação para envio; a foto válida pode ser visualizada no anúncio.
- **RF-05:** listar anúncios e permitir busca por texto e filtros por tipo, categoria e situação. A API aceita `status=open`, `resolved` ou `all`.
- **RF-06:** a API ordena anúncios abertos antes dos resolvidos, urgentes antes dos não urgentes e mais recentes primeiro. Na interface, a ordenação padrão é mais recente primeiro dentro de cada situação; o seletor permite priorizar urgentes.
- **RF-07:** retornar no máximo 200 anúncios por consulta; os contadores são calculados sobre todos os registros.
- **RF-08:** fornecer à pessoa que publicou um código de gerenciamento imprevisível, exibi-lo somente na criação e não armazená-lo em formato recuperável no servidor.
- **RF-09:** exigir o código válido para resolver ou excluir. Código incorreto resulta em HTTP 403; ID inexistente, HTTP 404.
- **RF-10:** resolver anúncio perdido com intenção `recovered` e encontrado com `returned`; persistir ambos com estado `resolved`.
- **RF-11:** dados inválidos na criação são rejeitados sem criar anúncio; filtros inválidos são rejeitados sem alterar o resultado da consulta; requisições acima do limite são rejeitadas. Os códigos HTTP correspondentes são definidos no contrato da API.
- **RF-12:** disponibilizar operações para consultar anúncios e disponibilidade, publicar, acessar foto, resolver e remover anúncios, conforme o contrato da API.
- **RF-13:** para um anúncio aberto, comparar no máximo 200 anúncios abertos do tipo oposto e retornar até três candidatos existentes ordenados por compatibilidade. Usar Gemini para ordenar os candidatos quando configurado; sem chave ou diante de falha do provedor, usar pontuação local. Limitar a oito análises por IP em 60 segundos. A rota é `POST /api/v1/items/{id}/matches`.
- **RF-15:** para cada sugestão, apresentar ao menos um motivo verificável da compatibilidade quando houver (categoria, palavras em comum, local ou proximidade da data); permitir marcar “Pode ser” ou “Não é meu item” e manter essas escolhas somente no armazenamento local do navegador. Não usar essas escolhas para treinar ou modificar anúncios.
- **RF-16:** permitir filtrar o mural por todos, anúncios em aberto ou anúncios resolvidos; identificar itens perdidos em vermelho, encontrados em amarelo e resolvidos em verde. Em “Todos”, apresentar anúncios em aberto primeiro e agrupar os resolvidos numa seção própria no fim do mural; os cartões e a seção de resolvidos usam fundo e identidade visual verdes.
- **RF-17:** exibir somente ação de contato por WhatsApp nos cartões. Na execução local, permitir selecionar e salvar uma foto nos cartões fictícios e no cartão restaurado “Mochila preta” de Christian Lopes; rejeitar a edição de foto a partir de conexão remota ou em outros anúncios da comunidade.
- **RF-14:** identificar os anúncios seed como exemplos fictícios e as publicações do formulário como publicações da comunidade; permitir mostrar todos, somente publicações da comunidade ou somente exemplos fictícios. A origem não afirma que uma publicação foi verificada.

## Requisitos de qualidade e privacidade

- **RNF-01 — Privacidade:** cenários de demonstração são fictícios. Um telefone real só pode ser usado em anúncio de demonstração com autorização explícita do titular e fica visível no mural; não representa uma ocorrência real. Quando configurado, Gemini recebe apenas título, tipo, categoria, local e data do anúncio e dos candidatos. Nomes de publicadores, descrições, fotos, contatos e códigos de gerenciamento não são enviados. A pontuação local não envia dados a terceiros.
- **RNF-02 — Proteção do gerenciamento:** o código de gerenciamento deve ser imprevisível, não recuperável a partir dos dados armazenados pelo servidor e obrigatório para alterar ou remover o anúncio.
- **RNF-03 — Compatibilidade e responsividade:** a jornada P1 deve ser verificável na versão estável do Google Chrome disponível durante a revisão, em larguras de viewport de 360 px, 768 px e 1366 px, sem rolagem horizontal da página. A versão do navegador e os resultados devem ser anotados no roteiro manual.
- **RNF-04 — Comunicação de falha:** quando o serviço estiver indisponível, a interface deve apresentar uma mensagem visível que oriente a pessoa a iniciar o servidor local; o resultado é verificado no SC-08.
- **RNF-05 — Acesso à demonstração:** quando publicada, a aplicação deve ser acessível por HTTPS a partir de uma rede externa e responder à rota de saúde. Esta é uma demonstração acadêmica, sem garantia de disponibilidade ou persistência na hospedagem gratuita.

## Critérios de aceitação

1. Dados válidos criam registro persistente e cartão visível no mural.
2. Pesquisa encontra palavra no título, descrição, categoria ou local.
3. Dados obrigatórios ausentes, categoria desconhecida ou data futura impedem a criação e retornam erro HTTP 422 pela API.
4. Foto válida é disponibilizada pela rota individual; anúncio sem foto não apresenta imagem.
5. Código incorreto não altera nem exclui o anúncio e resulta em HTTP 403.
6. Código correto permite resolver ou remover a publicação; registro resolvido aparece ao consultar `status=all`.
7. Anúncios permanecem no banco após reiniciar o servidor.
8. Sem servidor, a interface exibe orientação para iniciar o servidor local.
9. Busca sem correspondência apresenta estado vazio e não erro de conexão.
10. Filtros de tipo, categoria ou situação inválidos são rejeitados com HTTP 400 e mensagem explicativa.
11. Na jornada P1, a pessoa visitante consegue iniciar contato pelo meio informado no anúncio.
12. Um visitante externo consegue abrir a URL HTTPS publicada e obter resposta `200` em `/api/v1/health`, conforme SC-10.
13. Para um anúncio aberto, a análise retorna no máximo três anúncios abertos do tipo oposto que existem no banco; sem candidatos compatíveis, retorna lista vazia. A sugestão abre o cartão real correspondente.
14. Quando Gemini está configurado, ele recebe apenas título, tipo, categoria, local e data do anúncio original e dos candidatos; não recebe descrições, nomes, contatos, fotos ou códigos. Sem chave ou se o provedor falhar, a análise local continua disponível. Após oito análises em 60 segundos do mesmo IP, a API responde `429`.
15. Com exemplos fictícios e publicações feitas pelo formulário no banco, cada opção do filtro de origem mostra os cartões corretos e o rótulo correspondente.
16. Ao publicar, o visitante vê sugestões do tipo oposto; cada uma apresenta razões e ações de avaliação; a escolha negativa a oculta e a positiva fica marcada no navegador.
17. O filtro **Resolvidos** mostra apenas anúncios resolvidos com indicação verde; **Em aberto** exclui os concluídos; **Todos** mostra ambos.

## Decisões, limites e pendências

- **Categorias:** Acessórios, Documentos, Eletrônicos, Material de estudo, Roupas e acessórios, Chaves e Outros.
- **Contato:** e-mail e telefone são opcionais individualmente, mas pelo menos um é obrigatório.
- **Prova de controle:** o código comprova acesso ao segredo de gerenciamento; não confirma identidade ou propriedade do objeto.
- **Dados de demonstração:** os objetos e relatos são fictícios e não gerenciáveis por usuários. Na execução local do grupo, um arquivo ignorado pelo Git pode associar contatos autorizados para interação; esses cartões deixam claro que o item é fictício e que o WhatsApp é real.
- **Origem do anúncio:** `is_demo=1` identifica exemplos de demonstração, com ou sem contato local autorizado; publicações enviadas ao formulário têm `is_demo=0` e são rotuladas como “Publicação da comunidade”, sem verificação de autenticidade.
- **IA:** a análise compara candidatos no servidor. Gemini pode ordenar candidatos via variável secreta `GEMINI_API_KEY`; sem chave ou serviço disponível, pontuação local mantém a função utilizável. O Gemini recebe metadados mínimos dos anúncios, sem descrição ou contatos.
- **Privacidade:** publicações reais exibem os dados de contato informados. Contatos locais de demonstração exigem autorização explícita; o botão abre o WhatsApp do número mostrado, e a mensagem só é enviada quando a pessoa confirma o envio.
- **Contato demonstrável:** cartões com contato autorizado usam itens fictícios e abrem uma conversa WhatsApp pré-preenchida para o número indicado; nenhum envio é automático.
- **Fora desta entrega:** contas, autenticação de identidade, moderação, denúncia, notificação, recuperação do código, disponibilidade de produção e preservação de anúncios após reinício do serviço gratuito. A IA não envia mensagens a publicadores nem confirma que um item pertence a alguém.
- **Demonstração na nuvem:** será usada para avaliação acadêmica com conteúdo fictício e sem o arquivo local de contatos. A configuração Render gratuita pode desligar e reiniciar o serviço, apagando SQLite e fotos locais. Não enviar o banco local nem `data/local-demo-contacts.json` para o repositório ou hospedagem.
- **Pendência de validação externa:** comparar esta versão com a rubrica completa do professor antes da entrega acadêmica; essa rubrica não está incluída nos arquivos do projeto disponíveis nesta sessão.

## Referências internas

- Plano: [`plan.md`](plan.md)
- Tarefas: [`tasks.md`](tasks.md)
- Modelo de dados: [`data-model.md`](data-model.md)
- Guia de execução: [`quickstart.md`](quickstart.md)
- Rastreabilidade: [`traceability.md`](traceability.md)
- Checklist da especificação: [`checklists/requirements.md`](checklists/requirements.md)
- Contrato: [`contracts/openapi.yaml`](contracts/openapi.yaml)
