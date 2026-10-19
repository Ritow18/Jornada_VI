import sqlite3

class BancoDeDados:
    def __init__(self, nome_arquivo="banco_rigging.sqlite"):
        self.conexao = sqlite3.connect(nome_arquivo)
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

        self.conexao.commit()
        print("Toda a teia do banco de dados foi tecida com sucesso")

# Teste de terminal
if __name__ == "__main__":
    db = BancoDeDados()