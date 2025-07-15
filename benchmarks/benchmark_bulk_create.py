#!/usr/bin/env python3
"""
Benchmark de Criação em Massa - Dataverse SDK

Este benchmark testa a performance de criação de registros em massa,
demonstrando a capacidade do SDK de lidar com milhares de registros
de forma eficiente.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import json
from datetime import datetime

# Configuração para importar o SDK
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataverse_sdk import DataverseSDK
from dataverse_sdk.models import BulkOperationResult


class BulkCreateBenchmark:
    """Benchmark para operações de criação em massa."""
    
    def __init__(self, sdk: DataverseSDK):
        self.sdk = sdk
        self.results = []
        
    async def generate_test_data(self, count: int) -> List[Dict[str, Any]]:
        """Gera dados de teste para criação."""
        test_data = []
        
        for i in range(count):
            account = {
                "name": f"Benchmark Account {i:06d}",
                "accountnumber": f"BENCH{i:06d}",
                "description": f"Account created for benchmark testing - Batch {i // 100}",
                "websiteurl": f"https://benchmark-{i}.example.com",
                "telephone1": f"+1-555-{i:04d}",
                "emailaddress1": f"benchmark{i}@example.com",
                "revenue": 100000 + (i * 1000),  # Revenue crescente
                "numberofemployees": 10 + (i % 1000),  # Funcionários variáveis
            }
            test_data.append(account)
            
        return test_data
    
    async def run_benchmark(
        self, 
        record_count: int, 
        batch_size: int = 500, 
        parallel_batches: int = 32
    ) -> Dict[str, Any]:
        """Executa benchmark de criação em massa."""
        
        print(f"🚀 Iniciando benchmark de criação em massa")
        print(f"   📊 Registros: {record_count:,}")
        print(f"   📦 Batch Size: {batch_size}")
        print(f"   🔄 Paralelismo: {parallel_batches}")
        print("-" * 60)
        
        # Gerar dados de teste
        start_time = time.time()
        test_data = await self.generate_test_data(record_count)
        data_gen_time = time.time() - start_time
        
        print(f"✅ Dados gerados em {data_gen_time:.2f}s")
        
        # Executar criação em massa
        start_time = time.time()
        
        try:
            result = await self.sdk.bulk_create(
                entity_type="accounts",
                entities=test_data,
                batch_size=batch_size,
                parallel=True
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calcular métricas
            throughput = record_count / total_time if total_time > 0 else 0
            avg_time_per_record = total_time / record_count if record_count > 0 else 0
            
            benchmark_result = {
                "timestamp": datetime.now().isoformat(),
                "test_config": {
                    "record_count": record_count,
                    "batch_size": batch_size,
                    "parallel_batches": parallel_batches,
                },
                "performance": {
                    "total_time_seconds": total_time,
                    "data_generation_time": data_gen_time,
                    "throughput_records_per_second": throughput,
                    "avg_time_per_record_ms": avg_time_per_record * 1000,
                },
                "results": {
                    "total_processed": result.total_processed,
                    "successful": result.successful,
                    "failed": result.failed,
                    "success_rate_percent": result.success_rate,
                },
                "errors": result.errors[:5] if result.has_errors else []
            }
            
            # Exibir resultados
            print(f"\n📈 RESULTADOS DO BENCHMARK")
            print(f"⏱️  Tempo Total: {total_time:.2f}s")
            print(f"🚀 Throughput: {throughput:.1f} registros/segundo")
            print(f"📊 Processados: {result.total_processed:,}")
            print(f"✅ Sucessos: {result.successful:,}")
            print(f"❌ Falhas: {result.failed:,}")
            print(f"📈 Taxa de Sucesso: {result.success_rate:.1f}%")
            
            if result.has_errors:
                print(f"\n⚠️  Primeiros 5 erros:")
                for i, error in enumerate(result.errors[:5], 1):
                    print(f"   {i}. {error}")
            
            return benchmark_result
            
        except Exception as e:
            print(f"❌ Erro durante benchmark: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "test_config": {
                    "record_count": record_count,
                    "batch_size": batch_size,
                    "parallel_batches": parallel_batches,
                }
            }
    
    async def run_multiple_tests(self) -> List[Dict[str, Any]]:
        """Executa múltiplos testes com diferentes configurações."""
        
        test_configs = [
            {"count": 100, "batch_size": 50, "parallel": 8},
            {"count": 500, "batch_size": 100, "parallel": 16},
            {"count": 1000, "batch_size": 200, "parallel": 32},
            {"count": 2000, "batch_size": 500, "parallel": 32},
            {"count": 5000, "batch_size": 500, "parallel": 32},
        ]
        
        results = []
        
        for i, config in enumerate(test_configs, 1):
            print(f"\n{'='*60}")
            print(f"🧪 TESTE {i}/{len(test_configs)}")
            print(f"{'='*60}")
            
            result = await self.run_benchmark(
                record_count=config["count"],
                batch_size=config["batch_size"],
                parallel_batches=config["parallel"]
            )
            
            results.append(result)
            
            # Pausa entre testes
            if i < len(test_configs):
                print(f"\n⏸️  Pausa de 5s antes do próximo teste...")
                await asyncio.sleep(5)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], filename: str = None):
        """Salva resultados em arquivo JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_bulk_create_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Resultados salvos em: {filepath}")


async def main():
    """Função principal do benchmark."""
    
    print("⚡ BENCHMARK DE CRIAÇÃO EM MASSA - DATAVERSE SDK")
    print("=" * 60)
    
    # Configuração do SDK (usar variáveis de ambiente ou config)
    sdk = DataverseSDK(
        dataverse_url=os.getenv("DATAVERSE_URL", "https://demo.crm.dynamics.com"),
        client_id=os.getenv("AZURE_CLIENT_ID", "demo-client-id"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET", "demo-secret"),
        tenant_id=os.getenv("AZURE_TENANT_ID", "demo-tenant"),
        
        # Configurações otimizadas para performance
        max_connections=100,
        max_keepalive_connections=50,
        connect_timeout=10.0,
        read_timeout=30.0,
        default_batch_size=500,
        max_batch_size=1000,
        
        # Para testes, desabilitar SSL se necessário
        verify_ssl=False,
        disable_ssl_warnings=True,
    )
    
    benchmark = BulkCreateBenchmark(sdk)
    
    try:
        async with sdk:
            # Executar testes múltiplos
            results = await benchmark.run_multiple_tests()
            
            # Salvar resultados
            benchmark.save_results(results)
            
            # Resumo final
            print(f"\n🎯 RESUMO FINAL")
            print(f"=" * 60)
            
            successful_tests = [r for r in results if "error" not in r]
            
            if successful_tests:
                throughputs = [r["performance"]["throughput_records_per_second"] 
                             for r in successful_tests]
                
                print(f"✅ Testes executados: {len(results)}")
                print(f"🚀 Throughput médio: {statistics.mean(throughputs):.1f} registros/s")
                print(f"📊 Throughput máximo: {max(throughputs):.1f} registros/s")
                print(f"📈 Throughput mínimo: {min(throughputs):.1f} registros/s")
            else:
                print("❌ Nenhum teste foi executado com sucesso")
    
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")


if __name__ == "__main__":
    asyncio.run(main())

