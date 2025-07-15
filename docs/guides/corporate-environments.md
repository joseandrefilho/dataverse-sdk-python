# Configuração para Ambientes Corporativos

Este guia aborda como configurar o SDK Dataverse para funcionar em ambientes corporativos que possuem proxies, firewalls e políticas de SSL específicas.

## Problemas Comuns em Ambientes Corporativos

### 1. Erros de Proxy
```
ProxyError: HTTPSConnectionPool(host='login.microsoftonline.com', port=443)
```

### 2. Erros de SSL
```
SSL: CERTIFICATE_VERIFY_FAILED
```

### 3. Timeouts de Conexão
```
ConnectTimeout: HTTPSConnectionPool(host='yourorg.crm.dynamics.com', port=443)
```

## Soluções de Configuração

### Configuração Básica para Ambientes Corporativos

```python
from dataverse_sdk import DataverseSDK

# Configuração completa para ambiente corporativo
sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
    
    # Configurações de Proxy
    proxy_url="http://proxy.company.com:8080",
    proxy_username="your_username",
    proxy_password="your_password",
    
    # Configurações de SSL
    verify_ssl=False,  # Desabilita verificação SSL se necessário
    disable_ssl_warnings=True,  # Remove warnings de SSL
    trust_env=True,  # Confia nas configurações de ambiente
)
```

## Configurações de Proxy

### 1. Proxy Simples (sem autenticação)

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    proxy_url="http://proxy.company.com:8080"
)
```

### 2. Proxy com Autenticação

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    proxy_url="http://proxy.company.com:8080",
    proxy_username="corporate_user",
    proxy_password="corporate_password"
)
```

### 3. Configuração via Variáveis de Ambiente

```bash
# Configurar proxy via variáveis de ambiente
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export PROXY_USERNAME=corporate_user
export PROXY_PASSWORD=corporate_password
```

```python
# O SDK automaticamente detectará as configurações
sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    # ... outras configurações básicas ...
)
```

## Configurações de SSL

### 1. Desabilitar Verificação SSL (Não Recomendado para Produção)

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    verify_ssl=False,
    disable_ssl_warnings=True
)
```

### 2. Usar Certificado CA Corporativo

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    ssl_ca_bundle="/path/to/corporate-ca-bundle.pem"
)
```

### 3. Certificados de Cliente

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    ssl_cert_file="/path/to/client.crt",
    ssl_key_file="/path/to/client.key"
)
```

### 4. Configuração via Variáveis de Ambiente

```bash
# Configurações SSL via ambiente
export VERIFY_SSL=false
export SSL_CA_BUNDLE=/path/to/corporate-ca-bundle.pem
export DISABLE_SSL_WARNINGS=true
```

## Configuração Completa via Arquivo

Crie um arquivo `dataverse-config.json`:

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
  "disable_ssl_warnings": true,
  "trust_env": true
}
```

```python
# O SDK carregará automaticamente as configurações
sdk = DataverseSDK()
```

## Configuração via Classe Config

```python
from dataverse_sdk import DataverseSDK, Config

# Criar configuração personalizada
config = Config(
    proxy_url="http://proxy.company.com:8080",
    proxy_username="corporate_user",
    proxy_password="corporate_password",
    verify_ssl=False,
    disable_ssl_warnings=True,
    connect_timeout=30.0,  # Timeout maior para ambientes lentos
    read_timeout=60.0,
    max_retries=5  # Mais tentativas para redes instáveis
)

sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
    config=config
)
```

## Configurações Avançadas

### Timeouts Personalizados

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    config=Config(
        connect_timeout=30.0,  # 30 segundos para conectar
        read_timeout=120.0,    # 2 minutos para ler resposta
        write_timeout=30.0,    # 30 segundos para escrever
        pool_timeout=10.0      # 10 segundos para pool de conexões
    )
)
```

### Pool de Conexões

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    config=Config(
        max_connections=50,           # Máximo de conexões simultâneas
        max_keepalive_connections=10, # Conexões keep-alive
        keepalive_expiry=60          # Expiração keep-alive em segundos
    )
)
```

### Retry Logic

```python
sdk = DataverseSDK(
    # ... outras configurações ...
    config=Config(
        max_retries=5,              # Máximo de tentativas
        backoff_factor=2.0,         # Fator de backoff exponencial
        retry_status_codes=[429, 500, 502, 503, 504]  # Códigos para retry
    )
)
```

## Troubleshooting

### Verificar Configurações

```python
# Verificar se as configurações foram aplicadas
print(f"Proxy configurado: {bool(sdk.config.get('proxy_url'))}")
print(f"SSL verification: {sdk.config.get('verify_ssl')}")
print(f"Proxy URL: {sdk.config.get('proxy_url')}")
```

