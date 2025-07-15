# DataverseSDK API Reference

Referência completa da classe principal `DataverseSDK`.

## Classe DataverseSDK

```python
from dataverse_sdk import DataverseSDK
```

### Construtor

```python
DataverseSDK(
    dataverse_url: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    tenant_id: Optional[str] = None,
    auth_flow: str = "client_credentials",
    max_connections: int = 100,
    timeout: int = 300,
    retry_attempts: int = 3,
    log_level: str = "INFO",
    log_requests: bool = False
)
```

#### Parâmetros

- **dataverse_url** (`str`, opcional): URL do ambiente Dataverse. Se não fornecido, usa `DATAVERSE_URL` do ambiente.
- **client_id** (`str`, opcional): Client ID do Azure AD. Se não fornecido, usa `AZURE_CLIENT_ID` do ambiente.
- **client_secret** (`str`, opcional): Client Secret do Azure AD. Se não fornecido, usa `AZURE_CLIENT_SECRET` do ambiente.
- **tenant_id** (`str`, opcional): Tenant ID do Azure AD. Se não fornecido, usa `AZURE_TENANT_ID` do ambiente.
- **auth_flow** (`str`): Fluxo de autenticação. Opções: `"client_credentials"`, `"device_code"`, `"interactive"`.
- **max_connections** (`int`): Número máximo de conexões simultâneas.
- **timeout** (`int`): Timeout em segundos para requisições.
- **retry_attempts** (`int`): Número de tentativas em caso de falha.
- **log_level** (`str`): Nível de logging (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`).
- **log_requests** (`bool`): Se deve logar detalhes das requisições.

#### Exemplo

```python
# Usando variáveis de ambiente
sdk = DataverseSDK()

# Configuração explícita
sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
    max_connections=50,
    timeout=600
)
```

## Context Manager

O SDK deve ser usado como context manager para gerenciar conexões adequadamente:

```python
async with DataverseSDK() as sdk:
    # Suas operações aqui
    pass
```

## Métodos CRUD

### create()

Cria um novo registro.

```python
async def create(
    self,
    entity_name: str,
    data: Dict[str, Any],
    return_representation: bool = False
) -> str
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade (ex: "accounts", "contacts")
- **data** (`Dict[str, Any]`): Dados do registro a ser criado
- **return_representation** (`bool`): Se deve retornar os dados do registro criado

#### Retorno

- `str`: ID do registro criado
- `Dict[str, Any]`: Dados completos do registro (se `return_representation=True`)

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Criar conta
    account_id = await sdk.create("accounts", {
        "name": "Minha Empresa",
        "websiteurl": "https://minhaempresa.com",
        "telephone1": "11-99999-9999"
    })
    
    # Criar com retorno completo
    account_data = await sdk.create("accounts", {
        "name": "Outra Empresa"
    }, return_representation=True)
```

### read()

Lê um registro específico.

```python
async def read(
    self,
    entity_name: str,
    record_id: str,
    select: Optional[List[str]] = None,
    expand: Optional[List[str]] = None
) -> Dict[str, Any]
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **record_id** (`str`): ID do registro
- **select** (`List[str]`, opcional): Campos a serem retornados
- **expand** (`List[str]`, opcional): Relacionamentos a expandir

#### Retorno

- `Dict[str, Any]`: Dados do registro

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Ler todos os campos
    account = await sdk.read("accounts", account_id)
    
    # Ler campos específicos
    account = await sdk.read("accounts", account_id, 
        select=["name", "websiteurl", "revenue"]
    )
    
    # Ler com relacionamentos
    contact = await sdk.read("contacts", contact_id,
        select=["fullname", "emailaddress1"],
        expand=["parentcustomerid($select=name)"]
    )
