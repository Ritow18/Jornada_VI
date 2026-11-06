import customtkinter as ctk
from datetime import datetime
from DBs.rep import BancoDeDados, RepAcessorio
from tkinter import messagebox


class TelaAcessorios(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.db = BancoDeDados()
        self.repo = RepAcessorio(self.db)

        self.cursor = self.db.cursor
        self.cursor.execute("SELECT ID_tipo_acessorio, nome_tipo FROM Tipo_acessorio ORDER BY ID_tipo_acessorio")
        tipos = self.cursor.fetchall()
        self.mapa_tipos = {t[1]: t[0] for t in tipos}

        self.titulo = ctk.CTkLabel(self, text="Gestão de Acessórios", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, pady=(20, 10))

        # ================= TOPO: CADASTRO =================
        self.frame_cadastro = ctk.CTkFrame(self)
        self.frame_cadastro.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(self.frame_cadastro, text="Novo Acessório", font=("Roboto", 18, "bold")).pack(pady=(10, 5))

        frame_campos = ctk.CTkFrame(self.frame_cadastro, fg_color="transparent")
        frame_campos.pack(pady=(0, 12))

        ctk.CTkLabel(frame_campos, text="Tipo de Acessório").grid(row=0, column=0, padx=5, sticky="w")
        self.combo_tipo = ctk.CTkComboBox(frame_campos, width=150, values=list(self.mapa_tipos.keys()))
        self.combo_tipo.grid(row=1, column=0, padx=5, pady=(0, 5))

        ctk.CTkLabel(frame_campos, text="Código Identificador").grid(row=0, column=1, padx=5, sticky="w")
        self.inp_cod = ctk.CTkEntry(frame_campos, placeholder_text="Ex: CIN-001", width=120)
        self.inp_cod.grid(row=1, column=1, padx=5, pady=(0, 5))

        # AJUSTE: Rótulo de Capacidade mudado para kg
        ctk.CTkLabel(frame_campos, text="Capacidade (kg)").grid(row=0, column=2, padx=5, sticky="w")
        self.inp_capac = ctk.CTkEntry(frame_campos, placeholder_text="Ex: 5000", width=90)
        self.inp_capac.grid(row=1, column=2, padx=5, pady=(0, 5))

        ctk.CTkLabel(frame_campos, text="Desgaste (%)").grid(row=0, column=3, padx=5, sticky="w")
        self.inp_desgaste = ctk.CTkEntry(frame_campos, placeholder_text="Ex: 0.0", width=90)
        self.inp_desgaste.grid(row=1, column=3, padx=5, pady=(0, 5))

        ctk.CTkLabel(frame_campos, text="Peso (kg)").grid(row=0, column=4, padx=5, sticky="w")
        self.inp_peso = ctk.CTkEntry(frame_campos, placeholder_text="Ex: 12.5", width=90)
        self.inp_peso.grid(row=1, column=4, padx=5, pady=(0, 5))

        self.btn_salvar = ctk.CTkButton(frame_campos, text="Salvar Acessório", width=120, command=self.salvar_novo,
                                        fg_color="#2ECC71", hover_color="#27AE60")
        self.btn_salvar.grid(row=1, column=5, padx=(10, 5), pady=(0, 5))

        # ================= BAIXO: ABAS POR CATEGORIA =================
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="nsew")

        self.abas = {}
        for nome in ["Todos"] + list(self.mapa_tipos.keys()):
            aba = self.tabview.add(nome)
            aba.grid_columnconfigure(0, weight=1)
            aba.grid_rowconfigure(1, weight=1)

            lbl_contagem = ctk.CTkLabel(aba, text="", anchor="w", font=("Roboto", 12))
            lbl_contagem.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="w")

            lista = ctk.CTkScrollableFrame(aba)
            lista.grid(row=1, column=0, sticky="nsew")

            self.abas[nome] = (lbl_contagem, lista)

        self.carregar_lista()

    @staticmethod
    def _formatar_data(valor):
        if not valor: return "data não registrada"
        try: return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except ValueError: return str(valor)

    def carregar_lista(self):
        acessorios = self.repo.listar_todos()

        for nome, (lbl_contagem, lista) in self.abas.items():
            for widget in lista.winfo_children():
                widget.destroy()

            if nome == "Todos": itens = acessorios
            else: itens = [a for a in acessorios if a[1] == nome]

            lbl_contagem.configure(text=f"{len(itens)} item(ns) • mais recentes primeiro")

            if not itens:
                ctk.CTkLabel(lista, text="Nenhum acessório cadastrado.").pack(pady=20)
                continue

            for a in itens:
                self._criar_card(lista, a, mostrar_tipo=(nome == "Todos"))

    def _criar_card(self, parent, a, mostrar_tipo):
        id_a, tipo, cod, capac, desgaste, data, peso = a[0], a[1], a[2], a[3], a[4], a[5], a[6]

        card = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        card.pack(fill="x", pady=5, padx=5)

        cabecalho = f"[{tipo or 'Sem tipo'}] {cod}" if mostrar_tipo else cod
        
        info = (f"{cabecalho}\n"
                f"Capacidade: {capac} kg | Desgaste: {desgaste}% | Peso: {peso} kg\n"
                f"Cadastrado em: {self._formatar_data(data)}")
        
        ctk.CTkLabel(card, text=info, font=("Roboto", 12), justify="left").pack(side="left", padx=10, pady=10)

        btn_del = ctk.CTkButton(card, text="Excluir", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                                command=lambda i=id_a: self.deletar(i))
        btn_del.pack(side="right", padx=10, pady=10)

    def salvar_novo(self):
        try:
            tipo_nome = self.combo_tipo.get()
            tipo_id = self.mapa_tipos.get(tipo_nome)
            cod = self.inp_cod.get().strip()
            
            # Tratamento de vírgula e fallback para zero
            txt_capac = self.inp_capac.get().replace(",", ".")
            txt_desgaste = self.inp_desgaste.get().replace(",", ".") or "0.0"
            txt_peso = self.inp_peso.get().replace(",", ".") or "0.0"

            if not cod or not txt_capac:
                messagebox.showwarning("Atenção", "Código e Capacidade são obrigatórios.")
                return

            capac = float(txt_capac)
            desgaste = float(txt_desgaste)
            peso = float(txt_peso)

            # TRAVAS DE SEGURANÇA COM POP-UP
            if desgaste < 0 or desgaste > 100:
                messagebox.showerror("Erro de Validação", "O desgaste deve ser entre 0% e 100%.")
                return
            if capac <= 0 or capac > 1000000:
                messagebox.showerror("Erro de Engenharia", "A capacidade do acessório deve ser entre 1 kg e 1.000.000 kg (1.000 Toneladas).")
                return
            if peso < 0 or peso > 50000:
                messagebox.showerror("Erro de Engenharia", "O peso do acessório está irreal. Limite de 50.000 kg.")
                return

            if tipo_id and cod:
                self.repo.salvar_acessorio(tipo_id, cod, capac, desgaste, peso)
                self.inp_cod.delete(0, 'end')
                self.inp_capac.delete(0, 'end')
                self.inp_desgaste.delete(0, 'end')
                self.inp_peso.delete(0, 'end')
                self.carregar_lista()
                
                messagebox.showinfo("Sucesso", f"Acessório {cod} salvo com sucesso!")
                
        except ValueError:
            messagebox.showerror("Erro de Digitação", "Preencha Capacidade, Desgaste e Peso apenas com números.")
        except Exception as e:
            messagebox.showerror("Erro Interno", f"Ocorreu um erro ao salvar o acessório:\n{str(e)}")

    def deletar(self, id_acessorio):
        self.repo.deletar_acessorio(id_acessorio)
        self.carregar_lista()