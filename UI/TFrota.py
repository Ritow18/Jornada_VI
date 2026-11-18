import customtkinter as ctk
from tkinter import ttk, messagebox
import json
from datetime import datetime
from DBs.rep import BancoDeDados, RepGuindaste, RepTemplateCarga

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
        self.grid_rowconfigure(2, weight=5) 

        self.db = BancoDeDados()
        self.repo = RepGuindaste(self.db)
        self.repo_template = RepTemplateCarga(self.db)

        self.tabela_temp = {}
        self.criterio = "Data/Hora"
        self.ordem_decrescente = CRITERIOS[self.criterio][0]

        # ESTILIZAÇÃO DO TREEVIEW PARA MODO ESCURO  
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2b2b2b",
                        bordercolor="#343638",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#3498DB')])
        style.configure("Treeview.Heading",
                        background="#3b3b3b",
                        foreground="white",
                        relief="flat",
                        font=("Roboto", 11, "bold"))
        style.map("Treeview.Heading", background=[('active', '#3498DB')])

        # TÍTULO  
        self.titulo = ctk.CTkLabel(self, text="Gestão de Guindastes", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, pady=(10, 5))

        frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        frame_topo.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        frame_topo.grid_columnconfigure(0, weight=2) 
        frame_topo.grid_columnconfigure(1, weight=4) 
        frame_topo.grid_columnconfigure(2, weight=4) 
        frame_topo.grid_rowconfigure(0, weight=1)

        self.frame_cadastro = ctk.CTkFrame(frame_topo)
        self.frame_cadastro.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        ctk.CTkLabel(self.frame_cadastro, text="1. Novo Equipamento", font=("Roboto", 16, "bold")).pack(pady=(15, 15))

        self.inp_modelo = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Modelo (Ex: LTM 1100)")
        self.inp_modelo.pack(fill="x", padx=20, pady=6)

        self.inp_fab = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Fabricante (Ex: Liebherr)")
        self.inp_fab.pack(fill="x", padx=20, pady=6)

        self.inp_cap = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Capacidade Máxima (kg)")
        self.inp_cap.pack(fill="x", padx=20, pady=6)
        
        self.btn_salvar = ctk.CTkButton(self.frame_cadastro, text="Salvar Guindaste", height=40,
                                        fg_color="#2ECC71", hover_color="#27AE60", command=self.salvar_novo_guindaste)
        self.btn_salvar.pack(fill="x", padx=20, pady=(25, 5))
        
        ctk.CTkLabel(self.frame_cadastro, text="(Selecione o molde na tabela ao lado)", 
                     font=("Roboto", 11), text_color="gray").pack()

        frame_moldes = ctk.CTkFrame(frame_topo, fg_color="#333333")
        frame_moldes.grid(row=0, column=1, padx=(5, 5), sticky="nsew")

        ctk.CTkLabel(frame_moldes, text="2. Selecione a Tabela de Carga", font=("Roboto", 16, "bold")).pack(pady=(15, 5))

        frame_tree = ctk.CTkFrame(frame_moldes, fg_color="transparent")
        frame_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree_templates = ttk.Treeview(frame_tree, columns=("id", "nome", "qtd", "data", "json"), show="headings")
        self.tree_templates.heading("nome", text="Nome do Template")
        self.tree_templates.heading("qtd", text="Pontos")
        self.tree_templates.heading("data", text="Criado em")
        self.tree_templates.column("id", width=0, stretch=False)
        self.tree_templates.column("json", width=0, stretch=False)
        self.tree_templates.column("nome", width=140, anchor="w")
        self.tree_templates.column("qtd", width=60, anchor="center")
        self.tree_templates.column("data", width=90, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_templates.yview)
        self.tree_templates.configure(yscroll=scrollbar.set)
        self.tree_templates.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        botoes_molde = ctk.CTkFrame(frame_moldes, fg_color="transparent")
        botoes_molde.pack(pady=(5, 15))
        
        ctk.CTkButton(botoes_molde, text="Ver Detalhes", width=110, fg_color="#3498DB", hover_color="#2980B9", 
                      command=self.visualizar_molde_selecionado).pack(side="left", padx=5)
        ctk.CTkButton(botoes_molde, text="Apagar Molde", width=110, fg_color="#E74C3C", hover_color="#C0392B", 
                      command=self.deletar_template).pack(side="left", padx=5)
   
        frame_construtor = ctk.CTkFrame(frame_topo, fg_color="#2b2b2b")
        frame_construtor.grid(row=0, column=2, padx=(5, 0), sticky="nsew")

        ctk.CTkLabel(frame_construtor, text="Criar um Novo Molde", font=("Roboto", 16, "bold")).pack(pady=(15, 5))

        self.inp_nome_template = ctk.CTkEntry(frame_construtor, placeholder_text="Nome (Ex: Padrão LTM 1100)")
        self.inp_nome_template.pack(fill="x", padx=15, pady=5)

        frame_pontos = ctk.CTkFrame(frame_construtor, fg_color="transparent")
        frame_pontos.pack(fill="x", padx=15, pady=5)
        frame_pontos.grid_columnconfigure((0,1,2), weight=1)

        self.inp_lanca = ctk.CTkEntry(frame_pontos, placeholder_text="Lança (m)")
        self.inp_lanca.grid(row=0, column=0, padx=2, sticky="ew")
        self.inp_raio = ctk.CTkEntry(frame_pontos, placeholder_text="Raio (m)")
        self.inp_raio.grid(row=0, column=1, padx=2, sticky="ew")
        self.inp_capacidade = ctk.CTkEntry(frame_pontos, placeholder_text="Cap. (kg)")
        self.inp_capacidade.grid(row=0, column=2, padx=2, sticky="ew")

        ctk.CTkButton(frame_pontos, text="+", width=40, fg_color="#3498DB", hover_color="#2980B9", 
                      command=self.adicionar_ponto).grid(row=0, column=3, padx=2)

        self.frame_pontos_lista = ctk.CTkScrollableFrame(frame_construtor, fg_color="#1e1e1e", label_text="Pontos Temporários")
        self.frame_pontos_lista.pack(fill="both", expand=True, padx=15, pady=(5, 5))
        
        ctk.CTkButton(frame_construtor, text="Guardar Molde na Base", fg_color="#F39C12", hover_color="#D68910", 
                      command=self.salvar_template_db).pack(pady=(5, 15))

        frame_lista_area = ctk.CTkFrame(self, fg_color="transparent")
        frame_lista_area.grid(row=2, column=0, padx=20, pady=(5, 15), sticky="nsew")
        frame_lista_area.grid_columnconfigure(0, weight=1)
        frame_lista_area.grid_rowconfigure(1, weight=1)

        barra = ctk.CTkFrame(frame_lista_area, fg_color="transparent")
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ctk.CTkLabel(barra, text="Ordenar por:").pack(side="left", padx=(5, 8))
        self.seg_criterio = ctk.CTkSegmentedButton(barra, values=list(CRITERIOS.keys()), command=self.mudar_criterio)
        self.seg_criterio.set(self.criterio)
        self.seg_criterio.pack(side="left")
        self.btn_ordem = ctk.CTkButton(barra, text="", width=150, command=self.alternar_ordem)
        self.btn_ordem.pack(side="left", padx=10)
        self.lbl_contagem = ctk.CTkLabel(barra, text="", font=("Roboto", 12))
        self.lbl_contagem.pack(side="right", padx=5)

        self.frame_lista = ctk.CTkScrollableFrame(frame_lista_area, label_text="Frota Cadastrada")
        self.frame_lista.grid(row=1, column=0, sticky="nsew")

        self.atualizar_botao_ordem()
        self.carregar_templates()
        self.carregar_lista()
        self.atualizar_preview()

    #      MODAL VISUALIZADOR DE CARGAS     
    def abrir_modal_carga(self, titulo, json_str):
        try:
            tabela = json.loads(json_str)
        except:
            tabela = {}
            
        top = ctk.CTkToplevel(self)
        top.title(f"Visualizando: {titulo}")
        top.geometry("450x450")
        top.transient(self.winfo_toplevel()) 
        top.grab_set() 

        ctk.CTkLabel(top, text=f"Tabela de Carga:\n{titulo}", font=("Roboto", 16, "bold")).pack(pady=(15, 10))
        
        frame_tree = ctk.CTkFrame(top, fg_color="transparent")
        frame_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        tree = ttk.Treeview(frame_tree, columns=("lanca", "raio", "cap"), show="headings")
        tree.heading("lanca", text="Lança (m)")
        tree.heading("raio", text="Raio (m)")
        tree.heading("cap", text="Capacidade Máx (kg)")
        
        tree.column("lanca", width=100, anchor="center")
        tree.column("raio", width=100, anchor="center")
        tree.column("cap", width=120, anchor="center")
        
        scroll = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        for lanca in sorted(tabela.keys(), key=float):
            for raio in sorted(tabela[lanca].keys(), key=float):
                cap = tabela[lanca][raio]
                tree.insert("", "end", values=(lanca, raio, f"{cap:,.0f}".replace(",", ".")))

    def visualizar_molde_selecionado(self):
        selecionado = self.tree_templates.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um molde na tabela para visualizar.")
            return
        item = self.tree_templates.item(selecionado[0])
        nome = item['values'][1]
        json_str = item['values'][4]
        self.abrir_modal_carga(f"Molde - {nome}", json_str)

    # LÓGICA DE TEMPLATES
    def carregar_templates(self):
        for item in self.tree_templates.get_children():
            self.tree_templates.delete(item)
            
        templates = self.repo_template.listar_todos()
        for t in templates:
            data_fmt = self._formatar_data(t[2])
            json_str = t[3]
            try:
                tabela_dict = json.loads(json_str)
                qtd_pontos = sum(len(raios) for raios in tabela_dict.values())
            except:
                qtd_pontos = 0
            self.tree_templates.insert("", "end", values=(t[0], t[1], str(qtd_pontos), data_fmt, json_str))

    def deletar_template(self):
        selecionado = self.tree_templates.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um molde na tabela do meio para apagar.")
            return
        item = self.tree_templates.item(selecionado[0])
        id_template, nome = item['values'][0], item['values'][1]
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir o molde '{nome}'?"):
            self.repo_template.deletar_template(id_template)
            self.carregar_templates()

    def salvar_template_db(self):
        nome = self.inp_nome_template.get().strip()
        if not nome or not self.tabela_temp:
            messagebox.showwarning("Atenção", "Dê um nome ao molde e adicione pelo menos um ponto.")
            return
        try:
            self.repo_template.salvar_template(nome, self.tabela_temp)
            self.inp_nome_template.delete(0, 'end')
            self.tabela_temp = {}
            self.atualizar_preview()
            self.carregar_templates()
            messagebox.showinfo("Sucesso", f"Molde '{nome}' guardado com sucesso!")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                messagebox.showerror("Erro", "Já existe um molde com esse nome.")
            else:
                messagebox.showerror("Erro Interno", str(e))

    #      CONSTRUTOR DE CARGA     
    def adicionar_ponto(self):
        try:
            lanca_val = float(self.inp_lanca.get().replace(",", "."))
            raio_val = float(self.inp_raio.get().replace(",", "."))
            cap_val = float(self.inp_capacidade.get().replace(",", "."))

            if lanca_val <= 0 or lanca_val > 300 or raio_val <= 0 or raio_val > 300:
                messagebox.showerror("Erro", "Lança e Raio devem ser entre 0.1 e 300 metros.")
                return
            if cap_val <= 0 or cap_val > 5000000:
                messagebox.showerror("Erro", "Capacidade inválida (máx 5.000.000 kg).")
                return
            
            lanca, raio = str(lanca_val), str(raio_val)
            if lanca not in self.tabela_temp:
                self.tabela_temp[lanca] = {}
            self.tabela_temp[lanca][raio] = cap_val
            
            # Aqui, como conversamos, não apagamos a lança
            self.inp_raio.delete(0, 'end')
            self.inp_capacidade.delete(0, 'end')
            self.inp_raio.focus()
            self.atualizar_preview()
        except ValueError:
            messagebox.showerror("Erro", "Preencha Lança, Raio e Capacidade apenas com números.")

    def remover_ponto(self, lanca, raio):
        if lanca in self.tabela_temp and raio in self.tabela_temp[lanca]:
            del self.tabela_temp[lanca][raio]
            if not self.tabela_temp[lanca]:
                del self.tabela_temp[lanca]
            self.atualizar_preview()

    def atualizar_preview(self):
        for widget in self.frame_pontos_lista.winfo_children():
            widget.destroy()
        if not self.tabela_temp:
            ctk.CTkLabel(self.frame_pontos_lista, text="Molde vazio.", text_color="gray").pack(pady=20)
            return

        for lanca, raios in sorted(self.tabela_temp.items(), key=lambda x: float(x[0])):
            for raio, cap in sorted(raios.items(), key=lambda x: float(x[0])):
                linha = ctk.CTkFrame(self.frame_pontos_lista, fg_color="#3b3b3b", height=30)
                linha.pack(fill="x", pady=2, padx=2)
                texto = f"L: {lanca} | R: {raio} ➔ {cap:,.0f} kg".replace(",", ".")
                ctk.CTkLabel(linha, text=texto, font=("Roboto", 12)).pack(side="left", padx=10)
                ctk.CTkButton(linha, text="X", width=20, height=20, fg_color="#E74C3C", hover_color="#C0392B",
                              command=lambda l=lanca, r=raio: self.remover_ponto(l, r)).pack(side="right", padx=5)

    #      SALVAR GUINDASTE     
    def salvar_novo_guindaste(self):
        modelo = self.inp_modelo.get().strip()
        fab = self.inp_fab.get().strip()
        txt_cap = self.inp_cap.get().strip()
        selecionado = self.tree_templates.selection()
        
        if not modelo or not fab or not txt_cap:
            messagebox.showwarning("Atenção", "Preencha Modelo, Fabricante e Capacidade.")
            return
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione uma Tabela de Carga (Molde) na lista para vincular.")
            return

        try: 
            cap = float(txt_cap.replace(".", "").replace(",", "."))
        except: 
            return messagebox.showerror("Erro", "Capacidade deve conter apenas números.")

        item = self.tree_templates.item(selecionado[0])
        tabela_carga = json.loads(item['values'][4])
        
        #   NOVO AVISO DE SEGURANÇA (PERGUNTA)  
        maior_peso_do_molde = 0
        for lanca, raios in tabela_carga.items():
            for raio, peso in raios.items():
                if peso > maior_peso_do_molde:
                    maior_peso_do_molde = peso
                    
        if maior_peso_do_molde > cap:
            resposta = messagebox.askyesno(
                "Aviso de Inconsistência", 
                f"O molde selecionado contém cargas de até {maior_peso_do_molde:,.0f} kg.\n"
                f"Isso é maior que a capacidade nominal digitada ({cap:,.0f} kg)!\n\n"
                "Você tem certeza que gostaria de cadastrá-lo mesmo assim?"
            )
            # Se o usuário clicar em "Não", a função para aqui
            if not resposta:
                return
        try:
            self.repo.salvar_guindaste(modelo, fab, cap, tabela_carga)
            self.inp_modelo.delete(0, 'end')
            self.inp_fab.delete(0, 'end')
            self.inp_cap.delete(0, 'end')
            self.tree_templates.selection_remove(selecionado[0])
            self.carregar_lista()
            messagebox.showinfo("Sucesso", f"Guindaste {fab} {modelo} salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    #      ORDENAÇÃO E LISTAGEM DA FROTA     
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
        self.btn_ordem.configure(text=CRITERIOS[self.criterio][2] if self.ordem_decrescente else CRITERIOS[self.criterio][1])

    def _chave_ordenacao(self, g):
        # g[4] é o JSON, g[5] é a Data no rep_2.py
        id_g, modelo, fab, cap, data = g[0], (g[1] or "").lower(), (g[2] or "").lower(), g[3] or 0, g[5] or ""
        if self.criterio == "Modelo": return (modelo, fab, id_g)
        if self.criterio == "Fabricante": return (fab, modelo, id_g)
        if self.criterio == "Capacidade": return (cap, modelo, id_g)
        return (data, id_g) 

    @staticmethod
    def _formatar_data(valor):
        if not valor: return "Sem data"
        try: return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except: return str(valor)

    def carregar_lista(self):
        for widget in self.frame_lista.winfo_children(): widget.destroy()

        guindastes = self.repo.listar_todos() 
        self.lbl_contagem.configure(text=f"{len(guindastes)} guindaste(s)")
        if not guindastes:
            ctk.CTkLabel(self.frame_lista, text="Nenhum guindaste cadastrado.", text_color="gray").pack(pady=20)
            return

        for g in sorted(guindastes, key=self._chave_ordenacao, reverse=self.ordem_decrescente):
            # Ajustado para a ordem exata do rep_2.py
            id_g, modelo, fab, cap, json_str, data = g[0], g[1], g[2], g[3], g[4], g[5]
            
            card = ctk.CTkFrame(self.frame_lista, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=5)

            textos = ctk.CTkFrame(card, fg_color="transparent")
            textos.pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(textos, text=f"{fab} {modelo} | {cap:,.0f} kg".replace(",", "."), font=("Roboto", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(textos, text=f"Cadastrado em: {self._formatar_data(data)}", font=("Roboto", 12), text_color="gray").pack(anchor="w")

            botoes = ctk.CTkFrame(card, fg_color="transparent")
            botoes.pack(side="right", padx=10, pady=10)

            ctk.CTkButton(botoes, text="Ver Carga", width=80, fg_color="#3498DB", hover_color="#2980B9",
                          command=lambda n=f"{fab} {modelo}", j=json_str: self.abrir_modal_carga(n, j)).pack(side="left", padx=5)
            ctk.CTkButton(botoes, text="Excluir", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                          command=lambda i=id_g: self.deletar(i)).pack(side="left", padx=5)

    def deletar(self, id_guindaste):
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este guindaste da frota?"):
            self.repo.deletar_guindaste(id_guindaste)
            self.carregar_lista()

    def atualizar_dados(self):
        self.carregar_lista()
        self.carregar_templates()