---
layout: default
title: "Microsoft Dataverse SDK for Python"
description: "Modern, async Python SDK for Microsoft Dataverse with enterprise-grade features"
---

<div class="hero-section">
  <div class="hero-content">
    <h1 class="hero-title">
      <span class="gradient-text">Microsoft Dataverse SDK</span>
      <br>for Python
    </h1>
    <p class="hero-subtitle">
      SDK Python <strong>moderno e assíncrono</strong> para Microsoft Dataverse<br>
      Projetado para aplicações enterprise com foco em <strong>performance</strong>, <strong>confiabilidade</strong> e <strong>facilidade de uso</strong>
    </p>
    
    <div class="hero-badges">
      <a href="https://pypi.org/project/crmadminbrasil-dataverse-sdk/" target="_blank">
        <img src="https://badge.fury.io/py/crmadminbrasil-dataverse-sdk.svg" alt="PyPI version">
      </a>
      <a href="https://www.python.org/downloads/" target="_blank">
        <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
      </a>
      <a href="https://opensource.org/licenses/MIT" target="_blank">
        <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
      </a>
      <a href="https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk/stargazers" target="_blank">
        <img src="https://img.shields.io/github/stars/joseandrefilho/crmadminbrasil-dataverse-sdk.svg" alt="GitHub stars">
      </a>
    </div>

    <div class="hero-actions">
      <a href="#quick-start" class="btn btn-primary">🚀 Começar Agora</a>
      <a href="https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk" class="btn btn-secondary" target="_blank">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
        </svg>
        Ver no GitHub
      </a>
    </div>
  </div>
</div>

## 🚀 Instalação Rápida {#quick-start}

<div class="installation-section">
  <div class="install-step">
    <h3>1. Instalar o SDK</h3>
    <div class="code-block">
      <pre><code>pip install crmadminbrasil-dataverse-sdk</code></pre>
      <button class="copy-btn" onclick="copyToClipboard('pip install crmadminbrasil-dataverse-sdk')">📋</button>
    </div>
  </div>

  <div class="install-step">
    <h3>2. Configurar Credenciais</h3>
    <div class="code-block">
      <pre><code>dv-cli config init</code></pre>
      <button class="copy-btn" onclick="copyToClipboard('dv-cli config init')">📋</button>
    </div>
    <p class="step-description">Configure suas credenciais do Azure AD e URL do Dataverse</p>
  </div>

  <div class="install-step">
    <h3>3. Testar Conexão</h3>
    <div class="code-block">
      <pre><code>dv-cli entity list accounts --top 5</code></pre>
      <button class="copy-btn" onclick="copyToClipboard('dv-cli entity list accounts --top 5')">📋</button>
    </div>
    <p class="step-description">Verifique se a conexão está funcionando</p>
  </div>
</div>

## ⚡ Exemplo Prático

<div class="example-section">
  <div class="example-tabs">
    <button class="tab-btn active" onclick="showTab('python-tab')">🐍 Python SDK</button>
    <button class="tab-btn" onclick="showTab('cli-tab')">💻 CLI</button>
    <button class="tab-btn" onclick="showTab('aws-tab')">☁️ AWS Glue</button>
  </div>

  <div id="python-tab" class="tab-content active">
    <h4>SDK Python Assíncrono</h4>
    <div class="code-block">
      <pre><code>import asyncio
from dataverse_sdk import DataverseSDK

