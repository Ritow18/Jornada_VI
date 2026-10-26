import sqlite3
import os 

class BancoDeDados:
    def __init__(self, nome_arquivo="banco_rigging.sqlite"):

        dir_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_banco = os.path.join(dir_atual, nome_arquivo)

        self.conexao = sqlite3.connect(caminho_banco)
        self.cursor = self.conexao.cursor()
        
        # Força o SQLite a respeitar as Chaves Estrangeiras (FK)
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        
        self.criar_tabelas()

    def criar_tabelas(self):
        # 1. Tabelas Independentes (Não possuem Chave Estrangeira)
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Nivel_acesso (
                ID_role INTEGER PRIMARY KEY AUTOINCREMENT,
                Nome_role TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tipo_acessorio (
                ID_tipo_acessorio INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_tipo TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Guindaste (
                ID_guindaste INTEGER PRIMARY KEY AUTOINCREMENT,
                modelo TEXT NOT NULL,
                fabricante TEXT NOT NULL,
                capac_max_base_ton REAL NOT NULL,
                tabelaCarga_JSON TEXT
            )
        ''')

        # 2. Tabelas Nível 1 (Dependem das tabelas acima)

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Usuario (
                ID_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_role INTEGER NOT NULL,
                Reg_profissional TEXT NOT NULL,
                Nome_completo TEXT NOT NULL,
                Senha_hash TEXT NOT NULL,
                FOREIGN KEY (ID_role) REFERENCES Nivel_acesso (ID_role)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Acessorio (
                ID_acessorio INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_tipo_acessorio INTEGER NOT NULL,
                codIdentificacao TEXT NOT NULL,
                capac_carga_ton REAL NOT NULL,
                desgaste_perc REAL NOT NULL,
                dataUltimaInspecao TEXT,
                FOREIGN KEY (ID_tipo_acessorio) REFERENCES Tipo_acessorio (ID_tipo_acessorio)
            )
        ''')

        # 3. Tabelas de Extensão/Herança (Chave Primária = Chave Estrangeira)

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Cinta_Tubular (
                ID_acessorio INTEGER PRIMARY KEY,
                comprimento_m REAL NOT NULL,
                anguloInclinacao REAL,
                FOREIGN KEY (ID_acessorio) REFERENCES Acessorio (ID_acessorio) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Manilha (
                ID_acessorio INTEGER PRIMARY KEY,
                grauAco TEXT NOT NULL,
                diametro_pol REAL NOT NULL,
                FOREIGN KEY (ID_acessorio) REFERENCES Acessorio (ID_acessorio) ON DELETE CASCADE
            )
        ''')

        # 4. Tabelas Operacionais e Associativas

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS PlanoRigging (
                ID_plano INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_usuario_criador INTEGER NOT NULL,
                ID_guindaste INTEGER NOT NULL,
                numeroPlano TEXT NOT NULL,
                cliente TEXT NOT NULL,
                dataOperacao TEXT NOT NULL,
                raioOperacao REAL NOT NULL,
                velocidadeVento REAL,
                statusAprovacao INTEGER, 
                FOREIGN KEY (ID_usuario_criador) REFERENCES Usuario (ID_usuario),
                FOREIGN KEY (ID_guindaste) REFERENCES Guindaste (ID_guindaste)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Carga (
                ID_carga INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_plano INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                pesoLiquido_ton REAL NOT NULL,
                comprimento_m REAL,
                largura_m REAL,
                altura_m REAL,
                FOREIGN KEY (ID_plano) REFERENCES PlanoRigging (ID_plano) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Rel_Plano_Acessorio (
                ID_plano INTEGER NOT NULL,
                ID_acessorio INTEGER NOT NULL,
                quantidade_usada INTEGER NOT NULL,
                PRIMARY KEY (ID_plano, ID_acessorio),
                FOREIGN KEY (ID_plano) REFERENCES PlanoRigging (ID_plano),
                FOREIGN KEY (ID_acessorio) REFERENCES Acessorio (ID_acessorio)
            )
        ''')
        
        # Tabela para o Motor de Fórmulas Customizadas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS FormulaCustomizada (
                ID_formula INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_calculo TEXT NOT NULL,
                descricao TEXT,
                variaveis_esperadas TEXT NOT NULL, 
                expressao_matematica TEXT NOT NULL
            )
        ''')

        self.conexao.commit()
        print("Bancos e relações construidas")

class RepFormula:
    def __init__(self, banco):
        # Recebe a instância da classe BancoDeDados
        self.conexao = banco.conexao
        self.cursor = banco.cursor

    # 1. CREATE (Salvar nova fórmula)
    def salvar_formula(self, nome: str, descricao: str, variaveis: str, expressao: str) -> int:
        sql = '''
            INSERT INTO FormulaCustomizada (nome_calculo, descricao, variaveis_esperadas, expressao_matematica)
            VALUES (?, ?, ?, ?)
        '''
        self.cursor.execute(sql, (nome, descricao, variaveis, expressao))
        self.conexao.commit()
        return self.cursor.lastrowid # Retorna o ID único que o banco gerou para essa fórmula

    # 2. READ (Buscar/Listar fórmulas)
    def listar_todas(self) -> list:
        sql = "SELECT ID_formula, nome_calculo, variaveis_esperadas, expressao_matematica FROM FormulaCustomizada"
        self.cursor.execute(sql)
        
        # fetchall() busca todas as linhas encontradas e entrega como uma lista de tuplas
        # Exemplo: [(1, 'Fator Vento', 'vento, area', '(vento**2)*area'), (2, ...)]
        return self.cursor.fetchall()

    def buscar_por_id(self, id_formula: int) -> tuple:
        sql = "SELECT * FROM FormulaCustomizada WHERE ID_formula = ?"
        self.cursor.execute(sql, (id_formula,))
        
        # fetchone() traz apenas a 1a linha encontrada ou None se não existir
        return self.cursor.fetchone()

    # 3. UPDATE (Atualizar fórmula existente)
    def atualizar_formula(self, id_formula: int, nome: str, variaveis: str, expressao: str) -> bool:
        sql = '''
            UPDATE FormulaCustomizada 
            SET nome_calculo = ?, variaveis_esperadas = ?, expressao_matematica = ?
            WHERE ID_formula = ?
        '''
        self.cursor.execute(sql, (nome, variaveis, expressao, id_formula))
        self.conexao.commit()
        return self.cursor.rowcount > 0 # Retorna True se alterou alguma linha

    # 4. DELETE (Excluir fórmula)
    def deletar_formula(self, id_formula: int) -> bool:
        sql = "DELETE FROM FormulaCustomizada WHERE ID_formula = ?"
        self.cursor.execute(sql, (id_formula,))
        self.conexao.commit()
        return self.cursor.rowcount > 0


# Teste isolado do CRUD de fórmulas
if __name__ == "__main__":
    
    # Prepara o banco
    db = BancoDeDados()
    repo_formula = RepFormula(db)
    
    print("--- 1. TESTANDO INSERÇÃO (CREATE) ---")
    id_criado = repo_formula.salvar_formula(
        nome="Pressao de Vento Extra",
        descricao="Cálculo de rajada lateral",
        variaveis="v, a",
        expressao="0.613 * (v ** 2) * a"
    )
    print(f"Fórmula cadastrada com Sucesso! ID no SQLite: {id_criado}")
    
    print("\n--- 2. TESTANDO LEITURA (READ) ---")
    formulas = repo_formula.listar_todas()
    for f in formulas:
        print(f"ID: {f[0]} | Nome: {f[1]} | Vars: {f[2]} | Expressão: {f[3]}")