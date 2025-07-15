# AWS Glue Integration Guide

Este guia abrangente mostra como usar o **crmadminbrasil-dataverse-sdk** SDK no AWS Glue para criar pipelines de ETL robustos que integram dados entre o Microsoft Dataverse e outros sistemas.

## 📋 Visão Geral

AWS Glue é um serviço de ETL serverless que permite extrair, transformar e carregar dados entre diferentes fontes. Com o crmadminbrasil-dataverse-sdk SDK, você pode:

- **Extrair dados** do Dataverse para data lakes
- **Carregar dados** de diversas fontes para o Dataverse
- **Sincronizar dados** bidirecionalmente
- **Transformar dados** durante o processo de ETL
- **Automatizar pipelines** de integração

## 🏗️ Arquitetura de Integração

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │    AWS Glue     │    │   Dataverse     │
│                 │    │                 │    │                 │
│ • S3 Buckets    │───▶│ • ETL Jobs      │───▶│ • Accounts      │
│ • RDS           │    │ • Transformers  │    │ • Contacts      │
│ • DynamoDB      │    │ • Schedulers    │    │ • Custom Entities│
│ • APIs          │    │ • Crawlers      │    │ • Relationships │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Setup e Configuração

### 1. Preparação do Ambiente

#### Criar Role IAM para Glue

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "glue:*",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "*"
        }
    ]
}
```

#### Armazenar Credenciais no AWS Secrets Manager

```bash
# Criar secret para credenciais do Dataverse
aws secretsmanager create-secret \
    --name "dataverse/credentials" \
    --description "Credenciais para Microsoft Dataverse" \
    --secret-string '{
        "DATAVERSE_URL": "https://yourorg.crm.dynamics.com",
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret",
        "AZURE_TENANT_ID": "your-tenant-id"
    }'
```

### 2. Configuração do Job Glue

#### Parâmetros do Job

```python
# Job parameters no AWS Glue Console
{
    "--additional-python-modules": "crmadminbrasil-dataverse-sdk==1.0.0",
    "--python-modules-installer-option": "--upgrade",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true",
    "--job-bookmark-option": "job-bookmark-enable",
    "--TempDir": "s3://your-glue-temp-bucket/temp/",
    "--secret-name": "dataverse/credentials"
}
```

## 📥 Extração de Dados (Dataverse → AWS)

### Exemplo 1: Extrair Contas para S3

```python
import sys
import boto3
import json
import asyncio
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from dataverse_sdk import DataverseSDK
import pandas as pd

# Inicializar contextos Glue
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Obter parâmetros do job
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'secret-name',
    'output-bucket',
    'output-prefix'
])

job.init(args['JOB_NAME'], args)

def get_dataverse_credentials(secret_name):
    """Obter credenciais do AWS Secrets Manager."""
    secrets_client = boto3.client('secretsmanager')
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

async def extract_accounts_to_s3():
    """Extrair contas do Dataverse e salvar no S3."""
    
    # Obter credenciais
    credentials = get_dataverse_credentials(args['secret_name'])
    
    # Configurar SDK
    sdk = DataverseSDK(
        dataverse_url=credentials['DATAVERSE_URL'],
        client_id=credentials['AZURE_CLIENT_ID'],
        client_secret=credentials['AZURE_CLIENT_SECRET'],
        tenant_id=credentials['AZURE_TENANT_ID']
    )
    
    try:
        async with sdk:
            print("🔄 Iniciando extração de contas...")
            
            # Extrair todas as contas com paginação automática
            accounts = await sdk.query("accounts", {
                "select": [
                    "accountid", "name", "websiteurl", "telephone1",
                    "emailaddress1", "address1_city", "address1_country",
                    "createdon", "modifiedon", "statuscode"
                ],
                "filter": "statuscode eq 1",  # Apenas contas ativas
                "order_by": ["createdon desc"]
            })
            
            print(f"✅ Extraídas {len(accounts.value)} contas")
            
            # Converter para DataFrame pandas
            df = pd.DataFrame(accounts.value)
            
            # Transformações básicas
            df['extraction_date'] = pd.Timestamp.now()
            df['source'] = 'dataverse'
            
            # Converter para Spark DataFrame
            spark_df = spark.createDataFrame(df)
            
            # Salvar no S3 em formato Parquet particionado por data
            output_path = f"s3://{args['output_bucket']}/{args['output_prefix']}/accounts/"
            
            spark_df.write \
                .mode("overwrite") \
                .partitionBy("extraction_date") \
                .parquet(output_path)
            
            print(f"✅ Dados salvos em: {output_path}")
            
            # Registrar métricas
            glueContext.write_dynamic_frame.from_options(
                frame=DynamicFrame.fromDF(spark_df, glueContext, "accounts"),
                connection_type="s3",
                connection_options={
                    "path": output_path,
                    "partitionKeys": ["extraction_date"]
                },
                format="parquet"
            )
            
    except Exception as e:
        print(f"❌ Erro na extração: {str(e)}")
        raise

