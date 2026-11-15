import customtkinter as ctk
from datetime import datetime
from DBs.rep import BancoDeDados, RepGuindaste
from tkinter import messagebox

# Critério -> (decrescente por padrão, rótulo da ordem crescente, rótulo da ordem decrescente)
CRITERIOS = {
    "Data/Hora":  (True,  "Mais antigos primeiro", "Mais recentes primeiro"),
    "Modelo":     (False, "A → Z", "Z → A"),
    "Fabricante": (False, "A → Z", "Z → A"),
    "Capacidade": (True,  "Menor → maior", "Maior → menor"),
}

class TelaFrota(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3) 
        self.grid_rowconfigure(2, weight=4) 

        self.db = BancoDeDados()
        self.repo = RepGuindaste(self.db)

        # Dicionário temporário para guardar a tabela de carga enquanto o usuário constrói
        self.tabela_temp = {}

        # Ordenação atual da lista
        self.criterio = "Data/Hora"
        self.ordem_decrescente = CRITERIOS[self.criterio][0]

        # --- TÍTULO ---
        self.titulo = ctk.CTkLabel(self, text="Gestão de Guindastes", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, pady=(20, 10))

        # ================= TOPO: CADASTRO =================
        frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        frame_topo.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        frame_topo.grid_columnconfigure(0, weight=1)
        frame_topo.grid_columnconfigure(1, weight=1)
        frame_topo.grid_rowconfigure(0, weight=1)

        # --- Esquerda: dados do equipamento ---
        self.frame_cadastro = ctk.CTkFrame(frame_topo)
        self.frame_cadastro.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(self.frame_cadastro, text="Novo Equipamento", font=("Roboto", 18, "bold")).pack(pady=(10, 5))

        self.inp_modelo = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Modelo (Ex: LTM 1100)", width=260)
        self.inp_modelo.pack(pady=4, padx=15)

        self.inp_fab = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Fabricante (Ex: Liebherr)", width=260)
        self.inp_fab.pack(pady=4, padx=15)

        self.inp_cap = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Capacidade Máxima (kg)", width=260)
        self.inp_cap.pack(pady=4, padx=15)

        self.btn_salvar = ctk.CTkButton(self.frame_cadastro, text="Salvar Guindaste", command=self.salvar_novo,
                                        fg_color="#2ECC71", hover_color="#27AE60", height=36)
        self.btn_salvar.pack(pady=(20, 12))

        # --- Direita: CONSTRUTOR DA TABELA DE CARGA ---
        frame_tabela = ctk.CTkFrame(frame_topo, fg_color="#333333")
        frame_tabela.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        frame_tabela.grid_columnconfigure(0, weight=1)
        frame_tabela.grid_rowconfigure(2, weight=1) # Faz a lista de pontos expandir

        ctk.CTkLabel(frame_tabela, text="Construtor da Tabela de Carga", font=("Roboto", 14, "bold")).grid(
            row=0, column=0, pady=(10, 5))

        # Inputs para os pontos da tabela
        frame_pontos = ctk.CTkFrame(frame_tabela, fg_color="transparent")
        frame_pontos.grid(row=1, column=0)

        self.inp_lanca = ctk.CTkEntry(frame_pontos, placeholder_text="Lança (m)", width=90)
        self.inp_lanca.grid(row=0, column=0, padx=3)

        self.inp_raio = ctk.CTkEntry(frame_pontos, placeholder_text="Raio (m)", width=90)
        self.inp_raio.grid(row=0, column=1, padx=3)

        self.inp_capacidade = ctk.CTkEntry(frame_pontos, placeholder_text="Cap. (kg)", width=90)
        self.inp_capacidade.grid(row=0, column=2, padx=3)

        self.btn_add_ponto = ctk.CTkButton(frame_pontos, text="Adicionar", width=90, command=self.adicionar_ponto,
                                           fg_color="#3498DB", hover_color="#2980B9")
        self.btn_add_ponto.grid(row=0, column=3, padx=3)

        # NOVO: Grid CRUD de pontos
        self.frame_pontos_lista = ctk.CTkScrollableFrame(frame_tabela, fg_color="#2b2b2b", label_text="Pontos Adicionados")
        self.frame_pontos_lista.grid(row=2, column=0, padx=15, pady=(8, 12), sticky="nsew")
        self.atualizar_preview()

        # LISTA DA FROTA 
        frame_lista_area = ctk.CTkFrame(self, fg_color="transparent")
        frame_lista_area.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="nsew")
        frame_lista_area.grid_columnconfigure(0, weight=1)
        frame_lista_area.grid_rowconfigure(1, weight=1)

        # Barra de ordenação
        barra = ctk.CTkFrame(frame_lista_area, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(barra, text="Ordenar por:").pack(side="left", padx=(5, 8))

        self.seg_criterio = ctk.CTkSegmentedButton(barra, values=list(CRITERIOS.keys()),
                                                   command=self.mudar_criterio)
        self.seg_criterio.set(self.criterio)
        self.seg_criterio.pack(side="left")

        self.btn_ordem = ctk.CTkButton(barra, text="", width=150, command=self.alternar_ordem)
        self.btn_ordem.pack(side="left", padx=10)

        self.lbl_contagem = ctk.CTkLabel(barra, text="", font=("Roboto", 12))
        self.lbl_contagem.pack(side="right", padx=5)

        self.frame_lista = ctk.CTkScrollableFrame(frame_lista_area, label_text="Frota Cadastrada")
        self.frame_lista.grid(row=1, column=0, sticky="nsew")

        self.atualizar_botao_ordem()
        self.carregar_lista()

    # ORDENAÇÃO 
    def mudar_criterio(self, criterio):
        self.criterio = criterio
        self.ordem_decrescente = CRITERIOS[criterio][0]
        self.atualizar_botao_ordem()
        self.carregar_lista()

    def alternar_ordem(self):
        self.ordem_decrescente = not self.ordem_decrescente
        self.atualizar_botao_ordem()
        self.carregar_lista()

    def atualizar_botao_ordem(self):
        _, rotulo_asc, rotulo_desc = CRITERIOS[self.criterio]
        self.btn_ordem.configure(text=rotulo_desc if self.ordem_decrescente else rotulo_asc)

    def _chave_ordenacao(self, g):
        id_g, modelo, fab, cap, data = g[0], (g[1] or "").lower(), (g[2] or "").lower(), g[3] or 0, g[4] or ""
        if self.criterio == "Modelo":
            return (modelo, fab, id_g)
        if self.criterio == "Fabricante":
            return (fab, modelo, id_g)
        if self.criterio == "Capacidade":
            return (cap, modelo, id_g)
        return (data, id_g) 

    @staticmethod
    def _formatar_data(valor):
        if not valor:
            return "data não registrada"
        try:
            return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return str(valor)

    # TABELA DE CARGA 
    def adicionar_ponto(self):
        try:
            txt_lanca = self.inp_lanca.get().replace(",", ".")
            txt_raio = self.inp_raio.get().replace(",", ".")
            txt_cap = self.inp_capacidade.get().replace(",", ".")

            if not txt_lanca or not txt_raio or not txt_cap:
                messagebox.showwarning("Atenção", "Preencha todos os campos do ponto.")
                return

            lanca_val = float(txt_lanca)
            raio_val = float(txt_raio)
            cap_val = float(txt_cap)

            if lanca_val <= 0 or lanca_val > 300:
                messagebox.showerror("Erro", "A lança deve ser entre 0.1 e 300 metros.")
                return
            if raio_val <= 0 or raio_val > 300:
                messagebox.showerror("Erro", "O raio deve ser entre 0.1 e 300 metros.")
                return
            if cap_val <= 0 or cap_val > 5000000:
                messagebox.showerror("Erro", "Capacidade irreal. O limite é de 5.000.000 kg.")
                return

            lanca = str(lanca_val)
            raio = str(raio_val)
            
            if lanca not in self.tabela_temp:
                self.tabela_temp[lanca] = {}
            
            self.tabela_temp[lanca][raio] = cap_val
            
            self.inp_raio.delete(0, 'end')
            self.inp_capacidade.delete(0, 'end')
            self.inp_raio.focus()
            
            self.atualizar_preview()
            
        except ValueError:
            messagebox.showerror("Erro", "Preencha Lança, Raio e Capacidade apenas com números.")

    def remover_ponto(self, lanca, raio):
        if lanca in self.tabela_temp and raio in self.tabela_temp[lanca]:
            del self.tabela_temp[lanca][raio]
            
            # Se a lança ficar vazia, remove ela também para não poluir a tela
            if not self.tabela_temp[lanca]:
                del self.tabela_temp[lanca]
                
            self.atualizar_preview()

    def salvar_novo(self):
        try:
            modelo = self.inp_modelo.get().strip()
            fab = self.inp_fab.get().strip()
            txt_cap = self.inp_cap.get().strip()
            
            if not modelo or not fab or not txt_cap:
                messagebox.showwarning("Atenção", "Modelo, Fabricante e Capacidade Máxima são obrigatórios.")
                return

            txt_cap_limpo = txt_cap.replace(".", "").replace(",", ".")
            
            try:
                cap = float(txt_cap_limpo)
            except ValueError:
                messagebox.showerror("Erro", "A capacidade máxima deve conter apenas números.")
                return

            if cap <= 0:
                messagebox.showerror("Erro", "A capacidade do guindaste deve ser maior que zero.")
                return
                
            if cap > 5000000:
                messagebox.showerror("Erro", "Capacidade irreal! O limite do sistema é de 5.000.000 kg.")
                return
            
            if not self.tabela_temp:
                messagebox.showwarning("Atenção", "Adicione ao menos um ponto de Lança/Raio.")
                return
            
            self.repo.salvar_guindaste(modelo, fab, cap, self.tabela_temp)
            
            self.inp_modelo.delete(0, 'end')
            self.inp_fab.delete(0, 'end')
            self.inp_cap.delete(0, 'end')
            self.inp_lanca.delete(0, 'end')
            self.inp_raio.delete(0, 'end')
            self.inp_capacidade.delete(0, 'end')
            
            self.tabela_temp = {}
            self.atualizar_preview()
            self.carregar_lista()
            
            messagebox.showinfo("Sucesso", f"Guindaste {fab} {modelo} salvo com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro Interno", f"Ocorreu um erro inesperado:\n{str(e)}")
            
    def atualizar_preview(self):
        # Limpa os widgets atuais do grid CRUD
        for widget in self.frame_pontos_lista.winfo_children():
            widget.destroy()
        
        if not self.tabela_temp:
            ctk.CTkLabel(self.frame_pontos_lista, text="Nenhum ponto adicionado ainda.", text_color="gray").pack(pady=20)
            return

        # Reconstrói a lista linha por linha
        for lanca, raios in sorted(self.tabela_temp.items(), key=lambda x: float(x[0])):
            for raio, cap in sorted(raios.items(), key=lambda x: float(x[0])):
                linha = ctk.CTkFrame(self.frame_pontos_lista, fg_color="#3b3b3b")
                linha.pack(fill="x", pady=2, padx=2)

                texto = f"Lança: {lanca} m  |  Raio: {raio} m  ➔  {cap:,.0f} kg".replace(",", ".")
                lbl = ctk.CTkLabel(linha, text=texto, font=("Roboto", 13))
                lbl.pack(side="left", padx=10, pady=5)

                btn_del = ctk.CTkButton(linha, text="X", width=28, height=28, 
                                        fg_color="#E74C3C", hover_color="#C0392B",
                                        command=lambda l=lanca, r=raio: self.remover_ponto(l, r))
                btn_del.pack(side="right", padx=5, pady=5)

    # LISTA E EXCLUSÃO
    def carregar_lista(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        guindastes = self.repo.listar_todos() 
        self.lbl_contagem.configure(text=f"{len(guindastes)} guindaste(s)")

        if not guindastes:
            ctk.CTkLabel(self.frame_lista, text="Nenhum guindaste cadastrado.", text_color="gray").pack(pady=20)
            return

        guindastes = sorted(guindastes, key=self._chave_ordenacao, reverse=self.ordem_decrescente)

        for g in guindastes:
            id_g, modelo, fab, cap, data = g[0], g[1], g[2], g[3], g[4]
            card = ctk.CTkFrame(self.frame_lista, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=5)

            textos = ctk.CTkFrame(card, fg_color="transparent")
            textos.pack(side="left", padx=10, pady=10)
            
            ctk.CTkLabel(textos, text=f"{fab} {modelo} | {cap:,.0f} kg".replace(",", "."), 
                         font=("Roboto", 14, "bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(textos, text=f"Cadastrado em: {self._formatar_data(data)}", 
                         font=("Roboto", 12), text_color="gray", anchor="w").pack(anchor="w")

            btn_del = ctk.CTkButton(card, text="Excluir", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                                    command=lambda i=id_g: self.deletar(i))
            btn_del.pack(side="right", padx=10, pady=10)

    def deletar(self, id_guindaste):
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este guindaste?"):
            self.repo.deletar_guindaste(id_guindaste)
            self.carregar_lista()