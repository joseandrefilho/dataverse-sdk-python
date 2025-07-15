# Quick Start Guide

Este guia mostra como começar a usar o **crmadminbrasil-dataverse-sdk** SDK em poucos minutos.

## 🚀 Instalação Rápida

```bash
pip install crmadminbrasil-dataverse-sdk
```

## 🔑 Configuração Básica

### 1. Obter Credenciais

Você precisa de um **Azure AD App Registration** com permissões para o Dataverse:

1. Acesse [Azure Portal](https://portal.azure.com)
2. Vá para **Azure Active Directory** → **App registrations**
3. Clique em **New registration**
4. Configure as permissões necessárias

### 2. Configurar Variáveis de Ambiente

```bash
# Linux/macOS
export DATAVERSE_URL="https://yourorg.crm.dynamics.com"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"

# Windows
set DATAVERSE_URL=https://yourorg.crm.dynamics.com
set AZURE_CLIENT_ID=your-client-id
set AZURE_CLIENT_SECRET=your-client-secret
set AZURE_TENANT_ID=your-tenant-id
```

### 3. Arquivo .env (Opcional)

```bash
# .env
DATAVERSE_URL=https://yourorg.crm.dynamics.com
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

## 💻 Primeiro Código

### Exemplo Básico

```python
import asyncio
from dataverse_sdk import DataverseSDK

async def main():
    # Criar instância do SDK
    sdk = DataverseSDK()
    
    # Usar context manager para gerenciar conexões
    async with sdk:
        
        # 1. Criar uma conta
        print("🔄 Criando nova conta...")
        account_data = {
            "name": "Minha Empresa Teste",
            "websiteurl": "https://minhaempresa.com",
            "telephone1": "11-99999-9999",
            "description": "Conta criada via SDK"
        }
        
        account_id = await sdk.create("accounts", account_data)
        print(f"✅ Conta criada com ID: {account_id}")
        
        # 2. Ler a conta criada
        print("🔄 Lendo dados da conta...")
        account = await sdk.read("accounts", account_id)
        print(f"✅ Nome da conta: {account['name']}")
        
        # 3. Atualizar a conta
        print("🔄 Atualizando conta...")
        update_data = {
            "description": "Conta atualizada via SDK",
            "websiteurl": "https://minhaempresa.com.br"
        }
        
        await sdk.update("accounts", account_id, update_data)
        print("✅ Conta atualizada com sucesso")
        
        # 4. Consultar contas
        print("🔄 Consultando contas...")
        accounts = await sdk.query("accounts", {
            "select": ["name", "websiteurl", "createdon"],
            "filter": "contains(name, 'Teste')",
            "top": 5
        })
        
        print(f"✅ Encontradas {len(accounts.value)} contas:")
        for acc in accounts.value:
            print(f"   - {acc['name']}")
        
        # 5. Deletar a conta (limpeza)
        print("🔄 Deletando conta de teste...")
        await sdk.delete("accounts", account_id)
        print("✅ Conta deletada")
        
        print("🎉 Exemplo concluído com sucesso!")

# Executar exemplo
if __name__ == "__main__":
    asyncio.run(main())
```

## 🎯 Exemplos por Funcionalidade

### CRUD Operations

```python
async def crud_examples():
    sdk = DataverseSDK()
    
    async with sdk:
        
        # CREATE
        contact_data = {
            "firstname": "João",
            "lastname": "Silva",
            "emailaddress1": "joao.silva@email.com",
            "telephone1": "11-88888-8888"
        }
        contact_id = await sdk.create("contacts", contact_data)
        
        # READ
        contact = await sdk.read("contacts", contact_id, 
            select=["fullname", "emailaddress1"]
        )
        
        # UPDATE
        await sdk.update("contacts", contact_id, {
            "jobtitle": "Desenvolvedor"
        })
        
        # DELETE
        await sdk.delete("contacts", contact_id)

asyncio.run(crud_examples())
```

### Bulk Operations

```python
async def bulk_examples():
    sdk = DataverseSDK()
    
    async with sdk:
        
        # Criar múltiplos contatos
        contacts_data = [
            {
                "firstname": f"Contato{i}",
                "lastname": "Teste",
                "emailaddress1": f"contato{i}@teste.com"
            }
            for i in range(1, 11)  # 10 contatos
        ]
        
        # Bulk create
        result = await sdk.bulk_create("contacts", contacts_data)
        print(f"Criados: {result.successful}, Falhas: {result.failed}")
        
        # Bulk update
        updates = [
            {
                "contactid": contact_id,
                "jobtitle": "Cargo Atualizado"
            }
            for contact_id in result.created_ids[:5]  # Primeiros 5
        ]
        
        update_result = await sdk.bulk_update("contacts", updates)
        print(f"Atualizados: {update_result.successful}")

asyncio.run(bulk_examples())
```

### Queries Avançadas

```python
async def query_examples():
    sdk = DataverseSDK()
    
    async with sdk:
        
        # Query básica
        accounts = await sdk.query("accounts", {
            "select": ["name", "revenue"],
            "filter": "revenue gt 1000000",
            "order_by": ["revenue desc"],
            "top": 10
        })
        
        # Query com relacionamentos
        contacts_with_accounts = await sdk.query("contacts", {
            "select": ["fullname", "emailaddress1"],
            "expand": ["parentcustomerid($select=name)"],
            "filter": "parentcustomerid ne null"
        })
        
        # Query com paginação
        all_accounts = await sdk.query("accounts", {
            "select": ["name"],
            "top": 5000  # SDK gerencia paginação automaticamente
        })

asyncio.run(query_examples())
```

### FetchXML

```python
async def fetchxml_examples():
    sdk = DataverseSDK()
    
    async with sdk:
        
        fetchxml = """
        <fetch version="1.0" output-format="xml-platform" mapping="logical">
          <entity name="account">
            <attribute name="name" />
            <attribute name="revenue" />
            <filter type="and">
              <condition attribute="revenue" operator="gt" value="500000" />
              <condition attribute="statecode" operator="eq" value="0" />
            </filter>
            <order attribute="revenue" descending="true" />
          </entity>
        </fetch>
        """
        
        result = await sdk.fetch_xml(fetchxml)
        print(f"Encontradas {len(result)} contas com receita > $500k")

asyncio.run(fetchxml_examples())
```

## 🖥️ CLI Quick Start

### Configurar CLI

```bash
# Configuração inicial
dv-cli config init

# Ou configurar manualmente
dv-cli config set dataverse_url "https://yourorg.crm.dynamics.com"
dv-cli config set client_id "your-client-id"
dv-cli config set client_secret "your-client-secret"
dv-cli config set tenant_id "your-tenant-id"
```

### Comandos Básicos

```bash
# Listar entidades
dv-cli entity list accounts --top 10

# Criar entidade
echo '{"name": "Nova Empresa", "websiteurl": "https://nova.com"}' | dv-cli entity create accounts

# Consultar com filtro
dv-cli entity query accounts --filter "contains(name, 'Test')" --select name,websiteurl

# Operações em lote
dv-cli bulk create contacts --file contacts.json --batch-size 50

# Executar FetchXML
dv-cli fetchxml execute --file query.xml --output results.json

# Exportar dados
dv-cli data export accounts --output accounts.csv --format csv
```

## 🔧 Configuração Avançada

### SDK com Configurações Customizadas

```python
from dataverse_sdk import DataverseSDK

# Configuração customizada
sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
    
    # Configurações de performance
    max_connections=50,
    timeout=300,
    retry_attempts=3,
    
    # Configurações de logging
    log_level="INFO",
    log_requests=True
)
```

### Usando Hooks

```python
from dataverse_sdk import DataverseSDK
from dataverse_sdk.hooks import HookManager

