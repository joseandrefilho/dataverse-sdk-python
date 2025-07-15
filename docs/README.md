# Microsoft Dataverse SDK - Documentação

Bem-vindo à documentação completa do **crmadminbrasil-dataverse-sdk**, um SDK Python moderno e assíncrono para Microsoft Dataverse.

## 📚 Índice da Documentação

### 🚀 [Getting Started](getting-started/)
- [Instalação](getting-started/installation.md)
- [Configuração Inicial](getting-started/configuration.md)
- [Primeiro Uso](getting-started/quickstart.md)
- [Autenticação](getting-started/authentication.md)

### 📖 [Tutoriais](tutorials/)
- [Tutorial Básico: CRUD Operations](tutorials/basic-crud.md)
- [Tutorial Avançado: Bulk Operations](tutorials/bulk-operations.md)
- [Tutorial: FetchXML Queries](tutorials/fetchxml-queries.md)
- [Tutorial: CLI Usage](tutorials/cli-usage.md)
- [Tutorial: Hooks e Extensibilidade](tutorials/hooks-extensibility.md)

### 📋 [Guias](guides/)
- [Melhores Práticas](guides/best-practices.md)
- [Performance e Otimização](guides/performance.md)
- [Tratamento de Erros](guides/error-handling.md)
- [Configuração Avançada](guides/advanced-configuration.md)
- [Deployment em Produção](guides/production-deployment.md)

### 🔧 [Referência da API](api-reference/)
- [DataverseSDK](api-reference/dataverse-sdk.md)
- [AsyncDataverseClient](api-reference/async-client.md)
- [Modelos de Dados](api-reference/models.md)
- [Exceções](api-reference/exceptions.md)
- [Utilitários](api-reference/utilities.md)

### 💡 [Exemplos](examples/)
- [Exemplos Básicos](examples/basic-examples.md)
- [Exemplos Avançados](examples/advanced-examples.md)
- [Casos de Uso Reais](examples/real-world-examples.md)
- [Integração com Frameworks](examples/framework-integration.md)

### 🔍 [Troubleshooting](troubleshooting/)
- [Problemas Comuns](troubleshooting/common-issues.md)
- [Debugging](troubleshooting/debugging.md)
- [FAQ](troubleshooting/faq.md)
- [Suporte](troubleshooting/support.md)

## 🎯 Links Rápidos

- **PyPI Package**: https://pypi.org/project/crmadminbrasil-dataverse-sdk/
- **GitHub Repository**: https://github.com/joseandrefilho/dataverse-sdk-python
- **Issues & Bug Reports**: https://github.com/joseandrefilho/dataverse-sdk-python/issues
- **Discussions**: https://github.com/joseandrefilho/dataverse-sdk-python/discussions

## 📦 Instalação Rápida

```bash
pip install crmadminbrasil-dataverse-sdk
```

## 🚀 Uso Rápido

```python
import asyncio
from dataverse_sdk import DataverseSDK

async def main():
    sdk = DataverseSDK()
    
    async with sdk:
        # Criar uma conta
        account_id = await sdk.create("accounts", {
            "name": "Minha Empresa"
        })
        
        # Consultar contas
        accounts = await sdk.query("accounts", {
            "select": ["name"],
            "top": 10
        })
        
        print(f"Criada conta: {account_id}")
        print(f"Total de contas: {len(accounts.value)}")

asyncio.run(main())
```

## 🆘 Precisa de Ajuda?

1. **Consulte a documentação** - Comece com [Getting Started](getting-started/)
2. **Veja os exemplos** - Confira [Examples](examples/)
3. **Problemas?** - Consulte [Troubleshooting](troubleshooting/)
4. **Ainda com dúvidas?** - Abra uma [issue](https://github.com/joseandrefilho/dataverse-sdk-python/issues)

---

**Desenvolvido com ❤️ por José André Filho**

