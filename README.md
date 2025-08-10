# Myrthes Costuras

Aplicativo de gestão de oficina de costuras (concertos em geral), com PyQt6 (MVC) e Firebase (Firestore).

Dados da empresa:
- Nome Fantasia: Myrthes Costuras
- Razão Social: Mirtes Eliane Oliveira Costa
- CNPJ: 42.275.758/0001-82
- Inscrição Estadual (SP): 797.744.619.116
- Telefone: (16) 98854-7350

## Requisitos
- Python 3.10+
- Windows 10/11

## Instalação (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuração do Firebase
1. Crie um projeto no Firebase e gere a chave JSON de uma conta de serviço com acesso ao Firestore.
2. Baixe o arquivo e salve-o na raiz do projeto como `firebase_credentials.json` (ou use outro caminho).
3. Defina a variável de ambiente `FIREBASE_CREDENTIALS` ou crie um arquivo `.env` com:
```
FIREBASE_CREDENTIALS=firebase_credentials.json
```

Opcional: Se não houver credenciais, o app funciona em modo offline com dados em memória (útil para testes iniciais).

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

## Status atual
- Aba Serviços funcional com edição de preços. Demais abas (Clientes, Pedidos, Estoque) com placeholders para evolução incremental.

## Notas
- Preços são armazenados em centavos para evitar erros de ponto flutuante.
- Primeira execução popula serviços padrão se a coleção estiver vazia.
