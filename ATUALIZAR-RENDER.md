# Atualizar o site e ativar a IA

Endereço informado: https://cesmac-achados-perdidos.onrender.com/

As alterações desta pasta precisam chegar à fonte que o Render usa. Alterar arquivos no VS Code não atualiza o site automaticamente. Esta cópia não contém `.git` nem uma conexão identificável com o repositório remoto.

## 1. Identificar a fonte

Entre em https://dashboard.render.com/ e abra o serviço `cesmac-achados-perdidos`. Na página **Settings**, procure a configuração do repositório e da branch. Copie o endereço do repositório, não chaves, tokens ou variáveis secretas.

Se for um repositório Git, atualize nele os arquivos desta versão, preservando alterações que já existam no remoto. Os arquivos de código são `app/ai_service.py`, `app/assistant.js`, `app/server.py`, `app/main.js`, `app/index.html`, `app/styles.css`, além dos testes e documentação. Não envie `data/`, `.tools/`, `.env`, bancos SQLite ou contatos locais.

O comando inicial continua sendo:

```text
python app/server.py --host 0.0.0.0 --port $PORT
```

## 2. Configurar a chave

Crie uma chave para a Gemini API no Google AI Studio: https://aistudio.google.com/app/apikey

No serviço do Render, abra **Environment** e adicione:

| Key | Value |
| --- | --- |
| `GEMINI_API_KEY` | Sua chave privada, inserida diretamente no painel |
| `GEMINI_MODEL` | `gemini-3.6-flash` |

Não coloque a chave no JavaScript, no Git ou no chat. A aplicação lê variáveis de ambiente; ela não carrega arquivos `.env` automaticamente. A disponibilidade do modelo e a cota dependem da conta do provedor.

Depois de atualizar o código, salve as variáveis com deploy e aguarde o serviço ficar disponível. Se o deploy automático estiver desativado, use **Manual Deploy** para implantar o commit atualizado da branch conectada. Um deploy sem atualizar a fonte não inclui os arquivos locais.

## 3. Verificar

1. Abra `/api/v1/health`: deve responder `{"status":"ok"}`.
2. Abra `/api/v1/ai/status`: `configured: true` significa apenas que há uma chave presente; não testa sua validade.
3. No site, use o assistente, autorize o envio e descreva um item. Uma resposta real terá a identificação **RESPOSTA DO GEMINI**. Erro de chave, cota ou conexão aparece explicitamente.
4. No modo **Preparar anúncio**, envie um relato e opcionalmente uma foto sem dados pessoais. Confira o rascunho, complete local, data e contatos e publique somente depois de revisar.
5. Teste favoritos, buscas salvas, link compartilhado e contato por e-mail. Favoritos e buscas são locais ao navegador; não enviam notificações.
6. No Radar, selecione perdido/encontrado e teste com e sem exemplos fictícios. Os resultados mostram pistas, incertezas e perguntas para conferir o objeto. Uma foto do usuário pode ser analisada; fotos do catálogo não são comparadas.
7. Responda às perguntas de refinamento, acrescente ao relato e consulte novamente. Salve o plano, marque passos concluídos e recarregue a página para conferir a persistência local.

## Limites atuais

- Busca com IA considera até 100 anúncios abertos, priorizando comunidade. O mural carrega até 200 anúncios. Não há garantia de identificação do objeto.
- A busca e o rascunho enviam texto e foto opcional do usuário mediante consentimento. O catálogo não inclui contatos, descrições, códigos ou fotos dos anúncios. Exemplos são excluídos por padrão. O plano é salvo somente no navegador quando solicitado e nunca dispara consultas em segundo plano.
- Os testes automatizados usam respostas simuladas do provedor. A validação real exige uma chave e uma consulta bem-sucedida no ambiente configurado.
- O limite é de 8 análises/minuto por endereço de conexão, compartilhado com correspondências. Atrás do proxy do Render, visitantes podem compartilhar o limite. Para uso amplo, adote armazenamento de cotas compartilhado e identificação confiável no proxy.
- O Render atual usa SQLite em `/tmp`: anúncios e fotos podem desaparecer em reinícios e deploys. Para conservar publicações, será preciso configurar armazenamento persistente ou migrar para um banco gerenciado. Esta atualização não muda o plano nem cria serviços pagos.

Documentação consultada: [Deploys no Render](https://render.com/docs/deploys), [variáveis de ambiente no Render](https://render.com/docs/configure-environment-variables), [modelos Gemini](https://ai.google.dev/gemini-api/docs/models), [respostas estruturadas Gemini](https://ai.google.dev/gemini-api/docs/structured-output).