# Executar extração
asyncio.run(extract_accounts_to_s3())

job.commit()
```

### Exemplo 2: Extração Incremental com Job Bookmark

```python
async def extract_contacts_incremental():
    """Extração incremental de contatos usando Job Bookmark."""
    
    credentials = get_dataverse_credentials(args['secret_name'])
    sdk = DataverseSDK(**credentials)
    
    # Obter último timestamp do Job Bookmark
    bookmark = job.get_bookmark()
    last_modified = bookmark.get('last_modified', '1900-01-01T00:00:00Z')
    
    async with sdk:
        print(f"🔄 Extração incremental desde: {last_modified}")
        
        # Consultar apenas registros modificados
        contacts = await sdk.query("contacts", {
            "select": [
                "contactid", "fullname", "emailaddress1", "telephone1",
                "parentcustomerid", "createdon", "modifiedon"
            ],
            "filter": f"modifiedon gt {last_modified}",
            "order_by": ["modifiedon asc"]
        })
        
        if contacts.value:
            print(f"✅ Encontrados {len(contacts.value)} contatos modificados")
            
            # Processar dados
            df = pd.DataFrame(contacts.value)
            df['extraction_timestamp'] = pd.Timestamp.now()
            
            # Salvar no S3
            spark_df = spark.createDataFrame(df)
            output_path = f"s3://{args['output_bucket']}/{args['output_prefix']}/contacts_incremental/"
            
            spark_df.write \
                .mode("append") \
                .partitionBy("extraction_timestamp") \
                .parquet(output_path)
            
            # Atualizar bookmark com último timestamp
            max_modified = df['modifiedon'].max()
            job.update_bookmark({'last_modified': max_modified})
            
            print(f"✅ Bookmark atualizado para: {max_modified}")
        else:
            print("ℹ️ Nenhum registro novo encontrado")