```

### update()

Atualiza um registro existente.

```python
async def update(
    self,
    entity_name: str,
    record_id: str,
    data: Dict[str, Any],
    return_representation: bool = False
) -> Optional[Dict[str, Any]]
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **record_id** (`str`): ID do registro
- **data** (`Dict[str, Any]`): Dados a serem atualizados
- **return_representation** (`bool`): Se deve retornar os dados atualizados

#### Retorno

- `None`: Por padrão
- `Dict[str, Any]`: Dados atualizados (se `return_representation=True`)

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Atualização simples
    await sdk.update("accounts", account_id, {
        "websiteurl": "https://novosite.com",
        "description": "Descrição atualizada"
    })
    
    # Atualização com retorno
    updated_data = await sdk.update("accounts", account_id, {
        "revenue": 1000000
    }, return_representation=True)
```

### delete()

Deleta um registro.

```python
async def delete(
    self,
    entity_name: str,
    record_id: str
) -> None
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **record_id** (`str`): ID do registro

#### Exemplo

```python
async with DataverseSDK() as sdk:
    await sdk.delete("accounts", account_id)
```

### upsert()

Cria ou atualiza um registro baseado em uma chave alternativa.

```python
async def upsert(
    self,
    entity_name: str,
    key_name: str,
    key_value: str,
    data: Dict[str, Any],
    return_representation: bool = False
) -> Dict[str, Any]
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **key_name** (`str`): Nome da chave alternativa
- **key_value** (`str`): Valor da chave alternativa
- **data** (`Dict[str, Any]`): Dados do registro
- **return_representation** (`bool`): Se deve retornar os dados do registro

#### Retorno

- `Dict[str, Any]`: Resultado da operação com informações sobre criação/atualização

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Upsert baseado em email
    result = await sdk.upsert("contacts", "emailaddress1", "joao@email.com", {
        "firstname": "João",
        "lastname": "Silva",
        "telephone1": "11-88888-8888"
    })
    
    print(f"Operação: {result['operation']}")  # 'created' ou 'updated'
    print(f"ID: {result['id']}")
```

## Métodos de Consulta

### query()

Executa consultas OData.

```python
async def query(
    self,
    entity_name: str,
    options: Optional[Dict[str, Any]] = None
) -> QueryResult
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **options** (`Dict[str, Any]`, opcional): Opções de consulta OData

#### Opções de Consulta

```python
options = {
    "select": ["field1", "field2"],           # Campos a retornar
    "filter": "field eq 'value'",             # Filtro OData
    "order_by": ["field1 asc", "field2 desc"], # Ordenação
    "top": 100,                               # Limite de registros
    "skip": 50,                               # Pular registros
    "expand": ["relationship($select=field)"], # Expandir relacionamentos
    "count": True                             # Incluir contagem total
}
```

#### Retorno

- `QueryResult`: Objeto com resultados da consulta

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Consulta simples
    accounts = await sdk.query("accounts")
    
    # Consulta com filtros
    active_accounts = await sdk.query("accounts", {
        "select": ["name", "revenue", "createdon"],
        "filter": "statecode eq 0 and revenue gt 100000",
        "order_by": ["revenue desc"],
        "top": 50
    })
    
    # Consulta com relacionamentos
    contacts_with_accounts = await sdk.query("contacts", {
        "select": ["fullname", "emailaddress1"],
        "expand": ["parentcustomerid($select=name,revenue)"],
        "filter": "parentcustomerid ne null"
    })
    
    # Acessar resultados
    for account in active_accounts.value:
        print(f"{account['name']}: ${account['revenue']}")
    
    print(f"Total de registros: {active_accounts.count}")
```

### fetch_xml()

Executa consultas FetchXML.

```python
async def fetch_xml(
    self,
    fetch_xml: str,
    page_size: int = 5000
) -> List[Dict[str, Any]]
```

#### Parâmetros

- **fetch_xml** (`str`): Query FetchXML
- **page_size** (`int`): Tamanho da página para paginação

#### Retorno

- `List[Dict[str, Any]]`: Lista de registros

#### Exemplo

