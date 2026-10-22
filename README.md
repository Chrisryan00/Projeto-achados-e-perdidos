# CESMAC Achados & Perdidos

Portal local para conectar pessoas da comunidade CESMAC que perderam ou encontraram objetos. Publique um anúncio, encontre itens no mural e fale diretamente com quem publicou.

## Sobre o projeto

O CESMAC Achados & Perdidos é um protótipo acadêmico que organiza anúncios de itens perdidos e encontrados. Cada publicação informa o tipo do anúncio, nome e descrição do item, categoria, local, data e uma forma de contato. Os anúncios ficam em um banco SQLite local.

O site inclui busca e filtros, destaque para anúncios urgentes e um fluxo para marcar um item como recuperado ou devolvido. Quem publica recebe um código de gerenciamento, usado para marcar o anúncio como resolvido ou removê-lo. O código é salvo neste navegador e também pode ser importado em **Minhas publicações**.

## Integrantes

- Aloisio Guedes
- Igor Alcantara

## Funcionalidades

- Publicar itens perdidos ou encontrados.
- Anexar uma foto JPG, PNG ou WebP ao anúncio; a imagem é compactada no navegador e armazenada no SQLite local.
- Adicionar ou trocar a foto dos cartões fictícios e, localmente, do cartão “Mochila preta” de Christian Lopes.
- Exibir o nome informado por quem publicou e um avatar com suas iniciais.
- Informar categoria, descrição, local, data e contato por e-mail ou telefone.
- Marcar um anúncio como urgente.
- Pesquisar por nome, descrição, categoria e local.
- Filtrar por categoria e por itens perdidos ou encontrados.
- Separar no mural as publicações da comunidade dos exemplos fictícios.
- Ver sugestões de possíveis correspondências entre um anúncio perdido e anúncios encontrados (ou vice-versa), com IA opcional e análise local de fallback.
- Ver por que cada anúncio foi sugerido e registrar **Pode ser** ou **Não é meu item** no navegador.
- Consultar anúncios em aberto, resolvidos ou todos pelo filtro de situação.
- Diferenciar visualmente itens perdidos em vermelho, encontrados em amarelo e resolvidos em verde.
- Ver contadores de itens perdidos, encontrados e casos resolvidos.
- Carregar 16 anúncios fictícios em um banco novo e acrescentar os que faltam em bancos existentes, sem apagar publicações reais.
- Contatar a pessoa que publicou por e-mail ou WhatsApp.
- Gerenciar as próprias publicações com um código privado: marcar como resolvido ou remover.
- Consultar uma API REST e seu contrato OpenAPI.

## Tecnologias

- **Backend:** Python 3.9+ e biblioteca padrão (`http.server`, `sqlite3`).
- **Frontend:** HTML, CSS e JavaScript nativos.
- **Banco de dados:** SQLite.
- **Contrato da API:** OpenAPI 3.0 em YAML.
- **Análise de correspondências com IA (opcional):** Gemini API chamada pelo servidor; sem chave ou se o provedor falhar, a pontuação local continua funcionando. `GEMINI_API_KEY` nunca fica no JavaScript.

Não é necessário instalar pacotes Python externos.

## Como executar

### Requisitos

- Python 3.9 ou superior.
- Navegador moderno.
- Para ordenação semântica via Gemini: uma chave opcional; sem ela, as sugestões usam análise local.

### Pelo terminal

Abra o terminal na pasta raiz do projeto e execute:

```powershell
python app/server.py
```

