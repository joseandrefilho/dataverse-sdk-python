# Real-World ETL Scenarios

Este tutorial apresenta cenários reais de ETL usando o **jaf-dataverse-2025** SDK, com foco em casos de uso práticos encontrados em empresas.

## 🏢 Cenário 1: Migração de CRM Legacy para Dataverse

### Contexto
Uma empresa precisa migrar dados de um sistema CRM antigo para o Microsoft Dataverse, mantendo a integridade dos relacionamentos e histórico.

### Arquitetura
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Legacy CRM    │    │   AWS Glue      │    │   Dataverse     │
│                 │    │                 │    │                 │
│ • MySQL DB      │───▶│ • Data Mapping  │───▶│ • Accounts      │
│ • 500K Accounts │    │ • Validation    │    │ • Contacts      │
│ • 2M Contacts   │    │ • Deduplication │    │ • Opportunities │
│ • 100K Deals    │    │ • Relationships │    │ • Activities    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Implementação

```python
import asyncio
import pandas as pd
from dataverse_sdk import DataverseSDK
from sqlalchemy import create_engine
import logging

class CRMMigrationPipeline:
    """Pipeline de migração de CRM legacy para Dataverse."""
    
    def __init__(self, legacy_db_url, dataverse_credentials):
        self.legacy_engine = create_engine(legacy_db_url)
        self.dataverse_sdk = DataverseSDK(**dataverse_credentials)
        self.migration_log = []
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        await self.dataverse_sdk.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.dataverse_sdk.__aexit__(exc_type, exc_val, exc_tb)
    
    def extract_legacy_accounts(self):
        """Extrair contas do sistema legacy."""
        
        query = """
        SELECT 
            id as legacy_id,
            company_name,
            website,
            phone,
            email,
            address_street,
            address_city,
            address_state,
            address_country,
            industry,
            annual_revenue,
            employee_count,
            created_date,
            modified_date,
            status
        FROM companies 
        WHERE status = 'active'
        ORDER BY created_date
        """
        
        self.logger.info("🔄 Extraindo contas do sistema legacy...")
        df = pd.read_sql(query, self.legacy_engine)
        self.logger.info(f"✅ Extraídas {len(df)} contas")
        
        return df
    
    def transform_accounts(self, legacy_df):
        """Transformar dados de contas para formato Dataverse."""
        
        self.logger.info("🔄 Transformando dados de contas...")
        
        # Mapeamento de campos
        transformed_df = pd.DataFrame()
        
        # Campos obrigatórios
        transformed_df['name'] = legacy_df['company_name']
        
        # Campos opcionais com validação
        transformed_df['websiteurl'] = legacy_df['website'].apply(self._clean_url)
        transformed_df['telephone1'] = legacy_df['phone'].apply(self._clean_phone)
        transformed_df['emailaddress1'] = legacy_df['email'].apply(self._clean_email)
        
        # Endereço
        transformed_df['address1_line1'] = legacy_df['address_street']
        transformed_df['address1_city'] = legacy_df['address_city']
        transformed_df['address1_stateorprovince'] = legacy_df['address_state']
        transformed_df['address1_country'] = legacy_df['address_country']
        
        # Campos de negócio
        transformed_df['industrycode'] = legacy_df['industry'].apply(self._map_industry)
        transformed_df['revenue'] = legacy_df['annual_revenue']
        transformed_df['numberofemployees'] = legacy_df['employee_count']
        
        # Metadados de migração
        transformed_df['description'] = legacy_df.apply(
            lambda row: f"Migrado do sistema legacy (ID: {row['legacy_id']}) em {pd.Timestamp.now()}",
            axis=1
        )
        
        # Manter referência do ID legacy
        transformed_df['legacy_id'] = legacy_df['legacy_id']
        
        self.logger.info(f"✅ Transformadas {len(transformed_df)} contas")
        return transformed_df
    
    def _clean_url(self, url):
        """Limpar e validar URLs."""
        if pd.isna(url) or url == '':
            return None
        
        url = str(url).strip().lower()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url if len(url) <= 200 else url[:200]
    
    def _clean_phone(self, phone):
        """Limpar números de telefone."""
        if pd.isna(phone):
            return None
        
        # Remover caracteres não numéricos exceto + e espaços
        import re
        cleaned = re.sub(r'[^\d\+\s\-\(\)]', '', str(phone))
        return cleaned[:50] if cleaned else None
    
    def _clean_email(self, email):
        """Validar emails."""
        if pd.isna(email):
            return None
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        email = str(email).strip().lower()
        return email if re.match(email_pattern, email) else None
    
    def _map_industry(self, industry):
        """Mapear indústrias para códigos Dataverse."""
        
        industry_mapping = {
            'technology': 1,
            'healthcare': 2,
            'finance': 3,
            'manufacturing': 4,
            'retail': 5,
            'education': 6,
            'government': 7,
            'nonprofit': 8
        }
        
        if pd.isna(industry):
            return None
        
        industry_lower = str(industry).lower()
        return industry_mapping.get(industry_lower, 1)  # Default: technology
    
    async def load_accounts(self, accounts_df):
        """Carregar contas no Dataverse."""
        
        self.logger.info(f"🔄 Carregando {len(accounts_df)} contas no Dataverse...")
        
        # Remover campo legacy_id antes do upload
        upload_df = accounts_df.drop('legacy_id', axis=1)
        
        # Converter para lista de dicionários
        accounts_data = upload_df.to_dict('records')
        
        # Carregar em lotes
        result = await self.dataverse_sdk.bulk_create(
            "accounts",
            accounts_data,
            batch_size=100,
            parallel=True
        )
        
        self.logger.info(f"✅ Carregamento concluído:")
        self.logger.info(f"   - Sucessos: {result.successful}")
        self.logger.info(f"   - Falhas: {result.failed}")
        
        # Log de erros
        if result.has_errors:
            self.logger.warning("⚠️ Erros encontrados:")
            for i, error in enumerate(result.errors[:5]):
                self.logger.warning(f"   {i+1}. {error}")
        
        return result
    
    async def create_id_mapping(self, legacy_df, creation_result):
        """Criar mapeamento entre IDs legacy e Dataverse."""
        
        self.logger.info("🔄 Criando mapeamento de IDs...")
        
        # Consultar contas criadas para obter IDs do Dataverse
        created_accounts = await self.dataverse_sdk.query("accounts", {
            "select": ["accountid", "name", "description"],
            "filter": "contains(description, 'Migrado do sistema legacy')",
            "order_by": ["createdon desc"]
        })
        
        # Extrair legacy_id da descrição
        id_mapping = {}
        
        for account in created_accounts.value:
            description = account.get('description', '')
            
            # Extrair legacy_id da descrição usando regex
            import re
            match = re.search(r'ID: (\d+)', description)
            
            if match:
                legacy_id = int(match.group(1))
                dataverse_id = account['accountid']
                id_mapping[legacy_id] = dataverse_id
        
        self.logger.info(f"✅ Mapeamento criado para {len(id_mapping)} contas")
        
        # Salvar mapeamento para uso posterior
        mapping_df = pd.DataFrame([
            {'legacy_id': k, 'dataverse_id': v} 
            for k, v in id_mapping.items()
        ])
        
        return mapping_df
    
    async def migrate_contacts(self, account_mapping):
        """Migrar contatos com relacionamentos."""
        
        # Extrair contatos do sistema legacy
        contacts_query = """
        SELECT 
            id as legacy_id,
            company_id as legacy_company_id,
            first_name,
            last_name,
            email,
            phone,
            mobile,
            job_title,
            department,
            created_date,
            status
        FROM contacts 
        WHERE status = 'active'
        ORDER BY created_date
        """
        
        self.logger.info("🔄 Extraindo contatos do sistema legacy...")
        contacts_df = pd.read_sql(contacts_query, self.legacy_engine)
        self.logger.info(f"✅ Extraídos {len(contacts_df)} contatos")
        
        # Transformar dados
        transformed_contacts = pd.DataFrame()
        
        # Campos básicos
        transformed_contacts['firstname'] = contacts_df['first_name']
        transformed_contacts['lastname'] = contacts_df['last_name']
        transformed_contacts['emailaddress1'] = contacts_df['email'].apply(self._clean_email)
        transformed_contacts['telephone1'] = contacts_df['phone'].apply(self._clean_phone)
        transformed_contacts['mobilephone'] = contacts_df['mobile'].apply(self._clean_phone)
        transformed_contacts['jobtitle'] = contacts_df['job_title']
        transformed_contacts['department'] = contacts_df['department']
        
        # Relacionamento com conta
        account_mapping_dict = dict(zip(account_mapping['legacy_id'], account_mapping['dataverse_id']))
        
        def map_parent_account(legacy_company_id):
            if pd.isna(legacy_company_id):
                return None
            
            dataverse_account_id = account_mapping_dict.get(int(legacy_company_id))
            return f"accounts({dataverse_account_id})" if dataverse_account_id else None
        
        transformed_contacts['parentcustomerid@odata.bind'] = contacts_df['legacy_company_id'].apply(map_parent_account)
        
        # Metadados
        transformed_contacts['description'] = contacts_df.apply(
            lambda row: f"Migrado do sistema legacy (ID: {row['legacy_id']})",
            axis=1
        )
        
        # Remover contatos sem conta pai válida
        valid_contacts = transformed_contacts.dropna(subset=['parentcustomerid@odata.bind'])
        
        self.logger.info(f"🔄 Carregando {len(valid_contacts)} contatos válidos...")
        
        # Carregar contatos
        contacts_data = valid_contacts.to_dict('records')
        
        result = await self.dataverse_sdk.bulk_create(
            "contacts",
            contacts_data,
            batch_size=100,
            parallel=True
        )
        
        self.logger.info(f"✅ Contatos carregados:")
        self.logger.info(f"   - Sucessos: {result.successful}")
        self.logger.info(f"   - Falhas: {result.failed}")
        
        return result

# Uso do pipeline
async def run_crm_migration():
    """Executar migração completa do CRM."""
    
    # Configurações
    legacy_db_url = "mysql://user:password@legacy-db:3306/crm_database"
    
    dataverse_credentials = {
        'dataverse_url': 'https://yourorg.crm.dynamics.com',
        'client_id': 'your-client-id',
        'client_secret': 'your-client-secret',
        'tenant_id': 'your-tenant-id'
    }
    
    async with CRMMigrationPipeline(legacy_db_url, dataverse_credentials) as pipeline:
        
        # 1. Migrar contas
        legacy_accounts = pipeline.extract_legacy_accounts()
        transformed_accounts = pipeline.transform_accounts(legacy_accounts)
        accounts_result = await pipeline.load_accounts(transformed_accounts)
        
        # 2. Criar mapeamento de IDs
        account_mapping = await pipeline.create_id_mapping(legacy_accounts, accounts_result)
        
        # 3. Migrar contatos
        contacts_result = await pipeline.migrate_contacts(account_mapping)
        
        print("🎉 Migração concluída com sucesso!")
        print(f"   - Contas migradas: {accounts_result.successful}")
        print(f"   - Contatos migrados: {contacts_result.successful}")

# Executar migração
asyncio.run(run_crm_migration())
```