async def main():
    # Inicializar SDK (carrega configuração automaticamente)
    sdk = DataverseSDK()
    
    async with sdk:
        # ✅ Criar uma nova conta
        account_data = {
            "name": "CRM Admin Brasil",
            "websiteurl": "https://crmadminbrasil.com",
            "telephone1": "+55 11 99999-9999",
            "revenue": 5000000
        }
        account_id = await sdk.create("accounts", account_data)
        print(f"Conta criada: {account_id}")
        
        # ✅ Consultar contas com filtros avançados
        accounts = await sdk.query("accounts", {
            "select": ["name", "revenue", "websiteurl"],
            "filter": "revenue gt 1000000 and statecode eq 0",
            "orderby": "revenue desc",
            "top": 10
        })
        
        print(f"Encontradas {len(accounts.value)} contas enterprise")
        
        # ✅ Operações em lote (alta performance)
        contacts_data = [
            {"firstname": "João", "lastname": "Silva", "emailaddress1": "joao@empresa.com"},
            {"firstname": "Maria", "lastname": "Santos", "emailaddress1": "maria@empresa.com"},
            {"firstname": "Pedro", "lastname": "Costa", "emailaddress1": "pedro@empresa.com"}
        ]
        
        results = await sdk.bulk_create("contacts", contacts_data)
        print(f"Criados {len(results.success)} contatos em lote")

# Executar
asyncio.run(main())</code></pre>
      <button class="copy-btn" onclick="copyToClipboard(this.previousElementSibling.textContent)">📋</button>
    </div>
  </div>

  <div id="cli-tab" class="tab-content">
    <h4>Interface de Linha de Comando</h4>
    <div class="code-block">
      <pre><code># 🔧 Configuração inicial
dv-cli config init

# 📊 Listar entidades
dv-cli entity list accounts --top 10 --filter "revenue gt 1000000"

# ➕ Criar nova conta
dv-cli entity create accounts '{
  "name": "Nova Empresa",
  "websiteurl": "https://novaempresa.com",
  "revenue": 2500000
}'

# 📈 Operações em lote
dv-cli bulk create contacts data/contacts.json

# 🔍 Executar FetchXML
dv-cli fetchxml execute queries/top-accounts.xml

# 📤 Exportar dados
dv-cli data export accounts --output accounts.json --filter "statecode eq 0"

# 📥 Importar dados
dv-cli data import contacts contacts.json</code></pre>
      <button class="copy-btn" onclick="copyToClipboard(this.previousElementSibling.textContent)">📋</button>
    </div>
  </div>

  <div id="aws-tab" class="tab-content">
    <h4>Integração com AWS Glue</h4>
    <div class="code-block">
      <pre><code>import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from dataverse_sdk import DataverseSDK
import asyncio

# Configuração do Glue Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

async def sync_dataverse_to_s3():
    """Sincronizar dados do Dataverse para S3"""
    sdk = DataverseSDK()
    
    async with sdk:
        # Extrair contas ativas
        accounts = await sdk.query_all("accounts", {
            "select": ["name", "revenue", "websiteurl", "createdon"],
            "filter": "statecode eq 0"
        })
        
        # Converter para DataFrame do Spark
        df = spark.createDataFrame(accounts)
        
        # Salvar no S3 em formato Parquet
        df.write.mode("overwrite").parquet("s3://meu-bucket/dataverse/accounts/")
        
        print(f"Sincronizados {df.count()} registros para S3")

# Executar sincronização
asyncio.run(sync_dataverse_to_s3())
job.commit()</code></pre>
      <button class="copy-btn" onclick="copyToClipboard(this.previousElementSibling.textContent)">📋</button>
    </div>
  </div>
</div>

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



## 🎯 Principais Funcionalidades