asyncio.run(extract_contacts_incremental())
```

## 📤 Carregamento de Dados (AWS → Dataverse)

### Exemplo 3: Carregar Dados do S3 para Dataverse

```python
async def load_data_to_dataverse():
    """Carregar dados do S3 para o Dataverse."""
    
    credentials = get_dataverse_credentials(args['secret_name'])
    sdk = DataverseSDK(**credentials)
    
    # Ler dados do S3
    input_path = f"s3://{args['input_bucket']}/{args['input_prefix']}/new_accounts/"
    df = spark.read.parquet(input_path).toPandas()
    
    print(f"🔄 Carregando {len(df)} registros para o Dataverse...")
    
    async with sdk:
        # Preparar dados para inserção
        accounts_data = []
        
        for _, row in df.iterrows():
            account_data = {
                "name": row['company_name'],
                "websiteurl": row['website'],
                "telephone1": row['phone'],
                "emailaddress1": row['email'],
                "address1_city": row['city'],
                "address1_country": row['country'],
                "description": f"Importado via AWS Glue em {pd.Timestamp.now()}"
            }
            accounts_data.append(account_data)
        
        # Usar bulk operations para performance
        try:
            result = await sdk.bulk_create(
                "accounts",
                accounts_data,
                batch_size=100,  # Processar em lotes de 100
                parallel=True    # Execução paralela
            )
            
            print(f"✅ Criação em lote concluída:")
            print(f"   - Sucessos: {result.successful}")
            print(f"   - Falhas: {result.failed}")
            print(f"   - Taxa de sucesso: {result.success_rate:.1f}%")
            
            # Log de erros se houver
            if result.has_errors:
                print("⚠️ Erros encontrados:")
                for error in result.errors[:5]:  # Mostrar primeiros 5 erros
                    print(f"   - {error}")
            
            # Salvar relatório no S3
            report = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'total_records': len(accounts_data),
                'successful': result.successful,
                'failed': result.failed,
                'success_rate': result.success_rate,
                'errors': result.errors[:10] if result.has_errors else []
            }
            
            report_path = f"s3://{args['output_bucket']}/reports/load_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Salvar relatório
            s3_client = boto3.client('s3')
            s3_client.put_object(
                Bucket=args['output_bucket'],
                Key=report_path.replace(f"s3://{args['output_bucket']}/", ""),
                Body=json.dumps(report, indent=2),
                ContentType='application/json'
            )
            
        except Exception as e:
            print(f"❌ Erro no carregamento: {str(e)}")
            raise

asyncio.run(load_data_to_dataverse())
```

### Exemplo 4: Sincronização Bidirecional

```python
async def bidirectional_sync():
    """Sincronização bidirecional entre S3 e Dataverse."""
    
    credentials = get_dataverse_credentials(args['secret_name'])
    sdk = DataverseSDK(**credentials)
    
    async with sdk:
        # 1. Extrair dados modificados do Dataverse
        print("🔄 Fase 1: Extraindo dados do Dataverse...")
        
        dataverse_contacts = await sdk.query("contacts", {
            "select": ["contactid", "fullname", "emailaddress1", "modifiedon"],
            "filter": f"modifiedon gt {args.get('last_sync', '1900-01-01T00:00:00Z')}",
            "order_by": ["modifiedon desc"]
        })
        
        # 2. Ler dados do sistema externo (S3)
        print("🔄 Fase 2: Lendo dados externos...")
        
        external_data_path = f"s3://{args['input_bucket']}/external_contacts/"
        external_df = spark.read.parquet(external_data_path).toPandas()
        
        # 3. Identificar conflitos e resoluções
        print("🔄 Fase 3: Resolvendo conflitos...")
        
        # Lógica de merge baseada em timestamp
        dataverse_df = pd.DataFrame(dataverse_contacts.value)
        
        # Merge inteligente
        merged_data = resolve_conflicts(dataverse_df, external_df)
        
        # 4. Aplicar mudanças no Dataverse
        print("🔄 Fase 4: Aplicando mudanças no Dataverse...")
        
        updates_for_dataverse = merged_data[merged_data['action'] == 'update_dataverse']
        
        if not updates_for_dataverse.empty:
            update_data = []
            for _, row in updates_for_dataverse.iterrows():
                update_data.append({
                    'id': row['contactid'],
                    'fullname': row['fullname'],
                    'emailaddress1': row['emailaddress1']
                })
            
            update_result = await sdk.bulk_update("contacts", update_data)
            print(f"✅ Atualizados {update_result.successful} contatos no Dataverse")
        
        # 5. Salvar dados atualizados no S3
        print("🔄 Fase 5: Salvando dados sincronizados...")
        
        final_df = spark.createDataFrame(merged_data)
        sync_output_path = f"s3://{args['output_bucket']}/synchronized_data/"
        
        final_df.write \
            .mode("overwrite") \
            .partitionBy("sync_date") \
            .parquet(sync_output_path)
        
        print("✅ Sincronização bidirecional concluída")

