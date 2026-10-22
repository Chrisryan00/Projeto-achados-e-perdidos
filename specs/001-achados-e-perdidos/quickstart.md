# Guia rápido — CESMAC Achados & Perdidos

## Requisitos

- Windows, macOS ou Linux com Python 3.9 ou superior.
- Navegador moderno.
- Para ordenar possíveis correspondências com Gemini: uma chave Gemini opcional. As sugestões por pontuação local funcionam mesmo sem a chave.
- Não precisa instalar bibliotecas Python externas.

## Executar pelo terminal

Na raiz do projeto, execute:

```powershell
python app/server.py
```

Quando aparecer `CESMAC Achados & Perdidos disponível em http://127.0.0.1:8000`, abra esse endereço no navegador. Para encerrar o servidor, volte ao terminal em que ele foi iniciado e pressione **Ctrl + C**. Se a porta 8000 já estiver ocupada, inicie em outra porta com `python app/server.py --port 8001` e abra `http://127.0.0.1:8001`.

## Habilitar ordenação Gemini (opcional)

1. Crie uma chave em [Google AI Studio](https://aistudio.google.com/app/apikey). Não cole a chave em arquivos do projeto, no navegador ou no GitHub.
2. No mesmo PowerShell em que vai iniciar o servidor, defina a variável e inicie a aplicação:

```powershell
$env:GEMINI_API_KEY = "SUA_CHAVE"
python app/server.py
```

O modelo padrão é `gemini-3.6-flash`; para trocar, defina `GEMINI_MODEL` antes de iniciar. Sem chave, o sistema usa pontuação local e continua sugerindo possíveis correspondências.

## Executar pelo VS Code

1. Abra a pasta raiz do projeto no VS Code.
2. Pressione **Ctrl + Shift + B**.
3. Selecione **Abrir CESMAC no Chrome**.
4. A tarefa verifica/inicia o servidor em segundo plano e abre o endereço local no Chrome.

A mensagem de terminal reutilizado após abrir o Chrome indica que a tarefa terminou; o servidor foi iniciado em segundo plano. Para consultar os logs, veja `%TEMP%/cesmac-achados-server.log` e `%TEMP%/cesmac-achados-server-error.log`. A tarefa verifica `/api/v1/health` e `/openapi.yaml`; se um servidor antigo responder na porta 8000, inicia a versão atual na porta 8001.

## Verificar a API

Com o servidor ativo, abra:

- `http://127.0.0.1:8000/api/v1/health` — deve retornar `{"status":"ok"}`.
- `http://127.0.0.1:8000/openapi.yaml` — deve exibir o contrato de [`contracts/openapi.yaml`](contracts/openapi.yaml).

## Usar o mural

1. Clique em **Publicar item** e escolha se perdeu ou encontrou o objeto.
2. Preencha os dados e informe pelo menos um e-mail ou telefone. Use dados fictícios em apresentações.
3. Opcionalmente, anexe uma foto e marque urgência.
4. Após publicar, guarde o código de gerenciamento. Ele permite resolver ou remover o anúncio.
5. Pesquise ou filtre os anúncios no mural. Use **Minhas publicações** para consultar publicações cujo código está salvo ou importar o código manualmente.
6. Use **Mostrar** para alternar entre todos os anúncios, publicações feitas pela comunidade e exemplos fictícios. “Publicação da comunidade” descreve a origem do formulário; o sistema não verifica a identidade de quem publicou. Só inclua contato de amigos com a autorização deles.
7. Depois de publicar, confira as possíveis correspondências que aparecem na confirmação. No mural, qualquer anúncio aberto também tem a ação **Ver possíveis correspondências**. As sugestões mostram motivos e permitem marcar **Pode ser** ou **Não é meu item**; essas avaliações ficam somente neste navegador. Use os filtros **Todos**, **Em aberto** e **Resolvidos** para acompanhar o estado.
8. As sugestões são possibilidades, não confirmação de que seja o mesmo objeto. Gemini é opcional; sem chave, a pontuação local mantém a busca disponível. Quando Gemini é usado, ele recebe somente título, tipo, categoria, local e data, nunca contato, descrição, foto ou código de gerenciamento.

## Banco e limites

O banco padrão fica em `%LOCALAPPDATA%/CESMAC-AchadosPerdidos/items.sqlite3`. Para mudar o caminho, defina `LOST_FOUND_DB` antes de iniciar o servidor. O sistema é local e escuta em `127.0.0.1`; não exponha este servidor diretamente à internet.

Na publicação no Render, `GEMINI_API_KEY` pode ser definida nos segredos/variáveis de ambiente do serviço. Sem ela, a pontuação local permanece disponível. O `render.yaml` registra a variável como segredo não sincronizado, nunca inclui o valor. Consulte [como usar chaves Gemini](https://ai.google.dev/gemini-api/docs/generate-content/api-key) e [como configurar segredos no Render](https://render.com/docs/configure-environment-variables).
