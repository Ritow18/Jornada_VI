# RigMaster (Guindastes Ribas LTDA) — Sistema de Automação de Rigging

O **RigMaster** é um software desktop de engenharia desenvolvido para planejar, calcular e documentar operações de içamento de carga (Plano de Rigging). O sistema une um motor matemático rigoroso a uma interface gráfica fluida, garantindo a segurança operacional e automatizando a geração de laudos técnicos e anexos (ART/CREA).

## Tecnologias e Arquitetura
- **Linguagem:** Python 3.x.
- **Interface Gráfica (UI):** CustomTkinter (arquitetura unificada em janela única, design moderno e responsivo).
- **Banco de Dados:** SQLite3 (nativo, embarcado e sem dependência de servidores).
- **Geração e Manipulação de Documentos:** `fpdf` (criação de laudos) e `pypdf` (mesclagem de anexos e extração de texto offline).
- **Processamento em Memória:** Uso avançado de `io.BytesIO` para processar e mesclar PDFs diretamente na memória RAM, sem a criação de arquivos temporários no disco.
- **Distribuição (Build):** Compilado nativamente para Windows via `PyInstaller` (geração de executável `.exe` autossuficiente).

## Estrutura e Módulos Implementados

### 1. Interface Gráfica e Navegação (`UI/`)
Arquitetura baseada em MVP (Model-View-Presenter), unificada por um menu lateral dinâmico.
- **`TPrincipal.py`**: Ponto de entrada do sistema. Gerencia o layout principal, o redirecionamento dinâmico de diretórios (via `sys._MEIPASS` e `sys.frozen`) e alterna entre as telas sem abrir novas janelas.
- **`TDashboard.py`**: Painel central de visualização e métricas rápidas da operação.
- **`TPlano.py`**: Interface completa para o Plano de Rigging. Calcula a segurança da operação, gerencia a lingada de acessórios, anexa PDFs de ART/CREA (com auto-preenchimento inteligente de numeração via leitura do documento) e exporta o laudo final mesclado.
- **`TFrota.py`**: Gestão de guindastes (CRUD). Inclui um construtor visual de tabelas de carga, eliminando a necessidade de o usuário digitar matrizes JSON manualmente.
- **`TAcessorios.py`**: Cadastro e gestão de cintas, manilhas e outros equipamentos de amarração. Totalmente integrado ao catálogo da tela de Plano de Rigging.

### 2. Motor Matemático e Documental (`core/`)
Concentra as regras de negócio, algoritmos de engenharia e regras de exportação.
- **`CalculadorRigging`**: Calcula carga bruta, tensão em cintas multicabo, esforços nas sapatas, RMET (área de patolamento) e Taxa de Utilização do guindaste e dos acessórios (trava de segurança em 85%).
- **Interpolação Linear**: Trava cálculos fora dos limites do fabricante e calcula capacidades com precisão para raios intermediários não tabelados.
- **Motor de Geração PDF**: Transforma os cálculos em um laudo estruturado e une dinamicamente arquivos anexos em um único arquivo de saída.

### 3. Persistência de Dados e Isolamento (`DBs/`)
Gerencia o banco local `banco_rigging.sqlite` com alta segurança e resiliência de ambiente.
- **Ambiente de Produção (`.exe`)**: O sistema detecta automaticamente o modo de execução e cria/gerencia o banco de dados de forma invisível na pasta `AppData/Local/RigMaster` do Windows, garantindo que o usuário final interaja apenas com o `.exe` sem o risco de deletar arquivos sensíveis.
- **Repositórios (`rep.py` e `rep_plano.py`)**: Possuem numeração automática sequencial (padrão `AAMMXXX`), suporte a transações unificadas (vínculo entre Plano, Carga e Acessórios Utilizados) e execução de *Migrations* de schema dinâmicas (`migrar_schema_plano`).

## Como Executar

### Opção 1: Via Executável (Usuário Final)
Basta baixar o arquivo **`RigMaster.exe`** (gerado na pasta `dist/` após a compilação) e executá-lo em qualquer máquina Windows. O sistema criará seu próprio ecossistema de banco de dados automaticamente.

### Opção 2: Via Código-Fonte (Desenvolvimento)
1. Instale as dependências listadas:
   pip install -r requirements.txt
   rode o arquivo TPrincipal.py
