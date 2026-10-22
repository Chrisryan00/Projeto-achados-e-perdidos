# Tarefas — 001-achados-e-perdidos

Esta lista registra o trabalho de revisão e verificação que ainda falta na implementação existente. Os itens começam pela decisão humana e pela jornada P1. Uma tarefa só passa a concluída quando seu resultado for verificado e a evidência registrada em `checklists/validation.md` ou `checklists/acceptance-manual.md`.

## P1 — publicar, localizar e permitir contato

- [ ] **T001 — Revisar a spec com o grupo** — [US1] [US4] — **Caminho:** `specs/001-achados-e-perdidos/spec.md` e `specs/001-achados-e-perdidos/checklists/requirements.md`. **Verificação:** integrantes confirmam escopo, prioridades, cenários e limites da demonstração; registrar quem revisou e a data. Não exige aprovação do professor.
- [x] [P] **T002 — Criar testes de regra do anúncio** — [US1] — **Caminho:** `tests/test_domain.py`. **Verificação:** cobrir dados válidos, campos obrigatórios, tipo/categoria, limites incluindo telefone de 30 caracteres, data futura, contato, foto e urgência; suíte completa executada em 2026-10-20, 17 testes aprovados.
- [x] [P] **T003 — Criar teste de integração da jornada P1** — [US1] — **Caminho:** `tests/test_http_api.py`. **Verificação:** com banco temporário, publicar anúncio fictício, encontrá-lo por título/listagem, confirmar contato e código de gerenciamento; checar `201`, dados retornados e persistência após reinício. Teste da jornada passou na suíte completa em 2026-10-20.
- [x] **T004 — Executar e registrar a verificação automatizada da P1** — [US1] — **Caminhos:** `tests/test_domain.py`, `tests/test_http_api.py`, `specs/001-achados-e-perdidos/checklists/validation.md`. **Verificação:** suíte completa executada no Windows com Python 3.14 em 2026-10-20: 17 testes, `OK`; resultado registrado em `checklists/validation.md`.
- [ ] **T005 — Demonstrar a jornada P1 no navegador** — [US1] — **Caminho:** `specs/001-achados-e-perdidos/checklists/acceptance-manual.md`. **Verificação:** em Chrome, usar dados fictícios, publicar, localizar o cartão e acionar o contato; conferir 360, 768 e 1366 px; registrar versão, resultado observado e defeitos.

## P1 — correspondências e origem dos anúncios

- [ ] **T017 — Verificar sugestões explicáveis de correspondência** — [US6] — **Caminhos:** `app/server.py`, `app/main.js`, `app/index.html`, `app/styles.css`, `specs/001-achados-e-perdidos/contracts/openapi.yaml`, `specs/001-achados-e-perdidos/checklists/validation.md`. **Verificação:** comparar um anúncio perdido com encontrados abertos e vice-versa; após publicar, confirmar sugestões na tela de sucesso; conferir no máximo três IDs, razões, botões de avaliação, navegação aos cartões, estado vazio, análise local sem chave, fallback se Gemini falhar e limite `429`; se Gemini estiver configurado, conferir que só metadados básicos são enviados. Não registrar a chave.
- [ ] **T018 — Verificar rótulos e filtros de origem** — [US7] — **Caminhos:** `app/main.js`, `app/index.html`, `app/styles.css`, `specs/001-achados-e-perdidos/checklists/acceptance-manual.md`. **Verificação:** conferir filtro de todos, comunidade e exemplos; confirmar rótulo fictício em todos os cenários e botão de contato somente quando existir contato cadastrado e autorizado.
- [ ] **T019 — Verificar tipos coloridos e seção de resolvidos** — [US2] [US3] — **Caminhos:** `app/index.html`, `app/main.js`, `app/styles.css`, `specs/001-achados-e-perdidos/checklists/acceptance-manual.md`. **Verificação:** opções perdido/vermelho e encontrado/amarelo no formulário e nos cartões; resolver uma publicação própria e confirmar que todo anúncio resolvido aparece na seção verde ao fim do mural; filtros Todos/Em aberto/Resolvidos mostram os estados correspondentes; somente quem possui o código de gerenciamento pode resolver.

## P2 — consulta e acompanhamento

- [x] **T006 — Alinhar validação dos filtros da API e contrato** — [US2] — **Caminhos:** `app/server.py`, `specs/001-achados-e-perdidos/contracts/openapi.yaml`, `specs/001-achados-e-perdidos/spec.md`, `tests/test_http_api.py`. **Verificação:** tipo/categoria/situação válidos filtram; valores não permitidos respondem `400`; contrato e RF-11 descrevem o mesmo comportamento. Testes negativos passaram na execução de 17 testes informada em 20/10/2026.
- [ ] **T007 — Verificar busca, filtros, estados vazios e gerenciamento** — [US2] [US3] — **Caminhos:** `tests/test_http_api.py`, `specs/001-achados-e-perdidos/checklists/acceptance-manual.md`. **Verificação:** cobrir resultado vazio, filtros válidos/inválidos, token incorreto, resolução e remoção; registrar evidência para SC-03 a SC-06 e SC-09.