def resolve_conflicts(dataverse_df, external_df):
    """Resolver conflitos entre dados do Dataverse e externos."""
    
    # Merge baseado em email
    merged = pd.merge(
        dataverse_df, external_df,
        left_on='emailaddress1', right_on='email',
        how='outer', suffixes=('_dv', '_ext')
    )
    
    # Lógica de resolução: usar timestamp mais recente
    merged['action'] = 'no_change'
    merged['sync_date'] = pd.Timestamp.now().date()
    
    # Identificar registros que precisam ser atualizados
    mask_update_dv = (
        merged['modifiedon_ext'] > merged['modifiedon_dv']
    ) & merged['contactid'].notna()
    
    merged.loc[mask_update_dv, 'action'] = 'update_dataverse'
    
    return merged

asyncio.run(bidirectional_sync())
```

## 🔄 Pipelines Avançados

### Pipeline de ETL Completo

```python
class DataversePipeline:
    """Pipeline ETL completo para Dataverse."""
    
    def __init__(self, credentials, spark_context):
        self.credentials = credentials
        self.spark = spark_context
        self.sdk = None
    
    async def __aenter__(self):
        self.sdk = DataverseSDK(**self.credentials)
        await self.sdk.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.sdk:
            await self.sdk.__aexit__(exc_type, exc_val, exc_tb)
    
    async def extract_entity_data(self, entity_name, query_options=None):
        """Extrair dados de uma entidade."""
        print(f"🔄 Extraindo dados de {entity_name}...")
        
        default_options = {
            "select": ["*"],
            "order_by": ["createdon desc"]
        }
        
        if query_options:
            default_options.update(query_options)
        
        data = await self.sdk.query(entity_name, default_options)
        print(f"✅ Extraídos {len(data.value)} registros de {entity_name}")
        
        return pd.DataFrame(data.value)
    
    def transform_data(self, df, transformations):
        """Aplicar transformações nos dados."""
        print("🔄 Aplicando transformações...")
        
        for transform in transformations:
            df = transform(df)
        
        print("✅ Transformações aplicadas")
        return df
    
    async def load_to_dataverse(self, entity_name, data, operation='create'):
        """Carregar dados para o Dataverse."""
        print(f"🔄 Carregando {len(data)} registros para {entity_name}...")
        
        if operation == 'create':
            result = await self.sdk.bulk_create(entity_name, data.to_dict('records'))
        elif operation == 'update':
            result = await self.sdk.bulk_update(entity_name, data.to_dict('records'))
        elif operation == 'upsert':
            result = await self.sdk.bulk_upsert(entity_name, data.to_dict('records'))
        
        print(f"✅ Operação {operation} concluída: {result.successful} sucessos, {result.failed} falhas")
        return result
    
    def save_to_s3(self, df, path, format='parquet', partition_cols=None):
        """Salvar DataFrame no S3."""
        print(f"🔄 Salvando dados em {path}...")
        
        spark_df = self.spark.createDataFrame(df)
        
        writer = spark_df.write.mode("overwrite")
        
        if partition_cols:
            writer = writer.partitionBy(partition_cols)
        
        if format == 'parquet':
            writer.parquet(path)
        elif format == 'json':
            writer.json(path)
        elif format == 'csv':
            writer.csv(path, header=True)
        
        print(f"✅ Dados salvos em {path}")