### Logs Detalhados

```python
import logging
import structlog

# Configurar logs detalhados
logging.basicConfig(level=logging.DEBUG)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
)

# Agora o SDK mostrará logs detalhados de conexão
sdk = DataverseSDK(...)
```

### Teste de Conectividade

```python
async def test_connectivity():
    try:
        async with sdk:
            # Teste simples de conectividade
            entities = await sdk.query("accounts", {"top": 1})
            print("✅ Conectividade OK!")
            return True
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        return False

# Executar teste
import asyncio
asyncio.run(test_connectivity())
```

## Exemplos Práticos

### Exemplo 1: Empresa com Proxy Corporativo

```python
# Configuração típica para empresa com proxy
sdk = DataverseSDK(
    dataverse_url="https://contoso.crm.dynamics.com",
    client_id="12345678-1234-1234-1234-123456789012",
    client_secret="your-secret",
    tenant_id="87654321-4321-4321-4321-210987654321",
    
    # Proxy corporativo
    proxy_url="http://proxy.contoso.com:8080",
    proxy_username="john.doe",
    proxy_password="corporate_password",
    
    # SSL corporativo
    verify_ssl=False,
    disable_ssl_warnings=True
)
```

### Exemplo 2: Ambiente com Certificados Próprios

```python
# Configuração para ambiente com CA própria
sdk = DataverseSDK(
    dataverse_url="https://internal.crm.company.local",
    client_id="your-client-id",
    client_secret="your-secret",
    tenant_id="your-tenant-id",
    
    # Certificado CA da empresa
    ssl_ca_bundle="/etc/ssl/certs/company-ca.pem",
    verify_ssl=True,
    
    # Certificado de cliente se necessário
    ssl_cert_file="/etc/ssl/certs/client.crt",
    ssl_key_file="/etc/ssl/private/client.key"
)
```

### Exemplo 3: Configuração Flexível

```python
import os

# Configuração que se adapta ao ambiente
sdk = DataverseSDK(
    dataverse_url=os.getenv("DATAVERSE_URL"),
    client_id=os.getenv("AZURE_CLIENT_ID"),
    client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    tenant_id=os.getenv("AZURE_TENANT_ID"),
    
    # Configurações condicionais
    proxy_url=os.getenv("CORPORATE_PROXY"),
    verify_ssl=os.getenv("VERIFY_SSL", "true").lower() != "false",
    disable_ssl_warnings=os.getenv("DISABLE_SSL_WARNINGS", "false").lower() == "true"
)
```

## Variáveis de Ambiente Suportadas

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `HTTP_PROXY` | URL do proxy HTTP | `http://proxy:8080` |
| `HTTPS_PROXY` | URL do proxy HTTPS | `http://proxy:8080` |
| `PROXY_USERNAME` | Usuário do proxy | `corporate_user` |
| `PROXY_PASSWORD` | Senha do proxy | `password123` |
| `VERIFY_SSL` | Verificar SSL | `false` |
| `SSL_CA_BUNDLE` | Caminho para CA bundle | `/path/to/ca.pem` |
| `SSL_CERT_FILE` | Certificado cliente | `/path/to/cert.crt` |
| `SSL_KEY_FILE` | Chave privada cliente | `/path/to/key.key` |
| `DISABLE_SSL_WARNINGS` | Desabilitar warnings SSL | `true` |
| `TRUST_ENV` | Confiar no ambiente | `true` |

## Melhores Práticas

### 1. Segurança
- **Nunca** desabilite SSL em produção sem justificativa
- Use certificados válidos sempre que possível
- Mantenha credenciais de proxy seguras

### 2. Performance
- Configure timeouts apropriados para sua rede
- Use pool de conexões adequado
- Implemente retry logic para redes instáveis

### 3. Monitoramento
- Ative logs detalhados durante troubleshooting
- Monitore métricas de conectividade
- Implemente health checks

### 4. Configuração
- Use variáveis de ambiente para configurações sensíveis
- Documente configurações específicas do ambiente
- Teste configurações em ambiente de desenvolvimento primeiro

## Suporte

Se você continuar enfrentando problemas:

1. **Verifique logs detalhados** com `DEBUG` level
2. **Teste conectividade** com ferramentas como `curl` ou `wget`
3. **Consulte administradores de rede** sobre políticas corporativas
4. **Abra uma issue** no GitHub com logs e configurações (sem credenciais)

## Links Úteis

- [Documentação do httpx sobre proxies](https://www.python-httpx.org/advanced/#http-proxying)
- [Configuração SSL do Python](https://docs.python.org/3/library/ssl.html)
- [Troubleshooting de rede corporativa](https://docs.microsoft.com/en-us/azure/active-directory/develop/troubleshoot-authentication)

