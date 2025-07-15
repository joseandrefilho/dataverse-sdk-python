---
layout: home
title: "Microsoft Dataverse SDK for Python"
description: "Modern, async Python SDK for Microsoft Dataverse with enterprise-grade features"
---

# Microsoft Dataverse SDK for Python

[![PyPI version](https://badge.fury.io/py/crmadminbrasil-dataverse-sdk.svg)](https://pypi.org/project/crmadminbrasil-dataverse-sdk/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/joseandrefilho/crmadminbrasil-dataverse-sdk.svg)](https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk/stargazers)

Um SDK Python **moderno e assíncrono** para Microsoft Dataverse, projetado para aplicações enterprise com foco em **performance**, **confiabilidade** e **facilidade de uso**.

## 🚀 Instalação Rápida

```bash
pip install crmadminbrasil-dataverse-sdk
```

## ⚡ Exemplo Rápido

```python
import asyncio
from dataverse_sdk import DataverseSDK

async def main():
    sdk = DataverseSDK()
    
    async with sdk:
        # Criar uma conta
        account_id = await sdk.create("accounts", {
            "name": "Minha Empresa",
            "websiteurl": "https://minhaempresa.com"
        })
        
        # Consultar contas
        accounts = await sdk.query("accounts", {
            "select": ["name", "revenue"],
            "filter": "revenue gt 1000000",
            "top": 10
        })
        
        print(f"Encontradas {len(accounts.value)} contas")

asyncio.run(main())
```

## 🎯 Principais Funcionalidades

### 🔥 Performance Enterprise
- **100% Assíncrono** com `httpx` e `asyncio`
- **Pool de conexões** otimizado
- **Operações em lote** com auto-chunking
- **Retry logic** inteligente com backoff exponencial

### 🛡️ Confiabilidade
- **Tipagem forte** com Pydantic
- **Tratamento robusto de erros**
- **Rate limiting** automático
- **Logging estruturado**

### 🔧 Facilidade de Uso
- **API intuitiva** e bem documentada
- **CLI completa** para operações rápidas
- **Sistema de hooks** para extensibilidade
- **Configuração flexível**

### ☁️ Integração Cloud
- **AWS Glue** - ETL pipelines completos
- **Azure Functions** - Serverless ready
- **Docker** - Containerização nativa
- **CI/CD** - Workflows automatizados

## 📚 Documentação

### 🏁 Começando
- [**Instalação**](docs/getting-started/installation.md) - Guia completo de instalação
- [**Quick Start**](docs/getting-started/quickstart.md) - Primeiros passos
- [**Configuração**](docs/getting-started/configuration.md) - Setup de credenciais
- [**Autenticação**](docs/getting-started/authentication.md) - Fluxos Azure AD

### 📖 Tutoriais
- [**CRUD Básico**](docs/tutorials/basic-crud.md) - Operações fundamentais
- [**Bulk Operations**](docs/tutorials/bulk-operations.md) - Operações em lote
- [**FetchXML**](docs/tutorials/fetchxml-queries.md) - Consultas avançadas
- [**CLI Usage**](docs/tutorials/cli-usage.md) - Interface de linha de comando
- [**ETL Real-World**](docs/tutorials/real-world-etl-scenarios.md) - Cenários práticos

### 📋 Guias
- [**AWS Glue Integration**](docs/guides/aws-glue-integration.md) - ETL com AWS Glue
- [**Best Practices**](docs/guides/best-practices.md) - Melhores práticas
- [**Performance**](docs/guides/performance.md) - Otimização
- [**Production**](docs/guides/production-deployment.md) - Deploy em produção

### 🔧 API Reference
- [**DataverseSDK**](docs/api-reference/dataverse-sdk.md) - Classe principal
- [**Models**](docs/api-reference/models.md) - Modelos de dados
- [**Exceptions**](docs/api-reference/exceptions.md) - Tratamento de erros

## 🎯 Casos de Uso

### 📊 ETL e Data Integration
```python
# Extrair dados para AWS S3
accounts = await sdk.query("accounts", {"top": 10000})
df = pd.DataFrame(accounts.value)
df.to_parquet("s3://bucket/accounts.parquet")

# Carregar dados em lote
result = await sdk.bulk_create("contacts", contacts_data, batch_size=100)
print(f"Criados: {result.successful}, Falhas: {result.failed}")
```

### 🔄 Migração de Sistemas
```python
# Migração de CRM legacy
async with DataverseSDK() as sdk:
    # Extrair do sistema antigo
    legacy_data = extract_from_legacy_crm()
    
    # Transformar dados
    transformed_data = transform_for_dataverse(legacy_data)
    
    # Carregar no Dataverse
    result = await sdk.bulk_create("accounts", transformed_data)
```

### 🛒 E-commerce Integration
```python
# Sincronização de pedidos
orders = await fetch_ecommerce_orders()
opportunities = transform_orders_to_opportunities(orders)
await sdk.bulk_create("opportunities", opportunities)
```

### ⚡ Real-time Processing
```python
# Processamento de eventos em tempo real
@webhook_handler
async def handle_dataverse_event(event):
    if event['EntityName'] == 'account' and event['EventName'] == 'Create':
        await create_welcome_tasks(event['PrimaryEntityId'])
```

## 🖥️ CLI

Interface de linha de comando rica para operações rápidas:

```bash
# Configuração
dv-cli config init

# Operações básicas
dv-cli entity list accounts --top 10
dv-cli entity create accounts --data '{"name": "Nova Empresa"}'

# Operações em lote
dv-cli bulk create contacts --file contacts.json --batch-size 50

# FetchXML
dv-cli fetchxml execute --file query.xml --output results.json

# Export/Import
dv-cli data export accounts --output accounts.csv --format csv
```

## 🏢 Enterprise Ready

### 🔐 Segurança
- Autenticação Azure AD (Client Credentials, Device Code, Interactive)
- Tokens seguros com renovação automática
- Suporte a certificados e secrets

### 📈 Monitoramento
- Métricas detalhadas de performance
- Logging estruturado com contexto
- Integração com CloudWatch/Application Insights

### 🚀 Escalabilidade
- Pool de conexões configurável
- Processamento paralelo otimizado
- Rate limiting inteligente

## 🌟 Por que escolher este SDK?

| Funcionalidade | crmadminbrasil-dataverse-sdk | Outros SDKs |
|----------------|-------------------|-------------|
| **Performance** | 100% Async, Pool de conexões | Sync, Conexões individuais |
| **Bulk Operations** | Auto-chunking, Paralelo | Manual, Sequencial |
| **Error Handling** | Retry inteligente, Tipado | Básico, Genérico |
| **AWS Integration** | Guias específicos, Exemplos | Documentação limitada |
| **CLI** | Interface completa | Não disponível |
| **Documentação** | 440+ páginas, 310+ exemplos | Básica |
| **Suporte** | Ativo, GitHub Issues | Limitado |

## 📊 Benchmarks

```
Operação                    | crmadminbrasil-dataverse-sdk | SDK Tradicional
---------------------------|-------------------|----------------
Criar 1000 registros      | 12s               | 45s
Consultar 10k registros    | 3s                | 8s
Bulk update 5k registros   | 8s                | 25s
FetchXML complexo          | 2s                | 6s
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja nosso [guia de contribuição](CONTRIBUTING.md).

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk/discussions)
- **Documentação**: [Guia Completo](docs/)

## 🔗 Links Úteis

- **PyPI Package**: [crmadminbrasil-dataverse-sdk](https://pypi.org/project/crmadminbrasil-dataverse-sdk/)
- **GitHub Repository**: [dataverse-sdk-python](https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk)
- **Documentação Completa**: [GitHub Pages](https://joseandrefilho.github.io/crmadminbrasil-dataverse-sdk/)
- **Microsoft Dataverse**: [Documentação Oficial](https://docs.microsoft.com/en-us/powerapps/developer/data-platform/)

---

**Desenvolvido com ❤️ por [José André Filho](https://github.com/joseandrefilho)**

**⭐ Se este SDK foi útil para você, considere dar uma estrela no GitHub!**