# Uso do pipeline
async def run_etl_pipeline():
    """Executar pipeline ETL completo."""
    
    credentials = get_dataverse_credentials(args['secret_name'])
    
    async with DataversePipeline(credentials, spark) as pipeline:
        
        # 1. Extrair dados
        accounts_df = await pipeline.extract_entity_data("accounts", {
            "filter": "statuscode eq 1",
            "select": ["accountid", "name", "websiteurl", "createdon"]
        })
        
        # 2. Transformar dados
        def add_metadata(df):
            df['processed_date'] = pd.Timestamp.now()
            df['source'] = 'dataverse_etl'
            return df
        
        def clean_data(df):
            # Limpar URLs
            df['websiteurl'] = df['websiteurl'].str.lower().str.strip()
            # Remover registros sem nome
            df = df.dropna(subset=['name'])
            return df
        
        transformed_df = pipeline.transform_data(accounts_df, [add_metadata, clean_data])
        
        # 3. Salvar no Data Lake
        pipeline.save_to_s3(
            transformed_df,
            f"s3://{args['output_bucket']}/processed/accounts/",
            partition_cols=['processed_date']
        )
        
        # 4. Criar registros derivados no Dataverse
        # Exemplo: criar oportunidades para contas grandes
        large_accounts = transformed_df[transformed_df['name'].str.len() > 20]
        
        if not large_accounts.empty:
            opportunities_data = []
            for _, account in large_accounts.iterrows():
                opportunities_data.append({
                    "name": f"Oportunidade - {account['name']}",
                    f"parentaccountid@odata.bind": f"accounts({account['accountid']})",
                    "description": "Oportunidade criada automaticamente via ETL"
                })
            
            await pipeline.load_to_dataverse("opportunities", pd.DataFrame(opportunities_data))

asyncio.run(run_etl_pipeline())
```

## 📊 Monitoramento e Logging

### CloudWatch Metrics Customizadas

```python
import boto3

def send_custom_metrics(metric_name, value, unit='Count'):
    """Enviar métricas customizadas para CloudWatch."""
    
    cloudwatch = boto3.client('cloudwatch')
    
    cloudwatch.put_metric_data(
        Namespace='DataverseETL',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Dimensions': [
                    {
                        'Name': 'JobName',
                        'Value': args['JOB_NAME']
                    }
                ]
            }
        ]
    )

# Exemplo de uso
async def monitored_extraction():
    """Extração com monitoramento."""
    
    start_time = time.time()
    
    try:
        # Sua lógica de extração aqui
        result = await extract_data()
        
        # Métricas de sucesso
        send_custom_metrics('RecordsExtracted', len(result))
        send_custom_metrics('ExtractionSuccess', 1)
        
    except Exception as e:
        # Métricas de erro
        send_custom_metrics('ExtractionErrors', 1)
        print(f"❌ Erro: {str(e)}")
        raise
    
    finally:
        # Tempo de execução
        execution_time = time.time() - start_time
        send_custom_metrics('ExecutionTime', execution_time, 'Seconds')
```

## 🚨 Tratamento de Erros e Retry

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def resilient_dataverse_operation(operation_func, *args, **kwargs):
    """Operação resiliente com retry automático."""
    
    try:
        return await operation_func(*args, **kwargs)
    
    except Exception as e:
        print(f"⚠️ Erro na operação, tentando novamente: {str(e)}")
        raise

# Uso
async def safe_bulk_create(entity_name, data):
    """Criação em lote com retry."""
    
    return await resilient_dataverse_operation(
        sdk.bulk_create,
        entity_name,
        data,
        batch_size=50
    )
```

## 📅 Agendamento e Triggers

### CloudFormation Template para Trigger

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Dataverse ETL Pipeline with S3 Trigger'

Resources:
  DataverseETLJob:
    Type: AWS::Glue::Job
    Properties:
      Name: dataverse-etl-pipeline
      Role: !Ref GlueServiceRole
      Command:
        Name: pythonshell
        PythonVersion: '3.9'
        ScriptLocation: s3://your-scripts-bucket/dataverse_etl.py
      DefaultArguments:
        '--additional-python-modules': 'crmadminbrasil-dataverse-sdk==1.0.0'
        '--secret-name': 'dataverse/credentials'
      MaxRetries: 2
      Timeout: 60

  S3TriggerLambda:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: dataverse-etl-trigger
      Runtime: python3.9
      Handler: index.lambda_handler
      Code:
        ZipFile: |
          import boto3
          import json
          
          def lambda_handler(event, context):
              glue = boto3.client('glue')
              
              for record in event['Records']:
                  bucket = record['s3']['bucket']['name']
                  key = record['s3']['object']['key']
                  
                  if key.startswith('incoming-data/'):
                      glue.start_job_run(
                          JobName='dataverse-etl-pipeline',
                          Arguments={
                              '--input-bucket': bucket,
                              '--input-key': key
                          }
                      )
              
              return {'statusCode': 200}

  S3BucketNotification:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: your-etl-bucket
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: s3:ObjectCreated:*
            Function: !GetAtt S3TriggerLambda.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: incoming-data/
