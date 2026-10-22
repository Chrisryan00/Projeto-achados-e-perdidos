# Checklist de entrega — 001-achados-e-perdidos

Esta checklist acompanha a convergência entre a implementação e os artefatos SDD. Itens de execução só são marcados após observar o resultado no ambiente indicado.

## Documentos e consistência

- [x] Artefatos da funcionalidade estão em `specs/001-achados-e-perdidos/`.
- [x] Links relativos dos artefatos foram conferidos.
- [x] O README aponta para o contrato OpenAPI no caminho atual.
- [x] A rota `GET /openapi.yaml` está presente no código e no contrato.
- [x] Spec, contrato e servidor definem rejeição de filtros inválidos de tipo, categoria e situação.
- [x] A checklist de requisitos não declara RNF-07 inexistente.
- [x] O projeto documenta dados fictícios e limitações de privacidade e persistência.
- [x] A configuração para demonstração no Render está preparada; isso não significa que o serviço foi publicado.
- [x] A sugestão de correspondências funciona com análise local e pode usar Gemini se houver chave; validação de SC-11 ainda pendente.
- [x] Os anúncios têm rótulos e filtro para exemplos fictícios e publicações da comunidade; a origem não verifica autenticidade.
- [x] A aprovação do professor não é requisito para esta entrega; nenhuma aprovação foi inventada.

## Evidências

- [x] Execução da versão anterior informada pelo grupo em 20/10/2026 com Python 3.14: 17 testes passaram (`OK`, 5,372 s), registrada em `checklists/validation.md`.
- [ ] Quatro testes adicionais foram incluídos desde então; executar a suíte atual de 21 testes e registrar o resultado.
- [x] Conferir endpoints no servidor local que já estava ativo: página inicial 200, health `ok` e `/openapi.yaml` 200 com OpenAPI 3.0.3; registrado em `checklists/validation.md`.
- [ ] Parar e iniciar a aplicação pelo quickstart nesta cópia final; a checagem do servidor já ativo não comprova início limpo.
- [ ] Executar o roteiro manual em Chrome e preencher resultados observados, navegador e viewports.
- [ ] Verificar sugestões com análise local; opcionalmente configurar `GEMINI_API_KEY` somente no ambiente local/Render e conferir os metadados enviados sem registrar a chave.
- [ ] Fazer revisão interna do escopo e dos artefatos pelo grupo, se desejado; não exige aprovação do professor.
- [ ] Publicar pelo Render a partir de uma fonte Git conectada ou uma imagem Docker; a publicação exige conta conectada e código remoto.
- [ ] Após publicação, abrir a URL HTTPS, `/api/v1/health` e `/openapi.yaml` de outro navegador/dispositivo e registrar a evidência.
- [ ] Fechar as lacunas de cobertura de menor prioridade listadas em `traceability.md` ou registrá-las como limitações aceitas pelo grupo.

## Resultado atual

**Entrega ainda não concluída.** A versão anterior da suíte teve 17 testes aprovados. Quatro testes novos aguardam execução; a checagem manual da interface e a publicação pública também estão pendentes. A aprovação do professor não é uma pendência deste checklist.
