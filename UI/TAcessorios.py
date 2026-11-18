import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from DBs.rep import BancoDeDados, RepAcessorio


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
        self.linhas_lote = []

        self.titulo = ctk.CTkLabel(self, text="Gestão de Acessórios", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, pady=(20, 10))

        # ================= TOPO: CADASTRO EM LOTE =================
        self.frame_cadastro = ctk.CTkFrame(self)
        self.frame_cadastro.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(self.frame_cadastro, text="Cadastro em Lote", font=("Roboto", 18, "bold")).pack(pady=(10, 5))

        self.scroll_lote = ctk.CTkScrollableFrame(self.frame_cadastro, height=180, fg_color="transparent")
        self.scroll_lote.pack(fill="x", padx=10, pady=5)

        # Cabeçalho do lote
        cabecalho = ctk.CTkFrame(self.scroll_lote, fg_color="#2a2a2a", corner_radius=8, height=35)
        cabecalho.pack(fill="x", pady=(0, 5))
        
        # Grid para o cabeçalho (usando a mesma proporção das linhas)
        cabecalho.grid_columnconfigure((0,1,2,3), weight=1)
        cabecalho.grid_columnconfigure(4, weight=0)
        
        ctk.CTkLabel(cabecalho, text="Tipo de Acessório", anchor="w", font=("Roboto", 13, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkLabel(cabecalho, text="Capacidade (kg)", anchor="w", font=("Roboto", 13, "bold")).grid(row=0, column=1, padx=5, sticky="w")
        ctk.CTkLabel(cabecalho, text="Peso Unit. (kg)", anchor="w", font=("Roboto", 13, "bold")).grid(row=0, column=2, padx=5, sticky="w")
        ctk.CTkLabel(cabecalho, text="Desgaste (%)", anchor="w", font=("Roboto", 13, "bold")).grid(row=0, column=3, padx=5, sticky="w")

        rodape = ctk.CTkFrame(self.frame_cadastro, fg_color="transparent")
        rodape.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(rodape, text="+ Adicionar Linha", width=140, fg_color="#3498DB", hover_color="#2980B9", 
                      command=self.adicionar_linha).pack(side="left")
                      
        ctk.CTkButton(rodape, text="💾 Salvar Acessórios", width=140, fg_color="#2ECC71", hover_color="#27AE60", 
                      command=self.salvar_lote).pack(side="right")

        self.adicionar_linha()

        # ================= BAIXO: ABAS POR CATEGORIA (Cards Modernos) =================
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

    def adicionar_linha(self):
        linha_frame = ctk.CTkFrame(self.scroll_lote, fg_color="#1a1a1a", border_width=1, border_color="#444")
        linha_frame.pack(fill="x", pady=2)
        linha_frame.grid_columnconfigure((0,1,2,3), weight=1)
        linha_frame.grid_columnconfigure(4, weight=0)
        
        combo_tipo = ctk.CTkComboBox(linha_frame, values=list(self.mapa_tipos.keys()), state="readonly")
        combo_tipo.set(list(self.mapa_tipos.keys())[0])
        combo_tipo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        inp_capacidade = ctk.CTkEntry(linha_frame, placeholder_text="Ex: 5000")
        inp_capacidade.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        inp_peso = ctk.CTkEntry(linha_frame, placeholder_text="Ex: 12.5")
        inp_peso.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        inp_desgaste = ctk.CTkEntry(linha_frame, placeholder_text="Ex: 0")
        inp_desgaste.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        dados_linha = {
            "frame": linha_frame,
            "tipo": combo_tipo,
            "capacidade": inp_capacidade,
            "peso": inp_peso,
            "desgaste": inp_desgaste
        }
        self.linhas_lote.append(dados_linha)
        
        def remover():
            linha_frame.destroy()
            self.linhas_lote.remove(dados_linha)
            
        ctk.CTkButton(linha_frame, text="X", width=30, fg_color="#E74C3C", hover_color="#C0392B", 
                      command=remover).grid(row=0, column=4, padx=5, pady=5)

    def salvar_lote(self):
        if not self.linhas_lote:
            messagebox.showwarning("Aviso", "Não há nenhuma linha para salvar.")
            return

        sucessos = 0
        erros_validacao = 0

        try:
            for linha in self.linhas_lote:
                capacidade_txt = linha["capacidade"].get().strip()
                if not capacidade_txt: 
                    continue

                tipo_nome = linha["tipo"].get()
                tipo_id = self.mapa_tipos.get(tipo_nome)
                
                txt_desgaste = linha["desgaste"].get().strip().replace(",", ".") or "0.0"
                txt_peso = linha["peso"].get().strip().replace(",", ".") or "0.0"
                
                capac = float(capacidade_txt.replace(",", "."))
                desgaste = float(txt_desgaste)
                peso = float(txt_peso)

                # Travas de segurança (Ignora a linha se errada)
                if not (0 <= desgaste <= 100) or not (0 < capac <= 1000000) or not (0 <= peso <= 50000):
                    erros_validacao += 1
                    continue

                codigo = self.repo.gerar_codigo_automatico(tipo_nome)
                self.repo.salvar_acessorio(tipo_id, codigo, capac, desgaste, peso)
                sucessos += 1

            if sucessos > 0:
                msg = f"{sucessos} acessório(s) salvo(s) com sucesso!"
                if erros_validacao > 0:
                    msg += f"\n{erros_validacao} linha(s) ignorada(s) por valores irreais (engenharia)."
                
                messagebox.showinfo("Sucesso", msg)
                
                # Limpa e reseta
                for linha in self.linhas_lote:
                    linha["frame"].destroy()
                self.linhas_lote.clear()
                self.adicionar_linha()
                self.carregar_lista()
            elif erros_validacao > 0:
                messagebox.showwarning("Aviso", "Nenhuma linha salva. Verifique os limites de engenharia informados.")
            else:
                messagebox.showwarning("Aviso", "Nenhuma linha válida preenchida.")

        except ValueError:
            messagebox.showerror("Erro de Digitação", "Preencha Capacidade, Desgaste e Peso apenas com números.")
        except Exception as e:
            messagebox.showerror("Erro Interno", f"Falha ao salvar:\n{str(e)}")

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
                ctk.CTkLabel(lista, text="Nenhum acessório cadastrado.", text_color="#aaaaaa").pack(pady=20)
                continue

            for a in itens:
                self._criar_card(lista, a, mostrar_tipo=(nome == "Todos"))

    def _criar_card(self, parent, a, mostrar_tipo):
        id_a, tipo, cod, capac, desgaste, data, peso = a[0], a[1], a[2], a[3], a[4], a[5], a[6]

        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", border_width=1, border_color="#444")
        card.pack(fill="x", pady=5, padx=5)
        
        # Grid para travar o botão na direita
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        cabecalho = f"[{tipo or 'Sem tipo'}] {cod}" if mostrar_tipo else cod
        
        # Título do Card
        ctk.CTkLabel(info_frame, text=cabecalho, font=("Roboto", 14, "bold"), anchor="w").pack(fill="x")
        
        # Subtítulo (Cinza Claro)
        detalhes = f"Capacidade: {capac} kg   |   Desgaste: {desgaste}%   |   Peso: {peso} kg"
        ctk.CTkLabel(info_frame, text=detalhes, font=("Roboto", 12), text_color="#cccccc", anchor="w").pack(fill="x")
        
        # Rodapé pequeno (Data)
        ctk.CTkLabel(info_frame, text=f"Cadastrado em: {self._formatar_data(data)}", 
                     font=("Roboto", 10), text_color="#888888", anchor="w").pack(fill="x")

        # Botão de Excluir isolado
        btn_del = ctk.CTkButton(card, text="Excluir", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                                command=lambda i=id_a: self.deletar(i))
        btn_del.grid(row=0, column=1, padx=10, pady=10)

    def deletar(self, id_acessorio):
        self.repo.deletar_acessorio(id_acessorio)
        self.carregar_lista()

    def atualizar_dados(self):
        self.carregar_lista()