```

## 🔧 Otimização de Performance

### Configurações Recomendadas

```python
# Configurações otimizadas para Glue
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

# Configurações do SDK para performance
sdk_config = {
    'max_connections': 100,
    'timeout': 300,
    'retry_attempts': 3,
    'batch_size': 1000
}

sdk = DataverseSDK(**credentials, **sdk_config)
```

### Paralelização Inteligente

```python
async def parallel_entity_processing(entities):
    """Processar múltiplas entidades em paralelo."""
    
    import asyncio
    
    async def process_entity(entity_name):
        data = await sdk.query(entity_name, {"select": ["*"]})
        # Processar dados
        return process_data(data)
    
    # Executar em paralelo com limite de concorrência
    semaphore = asyncio.Semaphore(5)  # Máximo 5 entidades simultâneas
    
    async def bounded_process(entity):
        async with semaphore:
            return await process_entity(entity)
    
    results = await asyncio.gather(*[
        bounded_process(entity) for entity in entities
    ])
    
    return results
```

## 📋 Checklist de Deployment

### Pré-deployment

- [ ] Credenciais configuradas no Secrets Manager
- [ ] Role IAM com permissões adequadas
- [ ] Buckets S3 criados e configurados
- [ ] Scripts testados localmente
- [ ] Parâmetros do job validados

### Pós-deployment

- [ ] Logs do CloudWatch funcionando
- [ ] Métricas sendo coletadas
- [ ] Alertas configurados
- [ ] Testes de integração executados
- [ ] Documentação atualizada

## 🆘 Troubleshooting

### Problemas Comuns

#### Erro: "Module not found: dataverse_sdk"

```python
# Verificar se o módulo foi instalado corretamente
import sys
print(sys.path)

# Forçar reinstalação
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "crmadminbrasil-dataverse-sdk"])
```

#### Erro: "Authentication failed"

```python
# Verificar credenciais
credentials = get_dataverse_credentials(args['secret_name'])
print("Credenciais carregadas:", list(credentials.keys()))

# Testar autenticação
async def test_auth():
    sdk = DataverseSDK(**credentials)
    async with sdk:
        # Teste simples
        result = await sdk.query("accounts", {"top": 1})
        print("Autenticação OK")

asyncio.run(test_auth())
```

#### Timeout em Operações Grandes

```python
# Aumentar timeout e usar chunking
sdk = DataverseSDK(
    **credentials,
    timeout=600,  # 10 minutos
    max_connections=50
)

# Processar em chunks menores
async def chunked_processing(data, chunk_size=100):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        await sdk.bulk_create("entity", chunk)
        await asyncio.sleep(1)  # Pausa entre chunks
```

## 📚 Recursos Adicionais

- **AWS Glue Documentation**: https://docs.aws.amazon.com/glue/
- **Dataverse Web API**: https://docs.microsoft.com/en-us/powerapps/developer/data-platform/webapi/
- **SDK GitHub**: https://github.com/joseandrefilho/dataverse-sdk-python
- **PyPI Package**: https://pypi.org/project/crmadminbrasil-dataverse-sdk/

---

**💡 Dica**: Sempre teste seus jobs Glue em ambiente de desenvolvimento antes de executar em produção, e monitore o consumo de DPUs para otimizar custos!