```python
async with DataverseSDK() as sdk:
    fetchxml = """
    <fetch version="1.0" output-format="xml-platform" mapping="logical">
      <entity name="account">
        <attribute name="name" />
        <attribute name="revenue" />
        <attribute name="createdon" />
        <filter type="and">
          <condition attribute="revenue" operator="gt" value="1000000" />
          <condition attribute="statecode" operator="eq" value="0" />
        </filter>
        <order attribute="revenue" descending="true" />
        <link-entity name="contact" from="parentcustomerid" to="accountid">
          <attribute name="fullname" />
          <attribute name="emailaddress1" />
        </link-entity>
      </entity>
    </fetch>
    """
    
    results = await sdk.fetch_xml(fetchxml)
    
    for record in results:
        print(f"Conta: {record['name']}")
        print(f"Receita: ${record['revenue']}")
```

## Operações em Lote

### bulk_create()

Cria múltiplos registros em lote.

```python
async def bulk_create(
    self,
    entity_name: str,
    data: List[Dict[str, Any]],
    batch_size: int = 1000,
    parallel: bool = True
) -> BulkResult
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **data** (`List[Dict[str, Any]]`): Lista de registros a criar
- **batch_size** (`int`): Tamanho do lote
- **parallel** (`bool`): Execução paralela dos lotes

#### Retorno

- `BulkResult`: Resultado da operação em lote

#### Exemplo

```python
async with DataverseSDK() as sdk:
    contacts_data = [
        {
            "firstname": f"Contato{i}",
            "lastname": "Teste",
            "emailaddress1": f"contato{i}@teste.com"
        }
        for i in range(1, 1001)  # 1000 contatos
    ]
    
    result = await sdk.bulk_create("contacts", contacts_data, 
        batch_size=100, parallel=True
    )
    
    print(f"Criados: {result.successful}")
    print(f"Falhas: {result.failed}")
    print(f"Taxa de sucesso: {result.success_rate:.1f}%")
    
    if result.has_errors:
        print("Primeiros 5 erros:")
        for error in result.errors[:5]:
            print(f"  - {error}")
```

### bulk_update()

Atualiza múltiplos registros em lote.

```python
async def bulk_update(
    self,
    entity_name: str,
    data: List[Dict[str, Any]],
    batch_size: int = 1000,
    parallel: bool = True
) -> BulkResult
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **data** (`List[Dict[str, Any]]`): Lista de registros a atualizar (deve incluir ID)
- **batch_size** (`int`): Tamanho do lote
- **parallel** (`bool`): Execução paralela dos lotes

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Buscar contatos para atualizar
    contacts = await sdk.query("contacts", {
        "select": ["contactid", "jobtitle"],
        "filter": "jobtitle eq null",
        "top": 500
    })
    
    # Preparar atualizações
    updates = [
        {
            "contactid": contact["contactid"],
            "jobtitle": "Cargo Atualizado",
            "description": "Atualizado em lote"
        }
        for contact in contacts.value
    ]
    
    result = await sdk.bulk_update("contacts", updates)
    print(f"Atualizados: {result.successful} contatos")
```

### bulk_delete()

Deleta múltiplos registros em lote.

```python
async def bulk_delete(
    self,
    entity_name: str,
    record_ids: List[str],
    batch_size: int = 1000,
    parallel: bool = True
) -> BulkResult
```

#### Parâmetros

- **entity_name** (`str`): Nome da entidade
- **record_ids** (`List[str]`): Lista de IDs a deletar
- **batch_size** (`int`): Tamanho do lote
- **parallel** (`bool`): Execução paralela dos lotes

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Buscar registros de teste para deletar
    test_accounts = await sdk.query("accounts", {
        "select": ["accountid"],
        "filter": "contains(name, 'Teste')"
    })
    
    ids_to_delete = [acc["accountid"] for acc in test_accounts.value]
    
    result = await sdk.bulk_delete("accounts", ids_to_delete)
    print(f"Deletados: {result.successful} registros")
```