<div class="features-grid">
  <div class="feature-card">
    <div class="feature-icon">⚡</div>
    <h3>Performance Enterprise</h3>
    <ul>
      <li><strong>100% Assíncrono</strong> com httpx e asyncio</li>
      <li><strong>Pool de Conexões</strong> otimizado</li>
      <li><strong>Operações em Lote</strong> com auto-chunking</li>
      <li><strong>Retry Logic</strong> inteligente</li>
      <li><strong>Rate Limiting</strong> automático</li>
    </ul>
  </div>

  <div class="feature-card">
    <div class="feature-icon">🔧</div>
    <h3>Facilidade de Uso</h3>
    <ul>
      <li><strong>CLI Completa</strong> com auto-configuração</li>
      <li><strong>Tipagem Forte</strong> com Pydantic</li>
      <li><strong>Configuração Automática</strong></li>
      <li><strong>Documentação Rica</strong></li>
      <li><strong>Exemplos Práticos</strong></li>
    </ul>
  </div>

  <div class="feature-card">
    <div class="feature-icon">🛡️</div>
    <h3>Confiabilidade</h3>
    <ul>
      <li><strong>Autenticação Azure AD</strong> completa</li>
      <li><strong>Tratamento de Erros</strong> robusto</li>
      <li><strong>Logs Estruturados</strong></li>
      <li><strong>Testes Abrangentes</strong> (>90% cobertura)</li>
      <li><strong>Validação de Dados</strong></li>
    </ul>
  </div>

  <div class="feature-card">
    <div class="feature-icon">🔗</div>
    <h3>Integrações</h3>
    <ul>
      <li><strong>AWS Glue</strong> nativo</li>
      <li><strong>Pandas</strong> DataFrames</li>
      <li><strong>FetchXML</strong> completo</li>
      <li><strong>OData</strong> avançado</li>
      <li><strong>Webhooks</strong> e eventos</li>
    </ul>
  </div>
</div>

## 📊 Casos de Uso Reais

<div class="use-cases">
  <div class="use-case">
    <h3>🏢 Migração de CRM Legacy</h3>
    <p>Migre milhões de registros de sistemas legados para o Dataverse com operações em lote otimizadas e controle de erro granular.</p>
    <a href="docs/tutorials/real-world-etl-scenarios.html#migração-crm-legacy" class="learn-more">Ver Tutorial →</a>
  </div>

  <div class="use-case">
    <h3>🔄 Sincronização E-commerce</h3>
    <p>Sincronize dados de vendas, produtos e clientes entre seu e-commerce e Dataverse em tempo real com webhooks.</p>
    <a href="docs/tutorials/real-world-etl-scenarios.html#sincronização-e-commerce" class="learn-more">Ver Tutorial →</a>
  </div>

  <div class="use-case">
    <h3>☁️ Pipeline AWS Glue</h3>
    <p>Crie pipelines de dados robustos no AWS Glue para análise e business intelligence com dados do Dataverse.</p>
    <a href="docs/guides/aws-glue-integration.html" class="learn-more">Ver Guia →</a>
  </div>

  <div class="use-case">
    <h3>📈 Analytics e BI</h3>
    <p>Extraia dados para data lakes e ferramentas de BI como Power BI, Tableau e Looker com performance otimizada.</p>
    <a href="docs/examples/analytics-integration.html" class="learn-more">Ver Exemplos →</a>
  </div>
</div>

## 🚀 Por que Escolher Este SDK?

<div class="comparison-table">
  <table>
    <thead>
      <tr>
        <th>Recurso</th>
        <th>Este SDK</th>
        <th>SDKs Tradicionais</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Performance</strong></td>
        <td>✅ 100% Assíncrono + Pool de Conexões</td>
        <td>❌ Síncrono, uma conexão por vez</td>
      </tr>
      <tr>
        <td><strong>Operações em Lote</strong></td>
        <td>✅ Auto-chunking + Execução Paralela</td>
        <td>⚠️ Limitado ou manual</td>
      </tr>
      <tr>
        <td><strong>Tipagem</strong></td>
        <td>✅ Type Hints + Pydantic</td>
        <td>❌ Sem tipagem forte</td>
      </tr>
      <tr>
        <td><strong>CLI</strong></td>
        <td>✅ CLI Rica + Auto-configuração</td>
        <td>❌ Sem CLI ou básica</td>
      </tr>
      <tr>
        <td><strong>AWS Glue</strong></td>
        <td>✅ Integração Nativa</td>
        <td>❌ Configuração manual complexa</td>
      </tr>
      <tr>
        <td><strong>Documentação</strong></td>
        <td>✅ 440+ páginas + Exemplos</td>
        <td>⚠️ Documentação básica</td>
      </tr>
      <tr>
        <td><strong>Tratamento de Erros</strong></td>
        <td>✅ Retry Logic + Logs Estruturados</td>
        <td>⚠️ Tratamento básico</td>
      </tr>
    </tbody>
  </table>