## 🏪 Cenário 2: Sincronização E-commerce com Dataverse

### Contexto
Uma empresa de e-commerce precisa sincronizar dados de pedidos, clientes e produtos entre sua plataforma online e o Dataverse para análise de vendas e CRM.

### Implementação

```python
class EcommerceSyncPipeline:
    """Pipeline de sincronização e-commerce com Dataverse."""
    
    def __init__(self, ecommerce_api_config, dataverse_credentials):
        self.api_config = ecommerce_api_config
        self.dataverse_sdk = DataverseSDK(**dataverse_credentials)
        self.sync_state = {}
    
    async def __aenter__(self):
        await self.dataverse_sdk.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.dataverse_sdk.__aexit__(exc_type, exc_val, exc_tb)
    
    async def sync_customers(self):
        """Sincronizar clientes do e-commerce."""
        
        # Obter último timestamp de sincronização
        last_sync = self.sync_state.get('customers_last_sync', '1900-01-01T00:00:00Z')
        
        # Extrair clientes modificados da API do e-commerce
        customers_data = await self._fetch_ecommerce_customers(last_sync)
        
        if not customers_data:
            print("ℹ️ Nenhum cliente novo para sincronizar")
            return
        
        print(f"🔄 Sincronizando {len(customers_data)} clientes...")
        
        # Transformar para formato Dataverse
        dataverse_customers = []
        
        for customer in customers_data:
            # Verificar se cliente já existe
            existing = await self._find_existing_customer(customer['email'])
            
            customer_data = {
                'firstname': customer['first_name'],
                'lastname': customer['last_name'],
                'emailaddress1': customer['email'],
                'telephone1': customer.get('phone'),
                'address1_line1': customer.get('address', {}).get('street'),
                'address1_city': customer.get('address', {}).get('city'),
                'address1_stateorprovince': customer.get('address', {}).get('state'),
                'address1_postalcode': customer.get('address', {}).get('zip'),
                'address1_country': customer.get('address', {}).get('country'),
                'description': f"Cliente e-commerce (ID: {customer['id']})"
            }
            
            if existing:
                # Atualizar cliente existente
                customer_data['contactid'] = existing['contactid']
                dataverse_customers.append(customer_data)
            else:
                # Criar novo cliente
                dataverse_customers.append(customer_data)
        
        # Separar criações e atualizações
        new_customers = [c for c in dataverse_customers if 'contactid' not in c]
        update_customers = [c for c in dataverse_customers if 'contactid' in c]
        
        # Executar operações
        if new_customers:
            create_result = await self.dataverse_sdk.bulk_create("contacts", new_customers)
            print(f"✅ Criados {create_result.successful} novos clientes")
        
        if update_customers:
            update_result = await self.dataverse_sdk.bulk_update("contacts", update_customers)
            print(f"✅ Atualizados {update_result.successful} clientes")
        
        # Atualizar timestamp de sincronização
        self.sync_state['customers_last_sync'] = max(c['updated_at'] for c in customers_data)
    
    async def sync_orders(self):
        """Sincronizar pedidos como oportunidades."""
        
        last_sync = self.sync_state.get('orders_last_sync', '1900-01-01T00:00:00Z')
        
        # Extrair pedidos da API
        orders_data = await self._fetch_ecommerce_orders(last_sync)
        
        if not orders_data:
            print("ℹ️ Nenhum pedido novo para sincronizar")
            return
        
        print(f"🔄 Sincronizando {len(orders_data)} pedidos...")
        
        dataverse_opportunities = []
        
        for order in orders_data:
            # Encontrar cliente correspondente
            customer = await self._find_existing_customer(order['customer_email'])
            
            if not customer:
                print(f"⚠️ Cliente não encontrado para pedido {order['id']}")
                continue
            
            # Mapear status do pedido
            status_mapping = {
                'pending': 1,      # Em andamento
                'processing': 1,   # Em andamento
                'shipped': 2,      # Ganha
                'delivered': 2,    # Ganha
                'cancelled': 3,    # Perdida
                'refunded': 3      # Perdida
            }
            
            opportunity_data = {
                'name': f"Pedido #{order['order_number']}",
                'description': f"Pedido e-commerce (ID: {order['id']})",
                f"parentcontactid@odata.bind": f"contacts({customer['contactid']})",
                'estimatedvalue': order['total_amount'],
                'actualvalue': order['total_amount'] if order['status'] in ['shipped', 'delivered'] else None,
                'statuscode': status_mapping.get(order['status'], 1),
                'closeprobability': 100 if order['status'] in ['shipped', 'delivered'] else 50,
                'estimatedclosedate': order['created_at'],
                'actualclosedate': order.get('shipped_at') or order.get('delivered_at')
            }
            
            dataverse_opportunities.append(opportunity_data)
        
        # Carregar oportunidades
        if dataverse_opportunities:
            result = await self.dataverse_sdk.bulk_create("opportunities", dataverse_opportunities)
            print(f"✅ Criadas {result.successful} oportunidades")
        
        # Atualizar timestamp
        self.sync_state['orders_last_sync'] = max(o['updated_at'] for o in orders_data)
    
    async def sync_products(self):
        """Sincronizar produtos como entidades customizadas."""
        
        # Extrair produtos da API
        products_data = await self._fetch_ecommerce_products()
        
        print(f"🔄 Sincronizando {len(products_data)} produtos...")
        
        dataverse_products = []
        
        for product in products_data:
            product_data = {
                'name': product['name'],
                'description': product['description'],
                'new_sku': product['sku'],
                'new_price': product['price'],
                'new_category': product['category'],
                'new_stock_quantity': product['stock_quantity'],
                'new_is_active': product['is_active'],
                'new_ecommerce_id': str(product['id'])
            }
            
            dataverse_products.append(product_data)
        
        # Usar upsert baseado no SKU
        result = await self.dataverse_sdk.bulk_upsert("new_products", dataverse_products)
        print(f"✅ Sincronizados {result.successful} produtos")
    
    async def _fetch_ecommerce_customers(self, since):
        """Buscar clientes da API do e-commerce."""
        # Implementação específica da API
        # Retorna lista de clientes modificados desde 'since'
        pass
    
    async def _fetch_ecommerce_orders(self, since):
        """Buscar pedidos da API do e-commerce."""
        # Implementação específica da API
        pass
    
    async def _fetch_ecommerce_products(self):
        """Buscar produtos da API do e-commerce."""
        # Implementação específica da API
        pass
    
    async def _find_existing_customer(self, email):
        """Encontrar cliente existente por email."""
        
        if not email:
            return None
        
        try:
            result = await self.dataverse_sdk.query("contacts", {
                "select": ["contactid", "emailaddress1"],
                "filter": f"emailaddress1 eq '{email}'",
                "top": 1
            })
            
            return result.value[0] if result.value else None
        
        except Exception:
            return None

# Uso do pipeline
async def run_ecommerce_sync():
    """Executar sincronização completa do e-commerce."""
    
    ecommerce_config = {
        'api_url': 'https://api.mystore.com',
        'api_key': 'your-api-key'
    }
    
    dataverse_credentials = {
        'dataverse_url': 'https://yourorg.crm.dynamics.com',
        'client_id': 'your-client-id',
        'client_secret': 'your-client-secret',
        'tenant_id': 'your-tenant-id'
    }
    
    async with EcommerceSyncPipeline(ecommerce_config, dataverse_credentials) as pipeline:
        
        # Sincronizar em ordem: produtos → clientes → pedidos
        await pipeline.sync_products()
        await pipeline.sync_customers()
        await pipeline.sync_orders()
        
        print("🎉 Sincronização e-commerce concluída!")

asyncio.run(run_ecommerce_sync())
```

