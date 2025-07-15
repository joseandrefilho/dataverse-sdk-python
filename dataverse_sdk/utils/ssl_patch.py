"""
Módulo para aplicar patches SSL agressivos em todas as bibliotecas HTTP.
"""

import os
import ssl
import warnings
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


def apply_aggressive_ssl_patches(verify_ssl: bool = True, disable_warnings: bool = False) -> None:
    """
    Aplica patches SSL agressivos em todas as bibliotecas HTTP conhecidas.
    
    Args:
        verify_ssl: Se False, desabilita verificação SSL completamente
        disable_warnings: Se True, suprime todos os warnings SSL
    """
    if verify_ssl:
        return  # Não fazer nada se SSL deve ser verificado
    
    logger.info("Applying aggressive SSL patches", verify_ssl=verify_ssl, disable_warnings=disable_warnings)
    
    # Suprimir warnings
    if disable_warnings:
        warnings.filterwarnings('ignore')
        try:
            import urllib3
            urllib3.disable_warnings()
        except ImportError:
            pass
    
    # Criar contexto SSL completamente inseguro
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    try:
        ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
    except Exception:
        pass
    
    # Patch 1: urllib3
    try:
        import urllib3.util.ssl_
        original_create_urllib3_context = urllib3.util.ssl_.create_urllib3_context
        
        def patched_create_urllib3_context(*args, **kwargs):
            return ssl_context
        
        urllib3.util.ssl_.create_urllib3_context = patched_create_urllib3_context
        logger.debug("urllib3 SSL context patched")
    except Exception as e:
        logger.warning("Failed to patch urllib3", error=str(e))
    
    # Patch 2: ssl module
    try:
        original_create_default_context = ssl.create_default_context
        
        def patched_create_default_context(*args, **kwargs):
            return ssl_context
        
        ssl.create_default_context = patched_create_default_context
        logger.debug("ssl module patched")
    except Exception as e:
        logger.warning("Failed to patch ssl module", error=str(e))
    
    # Patch 3: httpx
    try:
        import httpx
        import httpx._config
        httpx._config.DEFAULT_SSL_CONTEXT = ssl_context
        logger.debug("httpx SSL context patched")
    except Exception as e:
        logger.debug("httpx not available or patch failed", error=str(e))
    
    # Patch 4: requests
    try:
        import requests
        import requests.adapters
        original_init_poolmanager = requests.adapters.HTTPAdapter.init_poolmanager
        
        def patched_init_poolmanager(self, *args, **kwargs):
            kwargs['ssl_context'] = ssl_context
            return original_init_poolmanager(self, *args, **kwargs)
        
        requests.adapters.HTTPAdapter.init_poolmanager = patched_init_poolmanager
        logger.debug("requests SSL context patched")
    except Exception as e:
        logger.debug("requests not available or patch failed", error=str(e))
    
    # Patch 5: aiohttp
    try:
        import aiohttp
        import aiohttp.connector
        original_init = aiohttp.connector.TCPConnector.__init__
        
        def patched_init(self, *args, **kwargs):
            kwargs['ssl'] = ssl_context
            return original_init(self, *args, **kwargs)
        
        aiohttp.connector.TCPConnector.__init__ = patched_init
        logger.debug("aiohttp SSL context patched")
    except Exception as e:
        logger.debug("aiohttp not available or patch failed", error=str(e))
    
    # Configurar variáveis de ambiente
    ssl_env_vars = {
        'PYTHONHTTPSVERIFY': '0',
        'CURL_CA_BUNDLE': '',
        'REQUESTS_CA_BUNDLE': '',
        'SSL_VERIFY': 'false',
        'NODE_TLS_REJECT_UNAUTHORIZED': '0',
        'PYTHONHTTPSVERIFY': '0',
    }
    
    for key, value in ssl_env_vars.items():
        os.environ[key] = value
    
    logger.info("Aggressive SSL patches applied successfully")


def apply_proxy_configuration(
    proxy_url: Optional[str] = None,
    proxy_username: Optional[str] = None,
    proxy_password: Optional[str] = None
) -> None:
    """
    Aplica configuração de proxy via variáveis de ambiente.
    
    Args:
        proxy_url: URL do proxy
        proxy_username: Username para autenticação do proxy
        proxy_password: Password para autenticação do proxy
    """
    if not proxy_url:
        return
    
    logger.info("Applying proxy configuration", proxy_url=proxy_url)
    
    # Adicionar autenticação se fornecida
    if proxy_username and proxy_password:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(proxy_url)
        proxy_url = urlunparse((
            parsed.scheme,
            f"{proxy_username}:{proxy_password}@{parsed.netloc}",
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
    
    # Configurar todas as variáveis de proxy possíveis
    proxy_env_vars = {
        'HTTP_PROXY': proxy_url,
        'HTTPS_PROXY': proxy_url,
        'http_proxy': proxy_url,
        'https_proxy': proxy_url,
        'ALL_PROXY': proxy_url,
        'all_proxy': proxy_url,
    }
    
    for key, value in proxy_env_vars.items():
        os.environ[key] = value
    
    logger.info("Proxy configuration applied successfully")