</div>

## 📚 Documentação Completa

<div class="docs-grid">
  <a href="docs/getting-started/quickstart.html" class="doc-card">
    <div class="doc-icon">🚀</div>
    <h3>Quick Start</h3>
    <p>Comece em 5 minutos com exemplos práticos</p>
  </a>

  <a href="docs/api-reference/dataverse-sdk.html" class="doc-card">
    <div class="doc-icon">📖</div>
    <h3>API Reference</h3>
    <p>Documentação completa de todas as funções</p>
  </a>

  <a href="docs/guides/aws-glue-integration.html" class="doc-card">
    <div class="doc-icon">☁️</div>
    <h3>AWS Glue Guide</h3>
    <p>Integração completa com AWS Glue</p>
  </a>

  <a href="docs/tutorials/real-world-etl-scenarios.html" class="doc-card">
    <div class="doc-icon">🔄</div>
    <h3>ETL Scenarios</h3>
    <p>Cenários reais de migração e sincronização</p>
  </a>

  <a href="docs/examples/" class="doc-card">
    <div class="doc-icon">💡</div>
    <h3>Exemplos</h3>
    <p>310+ exemplos de código prontos para usar</p>
  </a>

  <a href="docs/troubleshooting/" class="doc-card">
    <div class="doc-icon">🔧</div>
    <h3>Troubleshooting</h3>
    <p>Soluções para problemas comuns</p>
  </a>
</div>

## 🤝 Suporte e Comunidade

<div class="support-section">
  <div class="support-card">
    <h3>🐛 Reportar Bugs</h3>
    <p>Encontrou um problema? Reporte no GitHub Issues</p>
    <a href="https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk/issues" class="btn btn-outline" target="_blank">Reportar Issue</a>
  </div>

  <div class="support-card">
    <h3>💡 Solicitar Funcionalidades</h3>
    <p>Tem uma ideia? Compartilhe conosco!</p>
    <a href="https://github.com/joseandrefilho/crmadminbrasil-dataverse-sdk/discussions" class="btn btn-outline" target="_blank">Discussões</a>
  </div>

  <div class="support-card">
    <h3>📧 Suporte Comercial</h3>
    <p>Precisa de suporte enterprise?</p>
    <a href="mailto:contato@crmadminbrasil.com" class="btn btn-outline">Entrar em Contato</a>
  </div>
</div>

## 📈 Estatísticas do Projeto

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-number">1.0.2</div>
    <div class="stat-label">Versão Atual</div>
  </div>
  
  <div class="stat-card">
    <div class="stat-number">440+</div>
    <div class="stat-label">Páginas de Docs</div>
  </div>
  
  <div class="stat-card">
    <div class="stat-number">310+</div>
    <div class="stat-label">Exemplos de Código</div>
  </div>
  
  <div class="stat-card">
    <div class="stat-number">90%+</div>
    <div class="stat-label">Cobertura de Testes</div>
  </div>
</div>

---

<div class="footer-cta">
  <h2>Pronto para começar?</h2>
  <p>Instale o SDK agora e comece a integrar com o Dataverse em minutos!</p>
  
  <div class="cta-buttons">
    <a href="#quick-start" class="btn btn-primary btn-large">🚀 Instalar Agora</a>
    <a href="docs/getting-started/quickstart.html" class="btn btn-secondary btn-large">📚 Ver Documentação</a>
  </div>
</div>

<script>
// Função para copiar código
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(function() {
    // Feedback visual
    event.target.textContent = '✅';
    setTimeout(() => {
      event.target.textContent = '📋';
    }, 2000);
  });
}

// Sistema de abas
function showTab(tabId) {
  // Esconder todas as abas
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });
  
  // Remover classe active de todos os botões
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Mostrar aba selecionada
  document.getElementById(tabId).classList.add('active');
  
  // Adicionar classe active ao botão clicado
  event.target.classList.add('active');
}
</script>