## 📊 Cenário 3: Data Warehouse Integration

### Contexto
Integração bidirecional entre Dataverse e um Data Warehouse para análises avançadas e relatórios executivos.

### Implementação

```python
class DataWarehouseIntegration:
    """Integração entre Dataverse e Data Warehouse."""
    
    def __init__(self, dw_config, dataverse_credentials):
        self.dw_engine = create_engine(dw_config['connection_string'])
        self.dataverse_sdk = DataverseSDK(**dataverse_credentials)
    
    async def __aenter__(self):
        await self.dataverse_sdk.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.dataverse_sdk.__aexit__(exc_type, exc_val, exc_tb)
    
    async def extract_to_warehouse(self):
        """Extrair dados do Dataverse para o Data Warehouse."""
        
        # Definir entidades e campos para extração
        entities_config = {
            'accounts': {
                'select': [
                    'accountid', 'name', 'websiteurl', 'telephone1',
                    'industrycode', 'revenue', 'numberofemployees',
                    'createdon', 'modifiedon', 'statuscode'
                ],
                'table': 'dim_accounts'
            },
            'contacts': {
                'select': [
                    'contactid', 'fullname', 'emailaddress1', 'telephone1',
                    'jobtitle', 'parentcustomerid', 'createdon', 'modifiedon'
                ],
                'table': 'dim_contacts'
            },
            'opportunities': {
                'select': [
                    'opportunityid', 'name', 'estimatedvalue', 'actualvalue',
                    'closeprobability', 'statuscode', 'parentaccountid',
                    'parentcontactid', 'createdon', 'actualclosedate'
                ],
                'table': 'fact_opportunities'
            }
        }
        
        for entity_name, config in entities_config.items():
            print(f"🔄 Extraindo {entity_name}...")
            
            # Extrair dados do Dataverse
            data = await self.dataverse_sdk.query(entity_name, {
                "select": config['select']
            })
            
            if not data.value:
                print(f"ℹ️ Nenhum dado encontrado para {entity_name}")
                continue
            
            # Converter para DataFrame
            df = pd.DataFrame(data.value)
            
            # Adicionar metadados de ETL
            df['etl_load_date'] = pd.Timestamp.now()
            df['etl_source'] = 'dataverse'
            
            # Carregar no Data Warehouse
            table_name = config['table']
            
            # Truncate and load (full refresh)
            with self.dw_engine.begin() as conn:
                # Limpar tabela
                conn.execute(f"TRUNCATE TABLE {table_name}")
                
                # Inserir dados
                df.to_sql(
                    table_name,
                    conn,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
            
            print(f"✅ {len(df)} registros carregados em {table_name}")
    
    async def load_calculated_metrics(self):
        """Carregar métricas calculadas do DW para o Dataverse."""
        
        # Consultar métricas calculadas no DW
        metrics_query = """
        SELECT 
            account_id,
            total_opportunities,
            total_revenue,
            avg_deal_size,
            win_rate,
            last_activity_date,
            calculated_date
        FROM account_metrics 
        WHERE calculated_date = CURRENT_DATE
        """
        
        print("🔄 Extraindo métricas calculadas do Data Warehouse...")
        metrics_df = pd.read_sql(metrics_query, self.dw_engine)
        
        if metrics_df.empty:
            print("ℹ️ Nenhuma métrica calculada encontrada")
            return
        
        print(f"🔄 Atualizando {len(metrics_df)} contas com métricas...")
        
        # Preparar dados para atualização no Dataverse
        updates = []
        
        for _, row in metrics_df.iterrows():
            update_data = {
                'accountid': row['account_id'],
                'new_total_opportunities': int(row['total_opportunities']),
                'new_total_revenue': float(row['total_revenue']),
                'new_avg_deal_size': float(row['avg_deal_size']),
                'new_win_rate': float(row['win_rate']),
                'new_last_activity': row['last_activity_date'].isoformat() if pd.notna(row['last_activity_date']) else None,
                'new_metrics_updated_on': pd.Timestamp.now().isoformat()
            }
            
            updates.append(update_data)
        
        # Atualizar contas no Dataverse
        result = await self.dataverse_sdk.bulk_update("accounts", updates)
        
        print(f"✅ Atualizadas {result.successful} contas com métricas")
        
        if result.has_errors:
            print(f"⚠️ {result.failed} atualizações falharam")
    
    async def sync_custom_entities(self):
        """Sincronizar entidades customizadas bidirecionalmente."""
        
        # Extrair dados de entidade customizada do Dataverse
        print("🔄 Extraindo dados de campanhas de marketing...")
        
        campaigns = await self.dataverse_sdk.query("campaigns", {
            "select": [
                "campaignid", "name", "description", "budgetedcost",
                "actualcost", "expectedrevenue", "statuscode",
                "actualstart", "actualend", "createdon"
            ]
        })
        
        if campaigns.value:
            campaigns_df = pd.DataFrame(campaigns.value)
            
            # Calcular métricas de campanha no DW
            campaigns_df['roi'] = (
                (campaigns_df['expectedrevenue'] - campaigns_df['actualcost']) / 
                campaigns_df['actualcost'] * 100
            ).fillna(0)
            
            campaigns_df['cost_per_lead'] = (
                campaigns_df['actualcost'] / campaigns_df.get('leads_generated', 1)
            ).fillna(0)
            
            # Salvar no DW para análise
            campaigns_df.to_sql(
                'fact_campaigns',
                self.dw_engine,
                if_exists='replace',
                index=False
            )
            
            print(f"✅ {len(campaigns_df)} campanhas sincronizadas no DW")

# Uso da integração
async def run_dw_integration():
    """Executar integração completa com Data Warehouse."""
    
    dw_config = {
        'connection_string': 'postgresql://user:password@dw-server:5432/analytics_db'
    }
    
    dataverse_credentials = {
        'dataverse_url': 'https://yourorg.crm.dynamics.com',
        'client_id': 'your-client-id',
        'client_secret': 'your-client-secret',
        'tenant_id': 'your-tenant-id'
    }
    
    async with DataWarehouseIntegration(dw_config, dataverse_credentials) as integration:
        
        # 1. Extrair dados para o DW
        await integration.extract_to_warehouse()
        
        # 2. Carregar métricas calculadas
        await integration.load_calculated_metrics()
        
        # 3. Sincronizar entidades customizadas
        await integration.sync_custom_entities()
        
        print("🎉 Integração com Data Warehouse concluída!")

asyncio.run(run_dw_integration())
```