## P3 — informações adicionais

- [ ] **T008 — Verificar foto e urgência** — [US5] — **Caminhos:** `tests/test_domain.py`, `tests/test_http_api.py`, `specs/001-achados-e-perdidos/checklists/acceptance-manual.md`. **Verificação:** validar formato/tamanho e rota da foto; verificar marca de urgência no anúncio; registrar evidência para SC-07.
- [ ] **T020 — Verificar fotos nos cartões fictícios e contato WhatsApp** — [US5] [US7] — **Caminhos:** `app/server.py`, `app/main.js`, `app/styles.css`, `specs/001-achados-e-perdidos/contracts/openapi.yaml`, `specs/001-achados-e-perdidos/checklists/acceptance-manual.md`. **Verificação:** em execução local, adicionar foto a um cartão fictício e confirmar que ela continua após recarregar; confirmar que cartões da comunidade não têm controle de edição, que uma conexão remota recebe `403` e que cartões oferecem WhatsApp sem botão de e-mail.

## Convergência e entrega

- [ ] **T009 — Reexecutar a suíte completa e verificar quickstart/indisponibilidade** — [US1] — **Caminhos:** `tests/`, `specs/001-achados-e-perdidos/contracts/openapi.yaml`, `specs/001-achados-e-perdidos/quickstart.md`, `specs/001-achados-e-perdidos/checklists/validation.md`, `specs/001-achados-e-perdidos/checklists/acceptance-manual.md`. **Verificação:** após T006–T008, executar `python -m unittest discover -s tests -p "test_*.py"`, iniciar o servidor conforme quickstart, confirmar health e `GET /openapi.yaml`, executar SC-08 e registrar resultados atuais.
- [ ] **T010 — Atualizar rastreabilidade e checklist de entrega** — [US1] [US2] [US3] [US5] — **Caminhos:** `specs/001-achados-e-perdidos/traceability.md`, `specs/001-achados-e-perdidos/checklists/requirements.md`, `specs/001-achados-e-perdidos/checklists/delivery.md`. **Verificação:** cada requisito aponta para critério/cenário, teste ou roteiro, tarefa e evidência; corrigir IDs divergentes; comparar com a rubrica do professor quando o grupo a tiver.

## Demonstração na nuvem — Render

- [x] **T011 — Documentar a demonstração pública e seus limites** — [US4] — **Caminhos:** `specs/001-achados-e-perdidos/spec.md`, `specs/001-achados-e-perdidos/plan.md`, `README.md`. **Verificação:** documentos explicam URL HTTPS esperada, uso de dados fictícios e perda de SQLite/fotos no serviço gratuito; não afirmam que o deploy já existe.
- [x] **T012 — Excluir dados locais do repositório** — [US4] — **Caminho:** `.gitignore`. **Verificação:** banco SQLite e pasta `data/` local estão ignorados; o arquivo compartilhado com contatos não entra no GitHub nem na nuvem.
- [ ] **T013 — Disponibilizar o código sem dados privados em uma fonte aceita pelo Render** — [US4] — **Caminhos:** origem Git conectada ou imagem Docker; `.gitignore`. **Verificação:** a fonte de deploy contém app, testes, SDD, README e `render.yaml`; nenhum SQLite, contato real, token ou segredo foi enviado. GitHub é o caminho mais simples, mas não é a única fonte suportada.
- [ ] **T014 — Criar o serviço pelo Blueprint do Render** — [US4] — **Caminhos:** `render.yaml` e painel Render. **Verificação:** o Render conclui o deploy e fornece URL HTTPS; anotar URL e data em `checklists/validation.md`.
- [ ] **T015 — Validar a versão pública** — [US4] — **Caminhos:** `checklists/validation.md`, `checklists/acceptance-manual.md`, `README.md`. **Verificação:** abrir a URL de uma rede externa, conferir página, `/api/v1/health`, `/openapi.yaml` e fluxo de publicação com contato fictício; registrar o resultado e as limitações do plano gratuito.
- [ ] **T016 — Validar testes adicionais de lacunas da matriz** — [US2] [US3] — **Caminho:** `tests/test_http_api.py`. **Verificação:** executar os quatro novos testes para busca sem resultados, ordenação, IDs inexistentes e contadores; corrigir falhas e atualizar `validation.md` e `traceability.md` com o total efetivamente aprovado.

## Dependências

```text
T001 → [T002 || T003]
T002 + T003 → T004 → T005
T005 → [T006 → T007 → T008 || T017 || T018 || T019]
T005 + T007 + T008 + T016 + T017 + T018 + T019 → T009 → T010
T011 + T012 → T013 → T014 → T015
```

`[P]` marca apenas T002 e T003: após a revisão humana, os testes de domínio e o teste HTTP podem ser escritos em arquivos separados sem dependência entre si. A jornada P1 é verificada antes das tarefas P2/P3; o conjunto completo é executado na convergência.
