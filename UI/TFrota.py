import customtkinter as ctk
from DBs.rep import BancoDeDados, RepGuindaste

class TelaFrota(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.db = BancoDeDados()
        self.repo = RepGuindaste(self.db)
        
        # Dicionário temporário para guardar a tabela de carga enquanto o usuário constrói
        self.tabela_temp = {}

        # --- TÍTULO ---
        self.titulo = ctk.CTkLabel(self, text="Gestão de Guindastes", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, columnspan=2, pady=(20, 20))

        # ================= ESQUERDA: CADASTRO =================
        self.frame_cadastro = ctk.CTkScrollableFrame(self)
        self.frame_cadastro.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_cadastro, text="Novo Equipamento", font=("Roboto", 18, "bold")).pack(pady=10)

        self.inp_modelo = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Modelo (Ex: LTM 1100)", width=300)
        self.inp_modelo.pack(pady=5)

        self.inp_fab = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Fabricante (Ex: Liebherr)", width=300)
        self.inp_fab.pack(pady=5)

        self.inp_cap = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Capacidade Máxima (ton)", width=300)
        self.inp_cap.pack(pady=5)

        # --- CONSTRUTOR DA TABELA DE CARGA ---
        frame_tabela = ctk.CTkFrame(self.frame_cadastro, fg_color="#333333")
        frame_tabela.pack(pady=15, padx=10, fill="x")
        
        ctk.CTkLabel(frame_tabela, text="Construtor da Tabela de Carga", font=("Roboto", 14, "bold")).pack(pady=5)
        
        # Inputs para os pontos da tabela
        self.inp_lanca = ctk.CTkEntry(frame_tabela, placeholder_text="Lança (m) Ex: 30.0", width=280)
        self.inp_lanca.pack(pady=2)
        
        self.inp_raio = ctk.CTkEntry(frame_tabela, placeholder_text="Raio (m) Ex: 8.0", width=280)
        self.inp_raio.pack(pady=2)
        
        self.inp_capacidade = ctk.CTkEntry(frame_tabela, placeholder_text="Capacidade (ton) Ex: 34.0", width=280)
        self.inp_capacidade.pack(pady=2)
        
        self.btn_add_ponto = ctk.CTkButton(frame_tabela, text="Adicionar Ponto na Tabela", command=self.adicionar_ponto, fg_color="#3498DB", hover_color="#2980B9")
        self.btn_add_ponto.pack(pady=10)

        # Prévia visual da tabela construída
        self.txt_preview = ctk.CTkTextbox(frame_tabela, width=280, height=100, state="disabled")
        self.txt_preview.pack(pady=5)
        self.atualizar_preview()

        # Botão final para salvar o guindaste no banco
        self.btn_salvar = ctk.CTkButton(self.frame_cadastro, text="Salvar Guindaste", command=self.salvar_novo, fg_color="#2ECC71", hover_color="#27AE60", height=40)
        self.btn_salvar.pack(pady=20)

        # ================= DIREITA: LISTAGEM =================
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Frota Cadastrada")
        self.frame_lista.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        
        self.carregar_lista()

    def adicionar_ponto(self):
        try:
            lanca = str(float(self.inp_lanca.get())) # Garante formato decimal "30.0"
            raio = str(float(self.inp_raio.get()))
            cap = float(self.inp_capacidade.get())

            if lanca not in self.tabela_temp:
                self.tabela_temp[lanca] = {}
            
            self.tabela_temp[lanca][raio] = cap
            
            # Limpa apenas raio e capacidade para facilitar digitar o próximo ponto da mesma lança
            self.inp_raio.delete(0, 'end')
            self.inp_capacidade.delete(0, 'end')
            self.inp_raio.focus()
            
            self.atualizar_preview()
        except ValueError:
            print("Erro: Preencha Lança, Raio e Capacidade apenas com números.")

    def atualizar_preview(self):
        self.txt_preview.configure(state="normal")
        self.txt_preview.delete("0.0", "end")
        
        if not self.tabela_temp:
            self.txt_preview.insert("0.0", "Nenhum ponto adicionado ainda.")
        else:
            for lanca, raios in self.tabela_temp.items():
                self.txt_preview.insert("end", f"Lança {lanca}m:\n")
                for raio, cap in raios.items():
                    self.txt_preview.insert("end", f"  - Raio {raio}m : {cap} ton\n")
                    
        self.txt_preview.configure(state="disabled")

    def carregar_lista(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        guindastes = self.repo.listar_todos()
        
        if not guindastes:
            ctk.CTkLabel(self.frame_lista, text="Nenhum guindaste cadastrado.").pack(pady=20)
            return

        for g in guindastes:
            id_g, modelo, fab, cap = g[0], g[1], g[2], g[3]
            card = ctk.CTkFrame(self.frame_lista, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=5)
            
            info = f"{fab} {modelo} | {cap} ton"
            ctk.CTkLabel(card, text=info, font=("Roboto", 14, "bold")).pack(side="left", padx=10, pady=10)
            
            btn_del = ctk.CTkButton(card, text="Excluir", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                                    command=lambda i=id_g: self.deletar(i))
            btn_del.pack(side="right", padx=10, pady=10)

    def salvar_novo(self):
        try:
            modelo = self.inp_modelo.get()
            fab = self.inp_fab.get()
            cap = float(self.inp_cap.get())
            
            if not self.tabela_temp:
                print("Erro: A tabela de carga não pode estar vazia.")
                return
            
            self.repo.salvar_guindaste(modelo, fab, cap, self.tabela_temp)
            
            # Limpa tudo
            self.inp_modelo.delete(0, 'end')
            self.inp_fab.delete(0, 'end')
            self.inp_cap.delete(0, 'end')
            self.inp_lanca.delete(0, 'end')
            self.inp_raio.delete(0, 'end')
            self.inp_capacidade.delete(0, 'end')
            
            self.tabela_temp = {}
            self.atualizar_preview()
            self.carregar_lista()
        except ValueError:
            print("Erro: Preencha todos os campos do guindaste corretamente.")

    def deletar(self, id_guindaste):
        self.repo.deletar_guindaste(id_guindaste)
        self.carregar_lista()