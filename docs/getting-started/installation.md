# Instalação

Este guia mostra como instalar o **jaf-dataverse-2025** SDK em diferentes ambientes.

## 📋 Requisitos

### Requisitos do Sistema
- **Python**: 3.9 ou superior
- **Sistema Operacional**: Windows, macOS, Linux
- **Memória**: Mínimo 512MB RAM
- **Espaço em Disco**: ~50MB para o SDK e dependências

### Requisitos do Dataverse
- **Microsoft Dataverse** ou **Dynamics 365** environment
- **Credenciais de autenticação** (Azure AD App Registration)
- **Permissões adequadas** no ambiente Dataverse

## 🚀 Instalação via pip (Recomendado)

### Instalação Básica

```bash
pip install jaf-dataverse-2025
```

### Instalação com Dependências Opcionais

```bash
# Para desenvolvimento (inclui ferramentas de teste e linting)
pip install jaf-dataverse-2025[dev]

# Para documentação (inclui ferramentas de geração de docs)
pip install jaf-dataverse-2025[docs]

# Instalação completa (todas as dependências)
pip install jaf-dataverse-2025[all]
```

## 🐍 Ambientes Virtuais

### Usando venv (Recomendado)

```bash
# Criar ambiente virtual
python -m venv dataverse-env

# Ativar ambiente (Linux/macOS)
source dataverse-env/bin/activate

# Ativar ambiente (Windows)
dataverse-env\Scripts\activate

# Instalar SDK
pip install jaf-dataverse-2025
```

### Usando conda

```bash
# Criar ambiente conda
conda create -n dataverse-env python=3.11

# Ativar ambiente
conda activate dataverse-env

# Instalar SDK
pip install jaf-dataverse-2025
```

### Usando Poetry

```bash
# Inicializar projeto Poetry
poetry init

# Adicionar dependência
poetry add jaf-dataverse-2025

# Instalar dependências
poetry install
```

## 🐳 Docker

### Dockerfile Exemplo

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar SDK
RUN pip install jaf-dataverse-2025

# Copiar seu código
COPY . .

CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  dataverse-app:
    build: .
    environment:
      - DATAVERSE_URL=https://yourorg.crm.dynamics.com
      - AZURE_CLIENT_ID=your-client-id
      - AZURE_CLIENT_SECRET=your-client-secret
      - AZURE_TENANT_ID=your-tenant-id
    volumes:
      - ./app:/app
```

## 📦 Instalação a partir do Código Fonte

### Via Git

```bash
# Clonar repositório
git clone https://github.com/joseandrefilho/dataverse-sdk-python.git
cd dataverse-sdk-python

# Instalar em modo desenvolvimento
pip install -e .

# Ou com dependências de desenvolvimento
pip install -e ".[dev]"
```

### Via Download

```bash
# Baixar e extrair
wget https://github.com/joseandrefilho/dataverse-sdk-python/archive/main.zip
unzip main.zip
cd dataverse-sdk-python-main

# Instalar
pip install .
```

## ✅ Verificação da Instalação

### Teste Básico

```bash
# Verificar se o SDK foi instalado
python -c "import dataverse_sdk; print('✅ SDK instalado com sucesso!')"

# Verificar versão
python -c "from dataverse_sdk import __version__; print(f'Versão: {__version__}')"

# Testar CLI
dv-cli --help
```

### Teste Completo

```python
import asyncio
from dataverse_sdk import DataverseSDK

async def test_installation():
    """Teste básico de instalação."""
    try:
        # Criar instância do SDK
        sdk = DataverseSDK()
        print("✅ SDK criado com sucesso")
        
        # Verificar se as dependências estão funcionando
        from dataverse_sdk.models import QueryOptions
        from dataverse_sdk.exceptions import DataverseError
        print("✅ Módulos importados com sucesso")
        
        print("🎉 Instalação verificada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")

# Executar teste
asyncio.run(test_installation())
```

## 🔧 Dependências

### Dependências Principais

```
httpx>=0.25.0          # Cliente HTTP assíncrono
pydantic>=2.0.0        # Validação de dados
msal>=1.24.0           # Autenticação Microsoft
typer[all]>=0.9.0      # CLI framework
rich>=13.0.0           # Output formatado
pandas>=2.0.0          # Manipulação de dados
tenacity>=8.0.0        # Retry logic
structlog>=23.0.0      # Logging estruturado
```

### Dependências de Desenvolvimento

```
pytest>=7.0.0          # Framework de testes
pytest-asyncio>=0.21.0 # Testes assíncronos
pytest-cov>=4.0.0     # Cobertura de testes
black>=23.0.0          # Formatação de código
isort>=5.12.0          # Organização de imports
flake8>=6.0.0          # Linting
mypy>=1.5.0            # Verificação de tipos
bandit>=1.7.0          # Análise de segurança
```

## 🚨 Problemas Comuns

### Erro: "No module named 'dataverse_sdk'"

```bash
# Verificar se está no ambiente virtual correto
which python
pip list | grep jaf-dataverse

# Reinstalar se necessário
pip uninstall jaf-dataverse-2025
pip install jaf-dataverse-2025
```

### Erro: "Microsoft Visual C++ 14.0 is required" (Windows)

```bash
# Instalar Microsoft C++ Build Tools
# Ou usar versão pré-compilada
pip install --only-binary=all jaf-dataverse-2025
```

### Erro de Dependências

```bash
# Atualizar pip
python -m pip install --upgrade pip

# Limpar cache
pip cache purge

# Reinstalar
pip install --no-cache-dir jaf-dataverse-2025
```

### Problemas de Rede/Proxy

```bash
# Configurar proxy
pip install --proxy http://user:password@proxy.server:port jaf-dataverse-2025

# Usar mirror alternativo
pip install -i https://pypi.douban.com/simple/ jaf-dataverse-2025
```

## 🔄 Atualizações

### Verificar Atualizações

```bash
# Verificar versão atual
pip show jaf-dataverse-2025

# Verificar se há atualizações
pip list --outdated | grep jaf-dataverse
```

### Atualizar SDK

```bash
# Atualizar para versão mais recente
pip install --upgrade jaf-dataverse-2025

# Atualizar para versão específica
pip install jaf-dataverse-2025==1.1.0
```

## 📱 Ambientes Específicos

### Jupyter Notebook

```bash
# Instalar no kernel do Jupyter
!pip install jaf-dataverse-2025

# Verificar instalação
import dataverse_sdk
print("✅ SDK disponível no Jupyter")
```

### Google Colab

```python
# Instalar no Colab
!pip install jaf-dataverse-2025

# Importar e usar
from dataverse_sdk import DataverseSDK
```

### Azure Functions

```bash
# requirements.txt
jaf-dataverse-2025>=1.0.0
azure-functions>=1.11.0
```

### AWS Lambda

```bash
# Criar layer ou incluir no deployment package
pip install jaf-dataverse-2025 -t ./package
```

## 🎯 Próximos Passos

Após a instalação bem-sucedida:

1. **[Configuração](configuration.md)** - Configure suas credenciais
2. **[Quickstart](quickstart.md)** - Primeiro uso do SDK
3. **[Autenticação](authentication.md)** - Configure autenticação
4. **[Tutoriais](../tutorials/)** - Aprenda com exemplos práticos

---

**💡 Dica**: Sempre use ambientes virtuais para isolar suas dependências e evitar conflitos!

