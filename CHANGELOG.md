# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-07-15

### Fixed
- **SSL Global**: Configuração SSL mais robusta com múltiplas variáveis de ambiente
- **Monkey Patching**: Melhorado monkey patching do urllib3 com tratamento de erros
- **Configuração Abrangente**: SSL e proxy aplicados globalmente para todos os componentes
- **Variáveis de Ambiente**: Adicionadas PYTHONHTTPSVERIFY, CURL_CA_BUNDLE, REQUESTS_CA_BUNDLE

### Added
- **Método _configure_global_ssl_proxy**: Configuração centralizada de SSL/proxy
- **Logs Detalhados**: Melhor logging para debug de configurações SSL/proxy
- **Tratamento de Erros**: Try/catch para monkey patching com fallback

## [1.1.1] - 2025-07-15

### Fixed
- **SSL na Autenticação**: Corrigido erro `CERTIFICATE_VERIFY_FAILED` durante autenticação
- **MSAL Configuração**: Implementada configuração SSL/proxy correta para MSAL
- **Monkey Patching**: Adicionado monkey patching do urllib3 para SSL desabilitado
- **Variáveis de Ambiente**: Configuração de proxy via variáveis de ambiente para MSAL

### Added
- **Autenticação Corporativa**: Suporte completo a ambientes corporativos com SSL/proxy
- **Logs Detalhados**: Melhor logging para debug de configurações SSL/proxy

## [1.1.0] - 2025-07-15

### Fixed
- Corrigido erro `TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'`
- Atualizada implementação de proxy para usar sintaxe correta do httpx (`proxy` ao invés de `proxies`)
- Corrigida referência restante à variável `proxies` no log de inicialização

### Added
- Pasta `benchmarks/` com testes de performance para milhões de registros
- Estrutura de projeto reorganizada e profissional
- Documentação reorganizada em categorias lógicas

### Changed
- Estrutura do projeto completamente reorganizada
- Documentação movida para pastas apropriadas
- README atualizado com nova estrutura e benchmarks

## [1.0.9] - 2025-07-15

### Added
- Estrutura de projeto reorganizada
- Pasta `benchmarks/` com testes de performance
- Documentação reorganizada em categorias

### Changed
- Arquivos de documentação movidos para pastas apropriadas
- README atualizado com nova estrutura

## [1.0.8] - 2025-07-15

### Fixed
- Corrigido warning do Pydantic sobre `allow_population_by_field_name`
- Atualizado configurações para Pydantic v2 (`populate_by_name`)
- Eliminado warnings chatos durante uso do SDK

### Changed
- Todas as classes de modelo agora usam `populate_by_name = True`
- Console mais limpo sem warnings desnecessários

## [1.0.7] - 2025-07-15

### Added
- Comando `--version` no CLI para verificar versão instalada
- Comando `version` como subcomando alternativo
- Modo verbose para `--version` com informações do sistema
- Detecção inteligente de versão (pacote instalado vs desenvolvimento)

### Changed
- CLI agora suporta execução sem subcomando para mostrar versão
- Melhorada experiência do desenvolvedor com informações de versão

## [1.0.6] - 2025-07-15

### Added
- Suporte completo para ambientes corporativos
- Configurações de proxy com autenticação
- Configurações SSL customizáveis
- Opção para desabilitar verificação SSL
- Supressão de warnings SSL
- Suporte a certificados CA customizados
- Configuração via variáveis de ambiente

### Changed
- Cliente HTTP agora suporta configurações de proxy
- Melhorada compatibilidade com firewalls corporativos

### Fixed
- Problemas de SSL em ambientes corporativos
- Erros de proxy com autenticação

## [1.0.5] - 2025-07-15

### Fixed
- Correções nas operações bulk nativas
- Melhorado sistema de fallback para operações individuais
- Tratamento de erros mais robusto

## [1.0.4] - 2025-07-15

### Added
- Implementação inicial das operações bulk
- Sistema de fallback para operações individuais
- Melhorado tratamento de erros

## [1.0.3] - 2025-07-15

### Added
- Suporte completo a FetchXML
- Operações CRUD completas
- Sistema de autenticação robusto
- CLI completa com todos os comandos

## [1.0.0] - 2025-07-14

### Added
- Lançamento inicial do SDK
- Arquitetura 100% assíncrona
- Tipagem forte com Pydantic
- Pool de conexões e retry logic
- Sistema de hooks extensível
- Operações CRUD básicas
- Suporte a OData
- CLI básica
- Documentação completa
- Testes unitários e de integração
- CI/CD com GitHub Actions

---

## Tipos de Mudanças

- `Added` para novas funcionalidades
- `Changed` para mudanças em funcionalidades existentes
- `Deprecated` para funcionalidades que serão removidas
- `Removed` para funcionalidades removidas
- `Fixed` para correções de bugs
- `Security` para correções de vulnerabilidades

