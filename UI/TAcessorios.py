import customtkinter as ctk
from DBs.rep import BancoDeDados, RepAcessorio

class TelaAcessorios(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.db = BancoDeDados()
        self.repo = RepAcessorio(self.db)

        # Mapeia os Tipos de Acessórios cadastrados no SQLite
        self.cursor = self.db.cursor
        self.cursor.execute("SELECT ID_tipo_acessorio, nome_tipo FROM Tipo_acessorio")
        tipos = self.cursor.fetchall()
        self.mapa_tipos = {t[1]: t[0] for t in tipos}

        self.titulo = ctk.CTkLabel(self, text="Gestão de Acessórios", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, columnspan=2, pady=(20, 20))

        # ================= ESQUERDA: CADASTRO =================
        self.frame_cadastro = ctk.CTkFrame(self)
        self.frame_cadastro.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_cadastro, text="Novo Acessório", font=("Roboto", 18, "bold")).pack(pady=10)

        ctk.CTkLabel(self.frame_cadastro, text="Tipo de Acessório:").pack(pady=(5,0))
        self.combo_tipo = ctk.CTkComboBox(self.frame_cadastro, width=300, values=list(self.mapa_tipos.keys()))
        self.combo_tipo.pack(pady=5)

        self.inp_cod = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Código Identificador (Ex: CIN-001)", width=300)
        self.inp_cod.pack(pady=5)

        self.inp_capac = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Capacidade de Carga (ton)", width=300)
        self.inp_capac.pack(pady=5)

        self.inp_desgaste = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Desgaste % (Ex: 0.0)", width=300)
        self.inp_desgaste.pack(pady=5)

        self.btn_salvar = ctk.CTkButton(self.frame_cadastro, text="Salvar Acessório", command=self.salvar_novo, fg_color="#2ECC71", hover_color="#27AE60")
        self.btn_salvar.pack(pady=15)

        # ================= DIREITA: LISTAGEM =================
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Acessórios Cadastrados")
        self.frame_lista.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        
        self.carregar_lista()

    def carregar_lista(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        acessorios = self.repo.listar_todos() # Retorna: ID, nome_tipo, codIdentificacao, capac, desgaste
        
        if not acessorios:
            ctk.CTkLabel(self.frame_lista, text="Nenhum acessório cadastrado.").pack(pady=20)
            return

        for a in acessorios:
            id_a, tipo, cod, capac, desgaste = a[0], a[1], a[2], a[3], a[4]
            
            card = ctk.CTkFrame(self.frame_lista, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=5)
            
            info = f"[{tipo}] {cod}\nCapacidade: {capac} t | Desgaste: {desgaste}%"
            ctk.CTkLabel(card, text=info, font=("Roboto", 12), justify="left").pack(side="left", padx=10, pady=10)
            
            btn_del = ctk.CTkButton(card, text="Excluir", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                                    command=lambda i=id_a: self.deletar(i))
            btn_del.pack(side="right", padx=10, pady=10)

    def salvar_novo(self):
        try:
            tipo_nome = self.combo_tipo.get()
            tipo_id = self.mapa_tipos.get(tipo_nome)
            cod = self.inp_cod.get()
            capac = float(self.inp_capac.get())
            desgaste = float(self.inp_desgaste.get() or 0.0)

            if tipo_id and cod:
                self.repo.salvar_acessorio(tipo_id, cod, capac, desgaste)
                
                self.inp_cod.delete(0, 'end')
                self.inp_capac.delete(0, 'end')
                self.inp_desgaste.delete(0, 'end')
                
                self.carregar_lista()
        except Exception as e:
            print(f"Erro ao salvar acessório: {e}")

    def deletar(self, id_acessorio):
        self.repo.deletar_acessorio(id_acessorio)
        self.carregar_lista()