### bulk_upsert()

Executa upsert em múltiplos registros.

```python
async def bulk_upsert(
    self,
    entity_name: str,
    data: List[Dict[str, Any]],
    key_field: str = "id",
    batch_size: int = 1000,
    parallel: bool = True
) -> BulkResult
```

#### Exemplo

```python
async with DataverseSDK() as sdk:
    products_data = [
        {
            "new_sku": f"PROD{i:04d}",
            "name": f"Produto {i}",
            "new_price": 99.99 + i,
            "new_category": "Eletrônicos"
        }
        for i in range(1, 501)
    ]
    
    result = await sdk.bulk_upsert("new_products", products_data, 
        key_field="new_sku"
    )
    
    print(f"Criados: {result.created}")
    print(f"Atualizados: {result.updated}")
```

## Relacionamentos

### associate()

Cria associação entre registros.

```python
async def associate(
    self,
    entity_name: str,
    record_id: str,
    relationship_name: str,
    related_entity_name: str,
    related_record_id: str
) -> None
```

#### Exemplo

```python
async with DataverseSDK() as sdk:
    # Associar contato a uma conta
    await sdk.associate(
        "contacts", contact_id,
        "account_primary_contact",
        "accounts", account_id
    )
```

### disassociate()

Remove associação entre registros.

```python
async def disassociate(
    self,
    entity_name: str,
    record_id: str,
    relationship_name: str,
    related_record_id: str
) -> None
```

## Metadados

### get_entity_metadata()

Obtém metadados de uma entidade.

```python
async def get_entity_metadata(
    self,
    entity_name: str
) -> Dict[str, Any]
```

#### Exemplo

```python
async with DataverseSDK() as sdk:
    metadata = await sdk.get_entity_metadata("accounts")
    
    print(f"Nome da entidade: {metadata['LogicalName']}")
    print(f"Nome de exibição: {metadata['DisplayName']['UserLocalizedLabel']['Label']}")
    
    # Listar atributos
    for attr in metadata['Attributes']:
        print(f"  - {attr['LogicalName']}: {attr['AttributeType']}")
```

### list_entities()

Lista todas as entidades disponíveis.

```python
async def list_entities(self) -> List[Dict[str, Any]]
```

#### Exemplo

```python
async with DataverseSDK() as sdk:
    entities = await sdk.list_entities()
    
    for entity in entities:
        if entity['IsCustomEntity']:
            print(f"Entidade customizada: {entity['LogicalName']}")
```

## Propriedades

### hooks

Gerenciador de hooks para extensibilidade.

```python
sdk.hooks.register('before_request', my_hook_function)
sdk.hooks.register('after_response', my_response_hook)
```

### client

Cliente HTTP interno (AsyncDataverseClient).

```python
# Acessar configurações do cliente
print(f"URL base: {sdk.client.base_url}")
print(f"Timeout: {sdk.client.timeout}")
```

## Exceções

O SDK pode lançar as seguintes exceções:

- `DataverseError`: Erro base do Dataverse
- `AuthenticationError`: Erro de autenticação
- `ValidationError`: Erro de validação de dados
- `RateLimitError`: Rate limit atingido
- `NotFoundError`: Registro não encontrado
- `PermissionError`: Permissão insuficiente

```python
from dataverse_sdk.exceptions import *

try:
    await sdk.create("accounts", invalid_data)
except ValidationError as e:
    print(f"Dados inválidos: {e}")
except AuthenticationError as e:
    print(f"Erro de autenticação: {e}")
except DataverseError as e:
    print(f"Erro do Dataverse: {e}")
```

---

**📚 Veja também:**
- [AsyncDataverseClient](async-client.md) - Cliente HTTP interno
- [Modelos de Dados](models.md) - Estruturas de dados
- [Exceções](exceptions.md) - Tratamento de erros