## 🔄 Cenário 4: Real-time Event Processing

### Contexto
Processamento em tempo real de eventos do Dataverse usando webhooks e streaming.

### Implementação

```python
from flask import Flask, request, jsonify
import asyncio
import threading
from queue import Queue

class RealTimeEventProcessor:
    """Processador de eventos em tempo real do Dataverse."""
    
    def __init__(self, dataverse_credentials):
        self.dataverse_sdk = DataverseSDK(**dataverse_credentials)
        self.event_queue = Queue()
        self.app = Flask(__name__)
        self.setup_webhook_endpoints()
    
    def setup_webhook_endpoints(self):
        """Configurar endpoints para webhooks."""
        
        @self.app.route('/webhook/dataverse', methods=['POST'])
        def handle_dataverse_webhook():
            """Receber eventos do Dataverse via webhook."""
            
            try:
                event_data = request.get_json()
                
                # Validar evento
                if not self._validate_webhook_event(event_data):
                    return jsonify({'error': 'Invalid event'}), 400
                
                # Adicionar à fila de processamento
                self.event_queue.put(event_data)
                
                return jsonify({'status': 'received'}), 200
            
            except Exception as e:
                print(f"❌ Erro no webhook: {str(e)}")
                return jsonify({'error': 'Internal error'}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({'status': 'healthy'}), 200
    
    def _validate_webhook_event(self, event_data):
        """Validar evento do webhook."""
        
        required_fields = ['EntityName', 'EventName', 'PrimaryEntityId']
        return all(field in event_data for field in required_fields)
    
    async def process_events(self):
        """Processar eventos da fila."""
        
        await self.dataverse_sdk.__aenter__()
        
        try:
            while True:
                if not self.event_queue.empty():
                    event = self.event_queue.get()
                    await self._handle_event(event)
                
                await asyncio.sleep(0.1)  # Pequena pausa
        
        finally:
            await self.dataverse_sdk.__aexit__(None, None, None)
    
    async def _handle_event(self, event):
        """Processar evento individual."""
        
        entity_name = event['EntityName']
        event_name = event['EventName']
        entity_id = event['PrimaryEntityId']
        
        print(f"🔄 Processando evento: {event_name} em {entity_name} ({entity_id})")
        
        try:
            if entity_name == 'account' and event_name == 'Create':
                await self._handle_new_account(entity_id)
            
            elif entity_name == 'opportunity' and event_name == 'Update':
                await self._handle_opportunity_update(entity_id)
            
            elif entity_name == 'contact' and event_name == 'Create':
                await self._handle_new_contact(entity_id)
            
            else:
                print(f"ℹ️ Evento não tratado: {event_name} em {entity_name}")
        
        except Exception as e:
            print(f"❌ Erro processando evento: {str(e)}")
    
    async def _handle_new_account(self, account_id):
        """Processar nova conta criada."""
        
        # Buscar dados da conta
        account = await self.dataverse_sdk.read("accounts", account_id, 
            select=["name", "websiteurl", "industrycode"]
        )
        
        # Criar tarefas automáticas
        tasks = [
            {
                "subject": f"Boas-vindas - {account['name']}",
                "description": "Enviar kit de boas-vindas para nova conta",
                f"regardingobjectid@odata.bind": f"accounts({account_id})",
                "prioritycode": 2,  # Alta prioridade
                "scheduledstart": (pd.Timestamp.now() + pd.Timedelta(hours=1)).isoformat()
            },
            {
                "subject": f"Pesquisa de mercado - {account['name']}",
                "description": "Realizar pesquisa sobre a empresa e concorrentes",
                f"regardingobjectid@odata.bind": f"accounts({account_id})",
                "prioritycode": 1,  # Normal
                "scheduledstart": (pd.Timestamp.now() + pd.Timedelta(days=1)).isoformat()
            }
        ]
        
        # Criar tarefas
        result = await self.dataverse_sdk.bulk_create("tasks", tasks)
        print(f"✅ Criadas {result.successful} tarefas para nova conta")
        
        # Enviar notificação (integração com sistema externo)
        await self._send_notification(
            f"Nova conta criada: {account['name']}",
            f"Uma nova conta foi criada no sistema: {account['name']}"
        )
    
    async def _handle_opportunity_update(self, opportunity_id):
        """Processar atualização de oportunidade."""
        
        # Buscar dados da oportunidade
        opportunity = await self.dataverse_sdk.read("opportunities", opportunity_id,
            select=["name", "statuscode", "estimatedvalue", "closeprobability"]
        )
        
        status_code = opportunity.get('statuscode')
        
        # Oportunidade ganha
        if status_code == 3:  # Won
            await self._handle_won_opportunity(opportunity_id, opportunity)
        
        # Oportunidade perdida
        elif status_code == 4:  # Lost
            await self._handle_lost_opportunity(opportunity_id, opportunity)
        
        # Oportunidade com alta probabilidade
        elif opportunity.get('closeprobability', 0) >= 80:
            await self._handle_high_probability_opportunity(opportunity_id, opportunity)
    
    async def _handle_won_opportunity(self, opportunity_id, opportunity):
        """Processar oportunidade ganha."""
        
        print(f"🎉 Oportunidade ganha: {opportunity['name']}")
        
        # Criar tarefa de follow-up
        followup_task = {
            "subject": f"Follow-up pós-venda - {opportunity['name']}",
            "description": "Acompanhar satisfação do cliente e identificar oportunidades de upsell",
            f"regardingobjectid@odata.bind": f"opportunities({opportunity_id})",
            "prioritycode": 2,
            "scheduledstart": (pd.Timestamp.now() + pd.Timedelta(days=7)).isoformat()
        }
        
        await self.dataverse_sdk.create("tasks", followup_task)
        
        # Atualizar métricas em tempo real
        await self._update_sales_metrics(opportunity)
    
    async def _handle_lost_opportunity(self, opportunity_id, opportunity):
        """Processar oportunidade perdida."""
        
        print(f"😞 Oportunidade perdida: {opportunity['name']}")
        
        # Criar tarefa de análise
        analysis_task = {
            "subject": f"Análise de perda - {opportunity['name']}",
            "description": "Analisar motivos da perda e identificar melhorias no processo",
            f"regardingobjectid@odata.bind": f"opportunities({opportunity_id})",
            "prioritycode": 1,
            "scheduledstart": (pd.Timestamp.now() + pd.Timedelta(days=1)).isoformat()
        }
        
        await self.dataverse_sdk.create("tasks", analysis_task)
    
    async def _handle_new_contact(self, contact_id):
        """Processar novo contato criado."""
        
        # Buscar dados do contato
        contact = await self.dataverse_sdk.read("contacts", contact_id,
            select=["fullname", "emailaddress1", "parentcustomerid"]
        )
        
        # Criar tarefa de qualificação
        qualification_task = {
            "subject": f"Qualificar lead - {contact['fullname']}",
            "description": "Qualificar novo lead e determinar próximos passos",
            f"regardingobjectid@odata.bind": f"contacts({contact_id})",
            "prioritycode": 2,
            "scheduledstart": (pd.Timestamp.now() + pd.Timedelta(hours=2)).isoformat()
        }
        
        await self.dataverse_sdk.create("tasks", qualification_task)
        
        print(f"✅ Tarefa de qualificação criada para {contact['fullname']}")
    
    async def _send_notification(self, title, message):
        """Enviar notificação para sistema externo."""
        
        # Implementar integração com Slack, Teams, email, etc.
        print(f"📧 Notificação: {title} - {message}")
    
    async def _update_sales_metrics(self, opportunity):
        """Atualizar métricas de vendas em tempo real."""
        
        # Implementar atualização de dashboard em tempo real
        print(f"📊 Atualizando métricas com venda de ${opportunity.get('estimatedvalue', 0)}")
    
    def run_webhook_server(self, host='0.0.0.0', port=5000):
        """Executar servidor de webhooks."""
        
        self.app.run(host=host, port=port, threaded=True)
    
    def start_event_processor(self):
        """Iniciar processador de eventos em thread separada."""
        
        def run_processor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.process_events())
        
        processor_thread = threading.Thread(target=run_processor)
        processor_thread.daemon = True
        processor_thread.start()

# Uso do processador
def run_realtime_processor():
    """Executar processador de eventos em tempo real."""
    
    dataverse_credentials = {
        'dataverse_url': 'https://yourorg.crm.dynamics.com',
        'client_id': 'your-client-id',
        'client_secret': 'your-client-secret',
        'tenant_id': 'your-tenant-id'
    }
    
    processor = RealTimeEventProcessor(dataverse_credentials)
    
    # Iniciar processador de eventos
    processor.start_event_processor()
    
    # Executar servidor de webhooks
    print("🚀 Iniciando servidor de webhooks...")
    processor.run_webhook_server()

# Executar processador
if __name__ == "__main__":
    run_realtime_processor()
```

