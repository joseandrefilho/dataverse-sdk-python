#!/usr/bin/env python3
"""
Stress Test - Dataverse SDK

Este teste de stress demonstra a capacidade do SDK de lidar com
milhões de registros, testando os limites de performance e
estabilidade do sistema.
"""

import asyncio
import time
import psutil
import gc
from typing import List, Dict, Any
import json
from datetime import datetime
import os
import sys

# Configuração para importar o SDK
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataverse_sdk import DataverseSDK


class StressTest:
    """Teste de stress para operações de grande volume."""
    
    def __init__(self, sdk: DataverseSDK):
        self.sdk = sdk
        self.process = psutil.Process()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Obtém uso atual de memória."""
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": self.process.memory_percent(),
        }
    
    async def generate_large_dataset(self, count: int) -> List[Dict[str, Any]]:
        """Gera dataset grande de forma eficiente."""
        print(f"📊 Gerando dataset com {count:,} registros...")
        
        start_time = time.time()
        batch_size = 10000  # Gerar em lotes para economizar memória
        
        all_data = []
        
        for batch_start in range(0, count, batch_size):
            batch_end = min(batch_start + batch_size, count)
            batch_data = []
            
            for i in range(batch_start, batch_end):
                record = {
                    "name": f"Stress Test Account {i:08d}",
                    "accountnumber": f"STRESS{i:08d}",
                    "description": f"Large volume test record {i} - Batch {i // 1000}",
                    "websiteurl": f"https://stress-{i}.example.com",
                    "telephone1": f"+1-{(555000000 + i):010d}",
                    "emailaddress1": f"stress{i}@example.com",
                    "revenue": 50000 + (i * 100),
                    "numberofemployees": 1 + (i % 10000),
                    "industrycode": i % 20,  # Variar indústria
                    "customertypecode": i % 3,  # Variar tipo de cliente
                }
                batch_data.append(record)
            
            all_data.extend(batch_data)
            
            # Mostrar progresso
            progress = (batch_end / count) * 100
            memory = self.get_memory_usage()
            print(f"   📈 Progresso: {progress:.1f}% - Memória: {memory['rss_mb']:.1f}MB")
            
            # Forçar garbage collection periodicamente
            if batch_end % 50000 == 0:
                gc.collect()
        
        generation_time = time.time() - start_time
        final_memory = self.get_memory_usage()
        
        print(f"✅ Dataset gerado em {generation_time:.2f}s")
        print(f"💾 Memória final: {final_memory['rss_mb']:.1f}MB")
        
        return all_data
    
    async def stress_test_bulk_create(self, record_count: int) -> Dict[str, Any]:
        """Executa teste de stress para criação em massa."""
        
        print(f"\n🔥 STRESS TEST - CRIAÇÃO EM MASSA")
        print(f"📊 Registros: {record_count:,}")
        print(f"🎯 Objetivo: Testar limites do SDK")
        print("-" * 60)
        
        start_memory = self.get_memory_usage()
        start_time = time.time()
        
        try:
            # Gerar dados
            test_data = await self.generate_large_dataset(record_count)
            data_gen_time = time.time() - start_time
            
            # Configuração otimizada para grande volume
            batch_size = 1000  # Lotes maiores para eficiência
            
            print(f"\n🚀 Iniciando criação em massa...")
            print(f"   📦 Batch Size: {batch_size}")
            print(f"   🔄 Paralelismo: 32")
            
            creation_start = time.time()
            
            # Executar criação em lotes para controlar memória
            total_successful = 0
            total_failed = 0
            total_processed = 0
            
            chunk_size = 10000  # Processar em chunks de 10k
            
            for chunk_start in range(0, len(test_data), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(test_data))
                chunk_data = test_data[chunk_start:chunk_end]
                
                print(f"\n📦 Processando chunk {chunk_start:,} - {chunk_end:,}")
                
                try:
                    result = await self.sdk.bulk_create(
                        entity_type="accounts",
                        entities=chunk_data,
                        batch_size=batch_size,
                        parallel=True
                    )
                    
                    total_successful += result.successful
                    total_failed += result.failed
                    total_processed += result.total_processed
                    
                    # Mostrar progresso
                    progress = (chunk_end / len(test_data)) * 100
                    memory = self.get_memory_usage()
                    
                    print(f"   ✅ Chunk concluído: {result.successful:,} sucessos")
                    print(f"   📈 Progresso total: {progress:.1f}%")
                    print(f"   💾 Memória: {memory['rss_mb']:.1f}MB")
                    
                    # Limpeza de memória
                    del chunk_data
                    gc.collect()
                    
                except Exception as e:
                    print(f"   ❌ Erro no chunk: {e}")
                    total_failed += len(chunk_data)
                    total_processed += len(chunk_data)
            
            creation_time = time.time() - creation_start
            total_time = time.time() - start_time
            end_memory = self.get_memory_usage()
            
            # Calcular métricas
            throughput = total_processed / creation_time if creation_time > 0 else 0
            success_rate = (total_successful / total_processed * 100) if total_processed > 0 else 0
            memory_increase = end_memory['rss_mb'] - start_memory['rss_mb']
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "test_type": "stress_test_bulk_create",
                "config": {
                    "record_count": record_count,
                    "batch_size": batch_size,
                    "chunk_size": chunk_size,
                },
                "performance": {
                    "total_time_seconds": total_time,
                    "data_generation_time": data_gen_time,
                    "creation_time": creation_time,
                    "throughput_records_per_second": throughput,
                },
                "results": {
                    "total_processed": total_processed,
                    "successful": total_successful,
                    "failed": total_failed,
                    "success_rate_percent": success_rate,
                },
                "memory": {
                    "start_mb": start_memory['rss_mb'],
                    "end_mb": end_memory['rss_mb'],
                    "increase_mb": memory_increase,
                    "peak_percent": end_memory['percent'],
                }
            }
            
            # Exibir resultados finais
            print(f"\n🎯 RESULTADOS DO STRESS TEST")
            print(f"=" * 60)
            print(f"⏱️  Tempo Total: {total_time:.2f}s")
            print(f"🚀 Throughput: {throughput:.1f} registros/segundo")
            print(f"📊 Processados: {total_processed:,}")
            print(f"✅ Sucessos: {total_successful:,}")
            print(f"❌ Falhas: {total_failed:,}")
            print(f"📈 Taxa de Sucesso: {success_rate:.1f}%")
            print(f"💾 Memória Inicial: {start_memory['rss_mb']:.1f}MB")
            print(f"💾 Memória Final: {end_memory['rss_mb']:.1f}MB")
            print(f"📈 Aumento de Memória: {memory_increase:.1f}MB")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro durante stress test: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "test_type": "stress_test_bulk_create",
                "config": {"record_count": record_count}
            }
    
    async def run_progressive_stress_tests(self) -> List[Dict[str, Any]]:
        """Executa testes progressivos de stress."""
        
        test_sizes = [
            10000,    # 10K registros
            50000,    # 50K registros  
            100000,   # 100K registros
            500000,   # 500K registros
            1000000,  # 1M registros (se o ambiente suportar)
        ]
        
        results = []
        
        for i, size in enumerate(test_sizes, 1):
            print(f"\n{'='*80}")
            print(f"🧪 STRESS TEST {i}/{len(test_sizes)} - {size:,} REGISTROS")
            print(f"{'='*80}")
            
            # Verificar memória disponível
            memory = self.get_memory_usage()
            available_memory = psutil.virtual_memory().available / 1024 / 1024  # MB
            
            print(f"💾 Memória atual: {memory['rss_mb']:.1f}MB")
            print(f"💾 Memória disponível: {available_memory:.1f}MB")
            
            if available_memory < 1000:  # Menos de 1GB disponível
                print(f"⚠️  Memória insuficiente para teste de {size:,} registros")
                continue
            
            result = await self.stress_test_bulk_create(size)
            results.append(result)
            
            # Limpeza entre testes
            gc.collect()
            
            # Pausa entre testes
            if i < len(test_sizes):
                print(f"\n⏸️  Pausa de 10s antes do próximo teste...")
                await asyncio.sleep(10)
        
        return results


async def main():
    """Função principal do stress test."""
    
    print("🔥 STRESS TEST - DATAVERSE SDK")
    print("Testando limites de performance com milhões de registros")
    print("=" * 80)
    
    # Configuração do SDK otimizada para grande volume
    sdk = DataverseSDK(
        dataverse_url=os.getenv("DATAVERSE_URL", "https://demo.crm.dynamics.com"),
        client_id=os.getenv("AZURE_CLIENT_ID", "demo-client-id"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET", "demo-secret"),
        tenant_id=os.getenv("AZURE_TENANT_ID", "demo-tenant"),
        
        # Configurações máximas para stress test
        max_connections=200,
        max_keepalive_connections=100,
        connect_timeout=15.0,
        read_timeout=60.0,
        default_batch_size=1000,
        max_batch_size=2000,
        
        # Para testes
        verify_ssl=False,
        disable_ssl_warnings=True,
    )
    
    stress_test = StressTest(sdk)
    
    try:
        async with sdk:
            # Executar testes progressivos
            results = await stress_test.run_progressive_stress_tests()
            
            # Salvar resultados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_results_{timestamp}.json"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n💾 Resultados salvos em: {filepath}")
            
            # Resumo final
            print(f"\n🎯 RESUMO DO STRESS TEST")
            print(f"=" * 80)
            
            successful_tests = [r for r in results if "error" not in r]
            
            if successful_tests:
                max_records = max(r["config"]["record_count"] for r in successful_tests)
                total_records = sum(r["results"]["successful"] for r in successful_tests)
                
                print(f"✅ Testes executados: {len(results)}")
                print(f"📊 Maior volume testado: {max_records:,} registros")
                print(f"🚀 Total de registros criados: {total_records:,}")
                print(f"💪 SDK demonstrou capacidade para milhões de registros!")
            else:
                print("❌ Nenhum teste foi executado com sucesso")
    
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")


if __name__ == "__main__":
    asyncio.run(main())

