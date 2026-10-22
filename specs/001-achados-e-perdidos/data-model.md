# Modelo de dados — CESMAC Achados & Perdidos

## Persistência

O sistema usa SQLite. Por padrão, o banco fica em `%LOCALAPPDATA%/CESMAC-AchadosPerdidos/items.sqlite3`. A variável `LOST_FOUND_DB` pode apontar para outro arquivo. A aplicação cria ou atualiza as tabelas ao iniciar; a migração atual acrescenta colunas `is_demo` e `photo_data` quando faltam.

## Entidade `listings`

| Campo | Tipo SQLite | Regra e significado |
|---|---|---|
| `id` | INTEGER | Chave primária autoincremental. |
| `kind` | TEXT | `lost` ou `found`. |
| `title` | TEXT | Nome do objeto, obrigatório, até 100 caracteres. |
| `description` | TEXT | Descrição, obrigatória, até 1.500 caracteres. |
| `category` | TEXT | Uma das categorias definidas em `spec.md`. |
| `location` | TEXT | Local relacionado ao relato, até 120 caracteres. |
| `event_date` | TEXT | Data ISO `AAAA-MM-DD`, não futura. |
| `contact_name` | TEXT | Nome informado por quem publica, até 80 caracteres. |
| `contact_email` | TEXT | E-mail opcional; pelo menos e-mail ou telefone deve ser informado. |
| `contact_phone` | TEXT | Telefone opcional; usado também para montar o link de WhatsApp. |
| `urgent` | INTEGER | `0` ou `1`. |
| `status` | TEXT | `open` ou `resolved`; resultado de recuperação/devolução é inferido pelo `kind`. |
| `management_hash` | TEXT | SHA-256 do código de gerenciamento; o código em claro não é armazenado. |
| `created_at` | TEXT | Data/hora de criação em ISO 8601 UTC. |
| `updated_at` | TEXT | Data/hora da alteração mais recente em ISO 8601 UTC. |
| `is_demo` | INTEGER | `1` identifica exemplo fictício sem código gerenciável; `0` identifica publicação criada pelo formulário. Essa marca indica origem técnica, não veracidade comprovada. |
| `photo_data` | TEXT | Data URL Base64 opcional de imagem JPEG, PNG ou WebP. |

## Entidade `app_meta`

| Campo | Tipo SQLite | Regra e significado |
|---|---|---|
| `key` | TEXT | Chave primária do marcador. |
| `value` | TEXT | Valor associado. |

Os marcadores `demo_seeded` e `demo_seeded_v2` impedem que os dados demonstrativos sejam inseridos repetidamente. O seed acrescenta somente títulos ausentes e preserva os demais registros.

## Regras de integridade e acesso

- `management_hash` é calculado a partir de um segredo aleatório gerado na criação. A interface guarda o código por ID no armazenamento local do navegador e permite importá-lo em **Minhas publicações**.
- Anúncios fictícios recebem hash inacessível, sem e-mail ou telefone, e são marcados com `is_demo=1`.
- Publicações criadas pelo formulário ficam com `is_demo=0`; o mural mostra rótulos e filtros separados para exemplos e publicações da comunidade. O sistema não verifica identidade nem autenticidade.
- A API retorna `status: resolved` para uma publicação concluída; a tela usa `kind` para apresentar “recuperado” ou “devolvido”.
- Fotos ficam armazenadas no banco e são servidas pela rota individual do anúncio.
- O índice `idx_listings_status_date` auxilia a consulta por estado e data.

## Retenção e backup

Os dados permanecem no arquivo SQLite até sua remoção manual. O protótipo não implementa expiração, exportação, restauração ou backup automático. Para preservar os anúncios, faça uma cópia do arquivo com o servidor parado.
