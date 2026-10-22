# Evidências de validação — 001-achados-e-perdidos

Use dados fictícios e banco temporário. Esta ficha diferencia resultados históricos da execução mais recente informada pelo grupo.

## Testes automatizados

- **Execução mais recente informada:** 20/10/2026, aproximadamente 09:20 (horário local do terminal).
- **Sistema e versão do Python:** Windows; Python 3.14 (o grupo informou 3.14.8).
- **Comando:** `py -3.14 -m unittest discover -s tests -p "test_*.py" -v`
- **Resultado:** `Ran 17 tests in 5.372s` — `OK`. Os 17 testes passaram.
- **Cobertura exercitada:** validação de domínio, API de saúde e OpenAPI, publicação e busca, persistência, filtros válidos/inválidos, fotos, entradas excessivas e códigos de gerenciamento.
- **Histórico:** execuções anteriores em 19/10 tiveram falhas de limpeza SQLite e uma categoria com acentuação divergente no teste. As correções foram aplicadas. O resultado mais recente acima substitui essas evidências antigas para os testes automatizados.
- **Testes adicionados após essa execução:** quatro cenários automatizados (busca vazia, ordenação, contadores e IDs inexistentes) elevam a suíte atual a 21; ainda não foi possível executar essa versão porque o Python não está instalado no ambiente ligado ao workspace (`py -3.14` informa que não há Python instalado aqui).
- **Verificação HTTP equivalente nesta revisão:** via PowerShell, foram exercitados busca sem resultados, prioridade da ordenação, contadores antes/depois de publicar e resolver, e 404 de PATCH/DELETE. Os três anúncios com dados fictícios foram removidos ao final. Essa verificação manual não substitui a execução da suíte Python.
- **Testes adicionados após essa execução:** quatro cenários automatizados (busca vazia, ordenação, contadores e IDs inexistentes) elevam a suíte atual a 21; ainda não foi possível executar essa versão porque o Python não está instalado no ambiente ligado ao workspace (`py -3.14` informa que não há Python instalado aqui).
- **Verificação HTTP equivalente nesta revisão:** via PowerShell, foram exercitados busca sem resultados, prioridade da ordenação, contadores antes/depois de publicar e resolver, e 404 de PATCH/DELETE. Os três anúncios com dados fictícios foram removidos ao final. Essa verificação manual não substitui a execução da suíte Python.

## Contrato e início do servidor

- O teste automatizado `test_health_and_openapi_route` passou, verificando HTTP 200 em health e `/openapi.yaml` dentro do ambiente de teste.
- **Verificação HTTP local nesta revisão:** `GET /` retornou 200 e o título do portal; `GET /api/v1/health` retornou `{"status":"ok"}`; `GET /openapi.yaml` retornou 200 e iniciou com `openapi: 3.0.3`. O servidor já estava ativo na porta 8000; portanto, isso não comprova uma inicialização limpa pelo quickstart.
- Uma observação manual anterior, em 19/10, encontrou um servidor antigo na porta 8000 que respondia health, mas retornava 404 para `/openapi.yaml`. Essa observação é histórica e não representa a execução automatizada mais recente.
- **Inicialização manual limpa nesta cópia final:** pendente de parar e reiniciar o servidor com `python app/server.py` conforme quickstart.
- A tarefa do VS Code foi preparada para validar health/OpenAPI e iniciar a versão atual em outra porta se houver servidor antigo na 8000. Isso não substitui a verificação manual da interface.

## Revisão manual e publicação

- **Sugestões de correspondência, cores e situação:** a interface agora apresenta sugestões após publicar, motivos e avaliações locais; o servidor mantém pontuação local, com ordenação Gemini opcional e fallback em falha. O filtro Resolvidos, o esquema de cores e os novos fluxos ainda precisam de reinício e verificação manual nos SC-11 a SC-13; rótulos e filtros de origem também precisam da conferência SC-12.
- **Interface no Chrome e viewports 360/768/1366 px:** pendente de execução e registro no `acceptance-manual.md`.
- **URL pública no Render:** ainda não publicada; quando disponível, executar também SC-10 e registrar URL/resultado sem divulgar contatos reais.
- **Aprovador do professor:** não aplicável conforme decisão do grupo; nenhuma aprovação foi presumida.
