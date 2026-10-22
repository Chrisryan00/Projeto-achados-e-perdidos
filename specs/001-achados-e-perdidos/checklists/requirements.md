# Checklist de revisão da especificação

**Especificação:** [`../spec.md`](../spec.md)  
**Tipo de revisão registrada aqui:** análise técnica documental; não equivale à aprovação do PO.  
**Revisor do grupo / data:** pendente de preenchimento pelos integrantes. Aprovação do professor não é requisito deste checklist.  
**Resultado técnico preliminar:** requisitos de produto e cenários estão documentados; os quatro testes adicionais ainda precisam ser executados. Aprovação do professor não é necessária para o grupo.

## Clareza e cobertura

- [x] Problema, público e resultado desejado estão descritos.
- [x] A jornada P1 forma um fluxo demonstrável de publicação, localização e contato.
- [x] Histórias têm prioridade e resultado observável.
- [x] Cenários registram estado inicial, ação e resultado esperado.
- [x] Há sucesso, falha de validação, ausência de resultados, filtros inválidos, autorização, foto e serviço indisponível.
- [x] Requisitos funcionais RF-01 a RF-12 têm identificadores e comportamento verificável.
- [x] RF-13 a RF-16 descrevem correspondências explicáveis com fallback local, avaliações no navegador, filtros de situação e cores; a validação visual continua pendente.
- [x] Requisitos de qualidade RNF-01 a RNF-05 estão numerados de forma consistente, incluindo acesso público HTTPS.
- [x] Limites de campos, foto, requisição, listagem e telefone (30 caracteres) estão documentados.
- [x] Tipos, categorias, estados e resultados de resolução estão definidos.
- [x] Riscos de contato visível, código de gerenciamento, seed fictício e limites locais estão descritos.
- [x] Escolhas de implementação detalhadas foram movidas para o plano/contrato; a spec conserva comportamentos e resultados.

## Consistência entre artefatos

- [x] Spec, contrato e servidor definem HTTP 400 para filtros de tipo, categoria ou situação não permitidos.
- [x] O contrato restringe as enumerações de tipo, categoria e situação.
- [x] O modelo de dados descreve os campos persistidos usados pelo sistema.
- [x] A documentação distingue a intenção `recovered`/`returned` do estado persistido `resolved`.
- [x] O limite de telefone está alinhado entre spec, domínio e contrato.
- [x] A execução anterior confirmou 17 testes em 2026-10-20; quatro novos testes de lacunas aguardam execução (ver `validation.md`).
- [x] `GET /openapi.yaml` foi conferido no servidor local ativo nesta revisão.
- [ ] A sequência completa do quickstart com parada e reinício limpo do servidor foi executada.

## Verificação e privacidade

- [x] Cenários e testes usam dados fictícios.
- [x] Os dados de seed não contêm contatos reais.
- [x] A spec informa que contato de anúncio real aparece no mural.
- [x] A spec informa que Gemini pode receber metadados básicos de candidatos, sem descrição ou contatos; a análise local não exige envio externo.
- [x] Nenhuma credencial ou segredo foi incluído nos requisitos.
- [ ] Jornada P1 validada visualmente nos viewports de 360, 768 e 1366 px.

## Decisão de aprovação

- **Aprovação técnica documental:** revisão preliminar concluída pelo agente; esta revisão não se declara aprovação do PO.
- **Aprovação do professor:** não é exigida pelo grupo.
- **Revisão do grupo:** recomendada para confirmar o escopo, mas não bloqueia a preparação técnica.
- **Pendências de validação:** executar a suíte atual; conferir correspondências e fallback local; opcionalmente configurar chave de teste para validar Gemini; concluir roteiro manual; publicar/validar a URL pública.