async def log_request(request_data):
    print(f"📤 Request: {request_data['method']} {request_data['url']}")

async def log_response(response_data):
    print(f"📥 Response: {response_data['status_code']}")

# Configurar hooks
sdk = DataverseSDK()
sdk.hooks.register('before_request', log_request)
sdk.hooks.register('after_response', log_response)

async with sdk:
    # Todas as operações terão logs automáticos
    accounts = await sdk.query("accounts", {"top": 5})
```

## 🚨 Tratamento de Erros

```python
from dataverse_sdk import DataverseSDK
from dataverse_sdk.exceptions import (
    DataverseError, 
    AuthenticationError, 
    ValidationError,
    RateLimitError
)

async def error_handling_example():
    sdk = DataverseSDK()
    
    async with sdk:
        try:
            # Operação que pode falhar
            result = await sdk.create("accounts", {
                "name": "",  # Nome vazio causará erro
            })
            
        except ValidationError as e:
            print(f"❌ Erro de validação: {e}")
            
        except AuthenticationError as e:
            print(f"🔐 Erro de autenticação: {e}")
            
        except RateLimitError as e:
            print(f"⏱️ Rate limit atingido: {e}")
            # SDK já faz retry automático
            
        except DataverseError as e:
            print(f"💥 Erro geral do Dataverse: {e}")
            
        except Exception as e:
            print(f"🔥 Erro inesperado: {e}")

asyncio.run(error_handling_example())
```

## 📊 Monitoramento

```python
import time
from dataverse_sdk import DataverseSDK

async def monitoring_example():
    sdk = DataverseSDK()
    
    async with sdk:
        start_time = time.time()
        
        # Operação monitorada
        accounts = await sdk.query("accounts", {"top": 1000})
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📊 Métricas:")
        print(f"   - Registros: {len(accounts.value)}")
        print(f"   - Tempo: {duration:.2f}s")
        print(f"   - Registros/s: {len(accounts.value)/duration:.1f}")

asyncio.run(monitoring_example())
```

## 🎯 Próximos Passos

Agora que você tem o básico funcionando:

1. **[Explore os Tutoriais](../tutorials/)** - Aprenda funcionalidades avançadas
2. **[Leia os Guias](../guides/)** - Melhores práticas e otimização
3. **[Consulte a API Reference](../api-reference/)** - Documentação completa
4. **[Veja Exemplos Reais](../examples/)** - Casos de uso práticos

## 🆘 Problemas?

- **Erro de autenticação**: Verifique suas credenciais Azure AD
- **Timeout**: Aumente o valor de `timeout` na configuração
- **Rate limiting**: O SDK faz retry automático
- **Mais ajuda**: Consulte [Troubleshooting](../troubleshooting/)

## 📚 Recursos Úteis

- **PyPI Package**: https://pypi.org/project/crmadminbrasil-dataverse-sdk/
- **GitHub Repository**: https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk
- **Dataverse Web API Docs**: https://docs.microsoft.com/en-us/powerapps/developer/data-platform/webapi/

---

**🎉 Parabéns! Você está pronto para usar o crmadminbrasil-dataverse-sdk SDK!**

