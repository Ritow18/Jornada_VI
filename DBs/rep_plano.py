"""Persistência do Plano de Rigging.

Arquivo separado de rep.py de propósito: assim ninguém precisa mexer no
mesmo arquivo ao mesmo tempo. Não importa nada de rep.py (evita import circular).
"""
from datetime import datetime

# Colunas ajustadas para refletir apenas KG
COLUNAS_NOVAS = {
    "Acessorio": [
        ("peso_unitario_kg", "REAL DEFAULT 0"),
    ],
    "PlanoRigging": [
        ("local", "TEXT"),
        ("lanca_m", "REAL"),
        ("carga_bruta_kg", "REAL"), 
        ("capacidade_kg", "REAL"),
        ("tu_guindaste", "REAL"),
        ("esforco_sapata_kgf", "REAL"),
        ("rmet_kgf_cm2", "REAL"),
        ("peso_guindaste_caminhao_kgf", "REAL"),
        ("dist_eixo_sapata_m", "REAL"),
        ("abertura_sapatas_m", "REAL"),
        ("dormente_larg_cm", "REAL"),
        ("dormente_comp_cm", "REAL"),
        ("dormente_qtd", "INTEGER"),
        ("resistencia_terreno", "REAL"),
    ],
    "Rel_Plano_Acessorio": [
        ("angulo_graus", "REAL"),
        ("pernas", "INTEGER"),
        ("carga_aplicada_kg", "REAL"),
        ("esforco_kg", "REAL"), 
        ("tu_percentual", "REAL"),
    ],
}


def migrar_schema_plano(conexao):
    cur = conexao.cursor()
    for tabela, colunas in COLUNAS_NOVAS.items():
        existentes = {linha[1] for linha in cur.execute(f"PRAGMA table_info({tabela})").fetchall()}
        for nome, ddl in colunas:
            if nome not in existentes:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {ddl}")
    conexao.commit()


class RepPlano:
    def __init__(self, banco):
        self.conexao = banco.conexao
        self.cursor = banco.cursor

    def listar_acessorios(self) -> list:
        """Acessórios com tudo que o cálculo precisa."""
        self.cursor.execute('''
            SELECT a.ID_acessorio, t.nome_tipo, a.codIdentificacao,
                   a.capac_carga_kg, a.desgaste_perc, COALESCE(a.peso_unitario_kg, 0)
            FROM Acessorio a
            LEFT JOIN Tipo_acessorio t ON a.ID_tipo_acessorio = t.ID_tipo_acessorio
            ORDER BY t.nome_tipo, a.codIdentificacao
        ''')
        return [
            {"id": r[0], "tipo": r[1] or "", "codigo": r[2], "capac_kg": r[3],
             "desgaste_perc": r[4], "peso_unit_kg": r[5]}
            for r in self.cursor.fetchall()
        ]

    def proximo_numero(self) -> str:
        """Número sequencial no padrão da empresa: AAMM + 3 dígitos (ex.: 2607035)."""
        prefixo = datetime.now().strftime("%y%m")
        self.cursor.execute(
            "SELECT MAX(numeroPlano) FROM PlanoRigging WHERE numeroPlano LIKE ?", (prefixo + "%",))
        ultimo = self.cursor.fetchone()[0]
        seq = int(ultimo[len(prefixo):]) + 1 if ultimo else 1
        return f"{prefixo}{seq:03d}"

    def salvar_plano(self, cab: dict, carga: dict, itens: list, res: dict) -> str:
        """Grava plano + carga + acessórios numa única transação. Retorna o número do plano."""
        numero = self.proximo_numero()
        sap = res.get("sapatas") or {}
        s = cab.get("sapatas_entrada") or {}
        try:
            self.cursor.execute(
                f'''INSERT INTO PlanoRigging
                    (ID_guindaste, numeroPlano, cliente, dataOperacao, raioOperacao,
                     velocidadeVento, statusAprovacao, local, lanca_m, carga_bruta_kg,
                     capacidade_kg, tu_guindaste, esforco_sapata_kgf, rmet_kgf_cm2,
                     peso_guindaste_caminhao_kgf, dist_eixo_sapata_m, abertura_sapatas_m,
                     dormente_larg_cm, dormente_comp_cm, dormente_qtd, resistencia_terreno)
                    VALUES ({",".join(["?"] * 21)})''',
                (cab["id_guindaste"], numero, cab["cliente"], cab["data_iso"], cab["raio_m"],
                 cab.get("vento"), 1 if res["aprovado"] else 0, cab.get("local"), cab["lanca_m"],
                 res["carga_bruta_kg"], res["capacidade_kg"], res["tu_guindaste"]["tu_percentual"],
                 sap.get("esforco_kgf"), sap.get("rmet"),
                 s.get("peso_guindaste_kgf"), s.get("dist_eixo_m"), s.get("abertura_m"),
                 s.get("dormente_larg_cm"), s.get("dormente_comp_cm"), s.get("dormente_qtd"),
                 s.get("resistencia_terreno")))
            id_plano = self.cursor.lastrowid

            self.cursor.execute(
                '''INSERT INTO Carga (ID_plano, descricao, pesoLiquido_kg, comprimento_m, largura_m, altura_m)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (id_plano, carga["descricao"], carga["peso_liquido_kg"], # Sem dividir por 1000
                 carga.get("comp_m"), carga.get("larg_m"), carga.get("alt_m")))

            for l in res["linhas"]:
                self.cursor.execute(
                    '''INSERT INTO Rel_Plano_Acessorio
                       (ID_plano, ID_acessorio, quantidade_usada, angulo_graus, pernas,
                        carga_aplicada_kg, esforco_kg, tu_percentual)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (id_plano, l["id"], l["qtd"], l.get("angulo"), l.get("pernas"),
                     l["carga_aplicada_kg"], l["esforco_kg"], l["tu_percentual"])) # Sem multiplicar por 1000

            self.conexao.commit()
            return numero
        except Exception:
            self.conexao.rollback()
            raise