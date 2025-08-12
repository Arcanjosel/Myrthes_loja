# Myrthes Costuras

Aplicativo de gestão de oficina de costuras (concertos em geral), com PyQt6 (MVC) e Firebase (Firestore).

Dados da empresa:
- Nome Fantasia: Myrthes Costuras
- Razão Social: Mirtes Eliane Oliveira Costa
- CNPJ: 42.275.758/0001-82
- Inscrição Estadual (SP): 797.744.619.116
- Telefone: (16) 98854-7350

## Requisitos
- Python 3.10+ (desenvolvido e testado em 3.13)
- Windows 10/11

## Instalação (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Operação Offline (SQLite)
O aplicativo funciona totalmente offline usando SQLite. O suporte a Firebase foi removido nesta versão. A fila local de sincronização (`sync_queue`) permanece apenas para auditoria e pode ser limpa pelo diálogo "Sincronização".

## Executando
```powershell
python main.py
```

## Estrutura (resumo)
- `main.py`: inicializa app e janelas
- `app/config`: configurações gerais e Firebase
- `app/models`: modelos (Cliente, Serviço, etc.)
- `app/controllers`: controladores (regras da UI)
- `app/views`: janelas e componentes PyQt6
- `app/utils/firebase_repository.py`: acesso ao Firestore e fallback em memória

## Funcionalidades
- Dashboard: gráficos (matplotlib) de serviços mais/menos rentáveis e receita por dia, com exportação CSV.
- Pedidos: criação, busca por status/cliente/código, marcação de entregue, remoção em lote, impressão de recibo (térmica/arquivo).
- Clientes: cadastro, busca e listagem.
- Serviços: cadastro, ativação/desativação, edição de preço, filtros.
- Estoque: itens com ajuste de quantidade (exemplo simples, pode ser expandido).
- Sincronização: fila local (SQLite) e envio ao Firestore; diálogo para informar JSON de credenciais e disparar sync manual.
- Aparência/UX:
  - Tema system/dark (toggle no header); fonte global configurável (`UI_FONT_FAMILY`/`UI_FONT_SIZE_PT`).
  - Cabeçalhos de diálogos com cor `#007065` e descrições;
  - Tabelas com larguras ajustadas para colunas curtas (código, status, etc.).

## Atalhos e Navegação
- Ctrl+N: Novo pedido
- Ctrl+L: Ir para lista de pedidos
- Ctrl+Shift+C: Clientes
- Ctrl+Shift+S: Serviços
- Ctrl+D: Dashboard
- Ctrl+T: Alternar tema
- Ctrl+Shift+R: Sincronizar agora
- Delete: Remover pedidos selecionados

## Impressora Térmica
- Suporta USB (Vendor/Product ID), Serial (COMx) e IP (Network).
- Configurações em `Configurações → Impressora` ou diretamente no `settings.json`.

## Configurações Persistentes
- `settings.json` na raiz do projeto (é criado/sincronizado pelo app).
- Chaves relevantes: `APP_NAME`, `COMPANY_NAME`, `CNPJ`, `PHONE`, `DB_PATH`, `UI_*`, `THERMAL_PRINTER_*`, `FIREBASE_CREDENTIALS`.

## Sincronização (detalhes)
- Operações são enfileiradas em `sync_queue` (SQLite) e enviadas periodicamente.
- Diálogo “Sincronização” permite informar/alterar o caminho do JSON e enviar a fila imediatamente.
- Remoção de pedidos hoje remove apenas localmente. Se desejar replicar remoções no Firestore, será necessário estender o `SyncManager` com um evento de delete.

## Banco de Dados (SQLite)
- Tabelas: `services`, `clients`, `orders`, `order_items`, `payments`, `inventory`, `sync_queue`.
- Agregações prontas para o dashboard: `top_services_by_revenue`, `bottom_services_by_revenue`, `revenue_by_day`.

## Mock de Dados para Dashboard
- Se o banco estiver vazio, ao abrir o Dashboard é gerado um conjunto de pedidos fictícios para demonstrar os gráficos.

## Ícones e Cabeçalho
- Cabeçalho superior com logo `logo4.png`/`logo2.png` (raiz ou `assets/`) e botões: novo pedido, clientes, serviços, configurações, sincronização, alternar tema, dashboard.
- Abas com ícones.

## Notas
- Preços são armazenados em centavos para evitar erros de ponto flutuante.
- Primeira execução popula serviços padrão se a coleção estiver vazia.
- O app tenta localizar automaticamente `myrthes.json` nas pastas usuais.

## Notas
- Preços são armazenados em centavos para evitar erros de ponto flutuante.
- Primeira execução popula serviços padrão se a coleção estiver vazia.
