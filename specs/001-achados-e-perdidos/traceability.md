# Rastreabilidade — 001-achados-e-perdidos

Em 2026-10-20, o grupo executou a versão anterior da suíte no Windows com Python 3.14: 17 testes passaram (`OK`). Quatro testes adicionais foram escritos nesta revisão, elevando a suíte para 21 testes, mas ainda não foram executados. A aceitação manual e a publicação continuam pendentes; nenhuma tarefa é concluída sem evidência em `checklists/validation.md` ou `checklists/acceptance-manual.md`.

| Requisito | História | Critério/cenário | Teste ou evidência | Tarefa |
|---|---|---|---|---|
| RF-01 — tipos permitidos | US1 | SC-01, critério 1 | `tests/test_domain.py::test_accepts_lost_and_found_and_normalizes_date` — passou na suíte de 2026-10-20 | T002 |
| RF-02 — dados obrigatórios, data e contato | US1 | SC-01, SC-02 | `tests/test_domain.py::test_requires_supported_kind_category_and_contact`, `test_rejects_future_date` — passaram na suíte de 2026-10-20 | T002 |
| RF-03 — limites dos campos | US1 | SC-02 | `tests/test_domain.py::test_enforces_text_field_limits`, `test_accepts_phone_at_30_characters_and_rejects_31` — passaram na suíte de 2026-10-20 | T002 |
| RF-04 — foto aceita e limitada | US5 | SC-07 | `tests/test_domain.py::test_validates_photo_format_and_size`, `tests/test_http_api.py::test_photo_route_returns_uploaded_image` — passaram na suíte de 2026-10-20; roteiro SC-07 pendente | T008 |
| RF-05 — consulta e filtros | US2 | SC-03, SC-04, SC-09 | Filtros válidos/inválidos passaram na execução de 17 testes; `test_search_with_no_matches_returns_empty_list` foi adicionado e aguarda execução; aceitação manual pendente | T006–T007, T016 |
| RF-06 — ordenação | US2 | SC-04 | `test_list_order_prioritizes_open_urgent_and_newer_items` foi adicionado e aguarda execução; inspeção manual também pendente | T007, T016 |
| RF-07 — limite de lista e contadores | US2 | SC-04 | `test_counters_include_all_records_and_update_after_resolution` foi adicionado e aguarda execução; limite máximo 200 ainda não tem teste dedicado | T007, T016 |
| RF-08 — código de gerenciamento protegido | US1, US3 | SC-01, SC-05 | `test_publish_find_contact_and_persist_after_restart` conferiu retorno inicial, hash persistido e ausência na listagem; passou em 2026-10-20 | T003, T005 |
| RF-09 — autorização e inexistência | US3 | SC-05 | `test_wrong_management_code_cannot_resolve_item` cobriu 403 e passou; `test_missing_item_returns_404_for_resolve_and_delete` foi adicionado e aguarda execução | T007, T016 |
| RF-10 — resolução conforme tipo | US3 | SC-06 | `tests/test_http_api.py::test_valid_management_code_resolves_lost_and_found_items` passou em 2026-10-20 | T007 |
| RF-11 — entradas, filtros e corpo inválidos | US1, US2 | SC-02, SC-09 | `test_rejects_invalid_creation`, `test_rejects_invalid_status_kind_and_category_filters`, `test_oversized_request_returns_413` passaram em 2026-10-20 | T003, T006, T009 |
| RF-12 — operações documentadas da API | US1, US2, US3, US5 | SC-01, SC-06, SC-07, SC-08 | `tests/test_http_api.py::test_health_and_openapi_route` e os testes HTTP passaram em 2026-10-20; quickstart manual pendente | T003, T007–T009 |
| RNF-01 — privacidade e minimização no envio ao Gemini | US6 | SC-11, critério 14 | Revisão de código: Gemini recebe apenas IDs e campos básicos de anúncios; inspeção em execução ainda pendente | T017 |
| RNF-02 — proteção do código | US1, US3 | SC-05, SC-06 | Testes de token incorreto/correto acima passaram em 2026-10-20 | T003, T007 |
| RNF-03 — compatibilidade/responsividade | US1 | SC-01 | Chrome em 360, 768 e 1366 px; resultado manual pendente | T005 |
| RNF-04 — mensagem de indisponibilidade | US1 | SC-08 | Roteiro manual no navegador; pendente | T009 |
| RNF-05 — URL pública HTTPS e health | US4 | SC-10, critério 12 | Deploy Render, acesso por rede externa e health check; pendentes | T014–T015 |
| RF-13 — correspondências entre tipos opostos, fallback e limite | US6 | SC-11, critérios 13–14 | Nova rota `/api/v1/items/{id}/matches`; verificar lista local, ordenação Gemini, limite e navegação manualmente | T017 |
| RF-14 — origem e filtro para exemplos/comunidade | US7 | SC-12, critério 15 | Código de interface implementado; conferir visualmente com seed e publicação feita pelo formulário | T018 |
| RF-15 — explicar e avaliar sugestão | US6 | SC-11, critério 16 | Conferir razões, ações Pode ser/Não é meu item e armazenamento local no Chrome | T017 |
| RF-16 — filtrar estados com indicação visual | US2, US3 | SC-04, SC-06, SC-13, critério 17 | Conferir filtros Todos/Em aberto/Resolvidos, cores e mudança automática após resolução autorizada | T019 |

## Implementação relacionada

- Regras do domínio: `app/domain.py`.
- API, filtros, SQLite e contrato servido: `app/server.py`.
- Interface e contato: `app/index.html`, `app/main.js`, `app/styles.css`.
- Contrato: `specs/001-achados-e-perdidos/contracts/openapi.yaml`.
- Evidência de execução: `specs/001-achados-e-perdidos/checklists/validation.md`.

## Lacunas conhecidas

- A suíte automatizada passou com 17 testes em 2026-10-20; a evidência está em `checklists/validation.md`.
- Quatro testes adicionais para busca vazia, ordenação, contadores e ID inexistente aguardam execução; faltam ainda teste do limite de 200 registros e evidência de privacidade/tráfego externo.
- A jornada visual, os viewports e a conferência atual do quickstart dependem de execução no ambiente do grupo.
- O deploy do Render e a validação pública estão pendentes; a configuração gratuita não preserva SQLite/fotos após reinício ou suspensão.
- A correspondência local não depende de credenciais; o reordenamento Gemini não foi exercitado nesta sessão. Verificar fallback, limite, IDs e privacidade no roteiro; a validação do provedor é opcional e requer chave de teste.
- O filtro de origem e os cartões foram implementados, mas a verificação visual e o uso de anúncios de amigos com autorização ainda estão pendentes.
- A revisão do escopo pelo grupo e a comparação com a rubrica (se disponível) continuam pendentes; aprovação do professor não é necessária.
