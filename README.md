# Guindastes Ribas LTDA — Sistema de Automação de Rigging

## Tecnologias e Ferramentas
* Linguagem: Python 3.x.
* Interface Gráfica (UI): CustomTkinter (arquitetura unificada em janela única).
* Banco de Dados: SQLite3 (nativo, sem dependência de servidores).
* Processamento: Bibliotecas nativas `math` e `json` (motor leve, sem dependências como sympy).
* Distribuição: Preparado para compilação via PyInstaller (.exe).


## Estrutura e Módulos Implementados
### 1. Interface Gráfica e Navegação (`UI/`)
Arquitetura baseada em MVP (Model-View-Presenter), unificada por um menu lateral lateral dinâmico.
* `TPrincipal.py`: Ponto de entrada do sistema. Gerencia o layout principal e alterna entre as telas sem abrir novas janelas.
* `TOperacao.py`: Simulador de içamento. Puxa dados reais do banco, realiza o cálculo de segurança (TU) e exibe o status de aprovação.
* `TFrota.py`: Gestão de guindastes (CRUD). Inclui um construtor visual de tabelas de carga, eliminando a necessidade de o usuário digitar JSON manualmente.
* `TAcessorios.py`: Cadastro e gestão de cintas, manilhas e outros equipamentos de amarração.
* `TFormulas.py`: Construtor de fórmulas customizadas. Conta com um teclado visual de calculadora científica para inserção segura de funções algébricas e trigonométricas.

### 2. Motor Matemático (`core/calculos.py`)
Concentra as regras de negócio, travas de segurança e algoritmos de engenharia.
* `CalculadorRigging`: Calcula carga bruta, tensão em cintas, esforços nas sapatas, RMET (área de patolamento) e Taxa de Utilização (limite de 85%).
* Interpolação Linear: Trava cálculos fora dos limites do fabricante e calcula capacidades para raios intermediários não tabelados.
* `MotorFormulasCustomizadas`: Avaliador em sandbox (`__builtins__: None`) que executa fórmulas cadastradas em texto. Suporta trigonometria, logaritmos e comparadores nativos de forma isolada e segura.

### 3. Persistência de Dados (`DBs/rep.py`)
Gerencia o banco local `banco_rigging.sqlite` com resolução automática de caminhos absolutos (portabilidade garantida).
* Estrutura Relacional: 
  * Tabelas de Frota (`Guindaste`) com armazenamento de matrizes em JSON.
  * Tabelas Operacionais (`PlanoRigging`, `Carga`).
  * Tabelas de Equipamentos e Herança (`Acessorio`, `Cinta_Tubular`, `Manilha`) com `ON DELETE CASCADE`.
* Classes de Repositório: `BancoDeDados`, `RepGuindaste`, `RepFormula` e `RepAcessorio` controlam todas as operações CRUD e conversões de dados entre Python e SQLite.

## Próximos Passos (Faltantes / Backlog)

1. Geração de Relatórios (Exportação)
   * Desenvolver um módulo para capturar os dados processados na tela de simulação (`TOperacao.py`) e exportar um laudo/plano de rigging completo em formato PDF ou Excel.
   * O relatório deve conter os dados do guindaste, geometria do içamento, cálculos de segurança e o parecer técnico final.

2. Integração Plena das Fórmulas Customizadas
   * Atualmente, o sistema cria e armazena fórmulas personalizadas de forma excelente. O próximo passo é integrar esse repositório à tela de Operação.
   * Objetivo: Permitir que o engenheiro selecione uma fórmula cadastrada, insira os valores das variáveis criadas, e o sistema utilize o motor de cálculo para aplicar esse resultado adicional ao içamento (ex: adicionar uma taxa de vento dinâmica ao peso da carga).