## 📈 Monitoramento e Métricas

### Dashboard de ETL

```python
class ETLDashboard:
    """Dashboard para monitoramento de pipelines ETL."""
    
    def __init__(self, dataverse_credentials):
        self.dataverse_sdk = DataverseSDK(**dataverse_credentials)
    
    async def get_pipeline_metrics(self):
        """Obter métricas dos pipelines."""
        
        # Consultar logs de ETL (entidade customizada)
        etl_logs = await self.dataverse_sdk.query("new_etl_logs", {
            "select": [
                "new_pipeline_name", "new_status", "new_records_processed",
                "new_execution_time", "new_error_count", "createdon"
            ],
            "filter": "createdon ge 2024-01-01T00:00:00Z",
            "order_by": ["createdon desc"]
        })
        
        # Calcular métricas
        logs_df = pd.DataFrame(etl_logs.value)
        
        metrics = {
            'total_executions': len(logs_df),
            'success_rate': (logs_df['new_status'] == 'Success').mean() * 100,
            'avg_execution_time': logs_df['new_execution_time'].mean(),
            'total_records_processed': logs_df['new_records_processed'].sum(),
            'error_rate': (logs_df['new_error_count'] > 0).mean() * 100
        }
        
        return metrics
    
    async def generate_report(self):
        """Gerar relatório de ETL."""
        
        metrics = await self.get_pipeline_metrics()
        
        report = f"""
        📊 Relatório de ETL - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
        
        ✅ Execuções Totais: {metrics['total_executions']}
        📈 Taxa de Sucesso: {metrics['success_rate']:.1f}%
        ⏱️ Tempo Médio: {metrics['avg_execution_time']:.1f}s
        📋 Registros Processados: {metrics['total_records_processed']:,}
        ⚠️ Taxa de Erro: {metrics['error_rate']:.1f}%
        """
        
        return report
```

## 🎯 Conclusão

Estes cenários reais demonstram a versatilidade e poder do **jaf-dataverse-2025** SDK para:

- **Migrações complexas** com preservação de relacionamentos
- **Sincronizações bidirecionais** entre sistemas
- **Integração com Data Warehouses** para analytics
- **Processamento em tempo real** de eventos
- **Monitoramento e observabilidade** de pipelines

### Próximos Passos

1. **Adapte os exemplos** para seu caso específico
2. **Implemente monitoramento** robusto
3. **Configure alertas** para falhas
4. **Documente** seus pipelines customizados
5. **Teste** em ambiente de desenvolvimento primeiro

---

**💡 Dica**: Sempre implemente logging detalhado e tratamento de erros robusto em pipelines de produção!