Quando o terminal mostrar que o portal está disponível, abra [http://127.0.0.1:8000](http://127.0.0.1:8000) no navegador. Para parar o servidor, volte ao terminal e pressione **Ctrl + C**.

Para habilitar a ordenação semântica das correspondências, crie uma chave no [Google AI Studio](https://aistudio.google.com/app/apikey), pare o servidor se estiver rodando e execute no PowerShell:

```powershell
$env:GEMINI_API_KEY = "SUA_CHAVE"
python app/server.py
```

Não salve a chave no código, no `main.js`, no README ou no repositório. No Render, configure `GEMINI_API_KEY` como variável secreta do serviço. O modelo padrão é `gemini-3.6-flash` e pode ser alterado pela variável `GEMINI_MODEL`.

### Pelo Visual Studio Code

Com a pasta do projeto aberta no VS Code, pressione **Ctrl + Shift + B** e escolha **Abrir CESMAC no Chrome**. A tarefa inicia o servidor em segundo plano se necessário, espera a API responder e então abre o site. A mensagem de terminal reutilizado indica que a tarefa de abertura terminou; o servidor continua rodando em segundo plano. O log fica em `%TEMP%/cesmac-achados-server.log`.

## API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/v1/health` | Confere se a API está ativa. |
| `GET` | `/api/v1/items` | Lista anúncios e contadores; aceita filtros `q`, `kind`, `category` e `status`. |
| `GET` | `/api/v1/items/{id}/photo` | Retorna a foto anexada ao anúncio, quando houver. |
| `POST` | `/api/v1/items/{id}/matches` | Sugere até três anúncios abertos do tipo oposto; usa Gemini se configurado e pontuação local como fallback. |
| `POST` | `/api/v1/items` | Cria um anúncio e devolve o código de gerenciamento uma única vez. |
| `PATCH` | `/api/v1/items/{id}` | Marca o anúncio como recuperado ou devolvido, com código válido. |
| `DELETE` | `/api/v1/items/{id}` | Remove o anúncio com código válido. |
| `GET` | `/openapi.yaml` | Exibe o contrato OpenAPI. |

O contrato também está em [`specs/001-achados-e-perdidos/contracts/openapi.yaml`](specs/001-achados-e-perdidos/contracts/openapi.yaml).

## Testes

Execute a suíte automatizada na raiz do projeto:

```powershell
py -3.14 -m unittest discover -s tests -p "test_*.py" -v
```

Execução informada pelo grupo em 20/10/2026: **17 testes passaram** (`OK`). Depois disso, foram adicionados quatro testes para busca sem resultados, ordenação, contadores e IDs inexistentes. Uma verificação HTTP manual desses cenários passou, mas a suíte atual de 21 testes ainda precisa ser executada. Todos os testes usam banco temporário.

## Arquitetura

```mermaid
flowchart LR
  P[Pessoa da comunidade] --> W[Site HTML, CSS e JavaScript]
  W -->|HTTP e JSON| API[Servidor local Python]
  API --> R[Validação e regras do domínio]
  API --> DB[(SQLite local)]
  API -->|metadados básicos opcionais| AI[Gemini API]
  W -->|Busca e contato| M[Mural de anúncios]
```

Por padrão, o servidor escuta em `127.0.0.1` para uso local. O `render.yaml` prepara uma publicação pública para demonstração acadêmica; ela ainda precisa ser implantada e testada antes de haver uma URL para compartilhar.

## Publicar uma demonstração na internet (Render)

O arquivo `render.yaml` configura o serviço Python para o Render. A publicação ainda não foi feita. O Render precisa obter o código de um repositório Git conectado, de uma URL Git pública ou de uma imagem Docker; esta cópia não tem um repositório Git configurado. Você não precisa usar GitHub especificamente, mas precisa colocar o código em uma fonte que o Render consiga acessar. O Blueprint deste projeto é criado a partir de um repositório Git:

1. Coloque os arquivos do projeto em um repositório Git acessível ao Render (GitHub, GitLab ou outro provedor conectado), sem a pasta `data/` nem bancos SQLite locais. O `.gitignore` já exclui esses dados.
2. Entre em https://render.com e conecte o provedor Git que contém o repositório.
3. Escolha **New +** > **Blueprint** e selecione o repositório. O Render lê `render.yaml`; confirme a criação do serviço.
4. Aguarde o deploy e abra a URL `*.onrender.com` que aparece no painel do serviço. Compartilhe a URL somente depois de verificar a página, `/api/v1/health` e `/openapi.yaml`.

O serviço usa o plano gratuito e SQLite temporário. Os anúncios de demonstração são criados na inicialização, mas anúncios publicados e fotos podem ser apagados quando o serviço reiniciar, for atualizado ou desligar por inatividade. Isso serve para uma apresentação; para conservar dados entre reinícios, será necessário configurar armazenamento persistente ou migrar para um banco gerenciado, possivelmente com custo. O primeiro acesso pode demorar enquanto o serviço gratuito inicia.

Antes de publicar, confira os dados do mural. Os cartões com o selo “WhatsApp real · demo” têm item fictício, mas o contato é real: o botão abre uma conversa com o titular do número. Eles foram incluídos com autorização para demonstração local; não publique o banco em uma hospedagem pública sem nova autorização. O portal não tem contas de usuário nem moderação.

## Dados e privacidade

O SQLite padrão é criado em `%LOCALAPPDATA%/CESMAC-AchadosPerdidos/items.sqlite3` e fica fora do repositório. O seed cria itens fictícios; sete cartões locais usam os contatos autorizados guardados em `data/local-demo-contacts.json`, arquivo privado ignorado pelo Git. Eles recebem o selo “WhatsApp real · demo”; os demais exemplos são resolvidos e não mostram contato. O botão abre uma conversa com o titular do número, mas só envia a mensagem após confirmação no WhatsApp. Publicações da comunidade também exibem os contatos informados por quem publica. A análise Gemini opcional recebe somente metadados básicos de anúncios e nunca nomes, descrições, fotos, contatos ou códigos de gerenciamento. As sugestões são possibilidades e não comprovam que dois anúncios falam do mesmo item. As respostas **Pode ser** e **Não é meu item** ficam salvas apenas no navegador e não treinam o modelo.

## Estrutura

```text
app/
  domain.py    # Validação dos dados do anúncio
  index.html   # Interface do portal
  main.js      # Busca, filtros e interação com a API
  server.py    # API REST, arquivos estáticos e persistência SQLite
  styles.css   # Estilos responsivos
specs/
  constitution.md
  001-achados-e-perdidos/
    spec.md
    plan.md
    tasks.md
    data-model.md
    quickstart.md
    traceability.md
    checklists/
      requirements.md
      acceptance-manual.md
      delivery.md
      validation.md
    contracts/openapi.yaml
```

O projeto não foi publicado ainda. A configuração cloud é para demonstração e não representa um serviço público de produção.
