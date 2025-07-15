# 🏢 Guia Rápido: SDK Dataverse em Ambientes Corporativos

## ⚡ Solução Rápida para Erros Comuns

### 🚫 Erro: `SSL CERTIFICATE_VERIFY_FAILED`

```python
from dataverse_sdk import DataverseSDK

sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret", 
    tenant_id="your-tenant-id",
    
    # ✅ Solução SSL
    verify_ssl=False,
    disable_ssl_warnings=True
)
```

### 🚫 Erro: `ProxyError` ou `ConnectTimeout`

```python
sdk = DataverseSDK(
    # ... configurações básicas ...
    
    # ✅ Solução Proxy
    proxy_url="http://proxy.company.com:8080",
    proxy_username="seu_usuario",
    proxy_password="sua_senha"
)
```

## 🔧 Configuração Completa Corporativa

```python
# Configuração que resolve 99% dos problemas corporativos
sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
    
    # Proxy corporativo
    proxy_url="http://proxy.company.com:8080",
    proxy_username="corporate_user",
    proxy_password="corporate_password",
    
    # SSL flexível
    verify_ssl=False,
    disable_ssl_warnings=True,
    trust_env=True
)
```

## 🌍 Configuração via Variáveis de Ambiente

```bash
# Configure uma vez, use em qualquer lugar
export DATAVERSE_URL="https://yourorg.crm.dynamics.com"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"

# Configurações corporativas
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export PROXY_USERNAME="corporate_user"
export PROXY_PASSWORD="corporate_password"
export VERIFY_SSL="false"
export DISABLE_SSL_WARNINGS="true"
```

```python
# Código super simples
from dataverse_sdk import DataverseSDK

# ✅ Carrega tudo automaticamente!
sdk = DataverseSDK()
```

## 📄 Configuração via Arquivo JSON

Crie `dataverse-config.json`:

```json
{
  "dataverse_url": "https://yourorg.crm.dynamics.com",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "tenant_id": "your-tenant-id",
  "proxy_url": "http://proxy.company.com:8080",
  "proxy_username": "corporate_user",
  "proxy_password": "corporate_password",
  "verify_ssl": false,
  "disable_ssl_warnings": true
}
```

```python
# ✅ Carregamento automático!
sdk = DataverseSDK()
```

## 🧪 Teste Rápido

```python
import asyncio
from dataverse_sdk import DataverseSDK

async def test_connection():
    sdk = DataverseSDK(
        # Suas configurações aqui
        verify_ssl=False,
        disable_ssl_warnings=True
    )
    
    try:
        async with sdk:
            accounts = await sdk.query("accounts", {"top": 1})
            print("✅ Conexão funcionando!")
            return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

# Executar teste
asyncio.run(test_connection())
```

## 📋 Checklist de Troubleshooting

- [ ] **Proxy configurado?** Verifique `proxy_url`, `proxy_username`, `proxy_password`
- [ ] **SSL desabilitado?** Use `verify_ssl=False` se necessário
- [ ] **Warnings removidos?** Use `disable_ssl_warnings=True`
- [ ] **Timeouts aumentados?** Configure timeouts maiores se a rede for lenta
- [ ] **Credenciais corretas?** Verifique `client_id`, `client_secret`, `tenant_id`
- [ ] **URL correta?** Confirme o `dataverse_url`

## 🆘 Ainda com Problemas?

### 1. Logs Detalhados
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Agora você verá logs detalhados
sdk = DataverseSDK(...)
```

### 2. Verificar Configurações
```python
print(f"Proxy: {sdk.config.get('proxy_url')}")
print(f"SSL: {sdk.config.get('verify_ssl')}")
```

### 3. Contatar Suporte
- 📧 Abra uma issue no GitHub
- 📋 Inclua logs (sem credenciais)
- 🔧 Descreva seu ambiente corporativo

## 🚀 Instalação/Atualização

```bash
# Instalar versão mais recente com suporte corporativo
pip install --upgrade crmadminbrasil-dataverse-sdk

# Verificar versão (deve ser >= 1.0.6)
pip show crmadminbrasil-dataverse-sdk
```

---

**💡 Dica:** A versão 1.0.6+ inclui suporte completo para ambientes corporativos com proxy e SSL flexível!

