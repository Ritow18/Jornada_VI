import sqlite3
import os 
import json
import sys
from pathlib import Path

raiz_codigo = Path(__file__).resolve().parent.parent
if str(raiz_codigo) not in sys.path:
    sys.path.append(str(raiz_codigo))

from core.calculos import CalculadorRigging

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
            CREATE TABLE IF NOT EXISTS Tipo_acessorio (
                ID_tipo_acessorio INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_tipo TEXT NOT NULL
            )
        ''')
        # Verifica se a tabela já possui registros, se estiver vazia, insere os tipos padrão
        self.cursor.execute("SELECT COUNT(*) FROM Tipo_acessorio")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.executemany(
                "INSERT INTO Tipo_acessorio (nome_tipo) VALUES (?)",
                [("Cinta Tubular",), ("Manilha",), ("Balancim",), ("Manilha Curva",)]
            )
            self.conexao.commit()
        

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Guindaste (
                ID_guindaste INTEGER PRIMARY KEY AUTOINCREMENT,
                modelo TEXT NOT NULL,
                fabricante TEXT NOT NULL,
                capac_max_base_ton REAL NOT NULL,
                tabelaCarga_JSON TEXT
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
                ID_guindaste INTEGER NOT NULL,
                numeroPlano TEXT NOT NULL,
                cliente TEXT NOT NULL,
                dataOperacao TEXT NOT NULL,
                raioOperacao REAL NOT NULL,
                velocidadeVento REAL,
                statusAprovacao INTEGER, 
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

class RepFormula:
    def __init__(self, banco):
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
        return self.cursor.fetchall()

    def buscar_por_id(self, id_formula: int) -> tuple:
        sql = "SELECT * FROM FormulaCustomizada WHERE ID_formula = ?"
        self.cursor.execute(sql, (id_formula,))
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

class RepGuindaste:
    def __init__(self, banco):
        self.conexao = banco.conexao
        self.cursor = banco.cursor

    # 1. CREATE (Cadastrar Guindaste com Tabela de Carga em JSON)
    def salvar_guindaste(self, modelo: str, fabricante: str, capac_max_ton: float, tabela_carga: dict) -> int:
        # Converte o dicionário Python para uma string formatada em JSON
        tabela_json = json.dumps(tabela_carga)
        
        sql = '''
            INSERT INTO Guindaste (modelo, fabricante, capac_max_base_ton, tabelaCarga_JSON)
            VALUES (?, ?, ?, ?)
        '''
        self.cursor.execute(sql, (modelo, fabricante, capac_max_ton, tabela_json))
        self.conexao.commit()
        return self.cursor.lastrowid
    
    # 4. DELETE (Excluir Guindaste)
    def deletar_guindaste(self, id_guindaste: int) -> bool:
        sql = "DELETE FROM Guindaste WHERE ID_guindaste = ?"
        self.cursor.execute(sql, (id_guindaste,))
        self.conexao.commit()
        return self.cursor.rowcount > 0

    # 2. READ (Buscar Guindaste por ID e converter JSON de volta para Dicionário)
    def buscar_por_id(self, id_guindaste: int) -> dict:
        sql = "SELECT ID_guindaste, modelo, fabricante, capac_max_base_ton, tabelaCarga_JSON FROM Guindaste WHERE ID_guindaste = ?"
        self.cursor.execute(sql, (id_guindaste,))
        linha = self.cursor.fetchone()
        
        if not linha:
            return None
            
        return {
            "id": linha[0],
            "modelo": linha[1],
            "fabricante": linha[2],
            "capac_max_base_ton": linha[3],
            "tabela_carga": json.loads(linha[4]) if linha[4] else {}
        }

    # 3. READ ALL (Listar toda a frota cadastrada)
    def listar_todos(self) -> list:
        sql = "SELECT ID_guindaste, modelo, fabricante, capac_max_base_ton FROM Guindaste"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

class RepAcessorio:
    def __init__(self, banco):
        self.conexao = banco.conexao
        self.cursor = banco.cursor

    def salvar_acessorio(self, tipo_id: int, cod: str, capac: float, desgaste: float) -> int:
        sql = '''
            INSERT INTO Acessorio (ID_tipo_acessorio, codIdentificacao, capac_carga_ton, desgaste_perc)
            VALUES (?, ?, ?, ?)
        '''
        self.cursor.execute(sql, (tipo_id, cod, capac, desgaste))
        self.conexao.commit()
        return self.cursor.lastrowid

    def listar_todos(self) -> list:
        sql = '''
            SELECT a.ID_acessorio, t.nome_tipo, a.codIdentificacao, a.capac_carga_ton, a.desgaste_perc 
            FROM Acessorio a
            LEFT JOIN Tipo_acessorio t ON a.ID_tipo_acessorio = t.ID_tipo_acessorio
        '''
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def deletar_acessorio(self, id_acessorio: int) -> bool:
        sql = "DELETE FROM Acessorio WHERE ID_acessorio = ?"
        self.cursor.execute(sql, (id_acessorio,))
        self.conexao.commit()
        return self.cursor.rowcount > 0

if __name__ == "__main__":
    
    db = BancoDeDados()
    repo_formula = RepFormula(db)   
    
