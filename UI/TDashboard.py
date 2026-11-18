import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import os
from fpdf import FPDF

from DBs.rep import BancoDeDados, RepGuindaste, RepAcessorio
from core.calculos import CalculadorRigging

class TelaOperacao(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Grid Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        
        self.db = BancoDeDados()
        self.repo_guindaste = RepGuindaste(self.db)
        self.repo_acessorio = RepAcessorio(self.db)
        
        # Puxa os dados
        self.lista_guindastes = self.repo_guindaste.listar_todos()
        self.lista_acessorios = self.repo_acessorio.listar_todos()
        
        # Mapa para o dropdown do simulador
        self.mapa_guindastes = {f"{g[2]} {g[1]}": g[0] for g in self.lista_guindastes}
        nomes_guindastes = list(self.mapa_guindastes.keys()) if self.mapa_guindastes else ["Nenhum guindaste cadastrado"]

        # --- CABEÇALHO ---
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(frame_header, text="Painel Geral e Simulação Rápida", font=("Roboto", 24, "bold")).pack(side="left")

        # ==========================================
        # LADO ESQUERDO: SIMULADOR (Cima) + HISTÓRICO (Baixo)
        # ==========================================
        self.frame_esquerda = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_esquerda.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20))
        self.frame_esquerda.grid_columnconfigure(0, weight=1)
        self.frame_esquerda.grid_rowconfigure(1, weight=1) # Faz o histórico expandir

        # --- 1. SIMULADOR (Mais compacto) ---
        self.frame_simulador = ctk.CTkFrame(self.frame_esquerda, fg_color="#2b2b2b", corner_radius=10)
        self.frame_simulador.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        ctk.CTkLabel(self.frame_simulador, text="Simulação Rápida", font=("Roboto", 16, "bold")).pack(pady=(10, 5))

        # Inputs mais próximos
        frame_sel_guindaste = ctk.CTkFrame(self.frame_simulador, fg_color="transparent")
        frame_sel_guindaste.pack(padx=15, pady=2, fill="x")
        self.combo_guindaste = ctk.CTkComboBox(frame_sel_guindaste, values=nomes_guindastes, height=28)
        self.combo_guindaste.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_ver_tabela = ctk.CTkButton(frame_sel_guindaste, text="Cargas", width=60, height=28, fg_color="#8E44AD", hover_color="#9B59B6", command=self.abrir_tabela_selecao)
        self.btn_ver_tabela.pack(side="right")

        self.input_lanca = ctk.CTkEntry(self.frame_simulador, placeholder_text="Lança (m) Ex: 30", height=28)
        self.input_lanca.pack(padx=15, pady=4, fill="x")

        self.input_raio = ctk.CTkEntry(self.frame_simulador, placeholder_text="Raio (m) Ex: 9", height=28)
        self.input_raio.pack(padx=15, pady=4, fill="x")

        self.input_carga = ctk.CTkEntry(self.frame_simulador, placeholder_text="Carga Total (kg) Ex: 23200", height=28)
        self.input_carga.pack(padx=15, pady=4, fill="x")

        self.btn_simular = ctk.CTkButton(self.frame_simulador, text="SIMULAR", height=32, fg_color="#3498DB", hover_color="#2980B9", command=self.executar_simulacao)
        self.btn_simular.pack(padx=15, fill="x", pady=8)

        # Área de Resultados Compacta
        self.frame_resultado = ctk.CTkFrame(self.frame_simulador, fg_color="#1e1e1e")
        self.lbl_capacidade = ctk.CTkLabel(self.frame_resultado, text="Capacidade: --", font=("Roboto", 12))
        self.lbl_capacidade.pack(pady=(5, 0))
        self.lbl_tu = ctk.CTkLabel(self.frame_resultado, text="TU: --", font=("Roboto", 12))
        self.lbl_tu.pack()
        self.lbl_status = ctk.CTkLabel(self.frame_resultado, text="STATUS", font=("Roboto", 14, "bold"))
        self.lbl_status.pack(pady=(0, 5))

        # --- 2. HISTÓRICO DE PLANOS (Novo Espaço Embaixo) ---
        self.frame_historico = ctk.CTkFrame(self.frame_esquerda, fg_color="#2b2b2b", corner_radius=10)
        self.frame_historico.grid(row=1, column=0, sticky="nsew")
        self.frame_historico.grid_rowconfigure(1, weight=1)
        self.frame_historico.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.frame_historico, text="Planos Salvos", font=("Roboto", 16, "bold")).grid(row=0, column=0, pady=(10, 5))
        
        self.lista_planos = ctk.CTkScrollableFrame(self.frame_historico, fg_color="transparent")
        self.lista_planos.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Chama a função 100ms após abrir a tela para evitar lag
        self.after(100, self.carregar_historico_planos)

        # ==========================================
        # LADO DIREITO: DASHBOARD E ESTATÍSTICAS
        # ==========================================
        self.frame_dash = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_dash.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))
        self.frame_dash.grid_rowconfigure(1, weight=1)
        self.frame_dash.grid_columnconfigure(0, weight=1)

        # -- CARDS DE RESUMO --
        frame_cards = ctk.CTkFrame(self.frame_dash, fg_color="transparent")
        frame_cards.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        frame_cards.grid_columnconfigure((0, 1), weight=1)

        card_guindastes = ctk.CTkFrame(frame_cards, fg_color="#34495E", corner_radius=8)
        card_guindastes.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(card_guindastes, text="Frota Cadastrada", font=("Roboto", 14), text_color="#BDC3C7").pack(pady=(15, 0))
        ctk.CTkLabel(card_guindastes, text=f"{len(self.lista_guindastes)} Equipamentos", font=("Roboto", 22, "bold")).pack(pady=(0, 15))

        card_acessorios = ctk.CTkFrame(frame_cards, fg_color="#34495E", corner_radius=8)
        card_acessorios.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(card_acessorios, text="Acessórios Ativos", font=("Roboto", 14), text_color="#BDC3C7").pack(pady=(15, 0))
        ctk.CTkLabel(card_acessorios, text=f"{len(self.lista_acessorios)} Itens", font=("Roboto", 22, "bold")).pack(pady=(0, 15))

        # -- LISTAS DE PRÉVIA --
        frame_listas = ctk.CTkFrame(self.frame_dash, fg_color="transparent")
        frame_listas.grid(row=1, column=0, sticky="nsew")
        frame_listas.grid_columnconfigure((0, 1), weight=1)
        frame_listas.grid_rowconfigure(0, weight=1)

        lista_frota = ctk.CTkScrollableFrame(frame_listas, label_text="Últimos Guindastes", fg_color="#2b2b2b")
        lista_frota.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        if not self.lista_guindastes:
            ctk.CTkLabel(lista_frota, text="Nenhum guindaste.", text_color="gray").pack(pady=20)
        else:
            for g in self.lista_guindastes[:10]: 
                item = ctk.CTkFrame(lista_frota, fg_color="#3b3b3b")
                item.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(item, text=f"{g[2]} {g[1]}", font=("Roboto", 13, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
                ctk.CTkLabel(item, text=f"Capacidade: {g[3]:,.0f} kg", font=("Roboto", 11)).pack(anchor="w", padx=10, pady=(0, 5))

        lista_acess = ctk.CTkScrollableFrame(frame_listas, label_text="Últimos Acessórios", fg_color="#2b2b2b")
        lista_acess.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        if not self.lista_acessorios:
            ctk.CTkLabel(lista_acess, text="Nenhum acessório.", text_color="gray").pack(pady=20)
        else:
            for a in self.lista_acessorios[:10]: 
                item = ctk.CTkFrame(lista_acess, fg_color="#3b3b3b")
                item.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(item, text=f"{a[1]} ({a[2]})", font=("Roboto", 13, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
                ctk.CTkLabel(item, text=f"Carga: {a[3]:,.0f} kg", font=("Roboto", 11)).pack(anchor="w", padx=10, pady=(0, 5))


    # ==========================================
    # CARREGAMENTO E EXPORTAÇÃO DO HISTÓRICO
    # ==========================================
    def carregar_historico_planos(self):
        for widget in self.lista_planos.winfo_children():
            widget.destroy()
            
        cur = self.db.cursor
        try:
            # Puxa os últimos 15 planos salvos
            cur.execute("SELECT ID_plano, numeroPlano, cliente, dataOperacao, statusAprovacao FROM PlanoRigging ORDER BY ID_plano DESC LIMIT 15")
            planos = cur.fetchall()
            
            if not planos:
                ctk.CTkLabel(self.lista_planos, text="Nenhum plano salvo ainda.", text_color="gray").pack(pady=20)
                return
                
            for p in planos:
                id_plano, num, cliente, data, status = p
                cor_status = "#2ECC71" if status == 1 else "#E74C3C" # Verde se aprovado, vermelho se reprovado
                
                card = ctk.CTkFrame(self.lista_planos, fg_color="#3b3b3b", corner_radius=6)
                card.pack(fill="x", pady=3, padx=2)
                
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=10, pady=5)
                
                ctk.CTkLabel(info, text=f"Plano {num}", font=("Roboto", 13, "bold"), text_color=cor_status).pack(anchor="w")
                ctk.CTkLabel(info, text=f"{cliente} | {data}", font=("Roboto", 11)).pack(anchor="w")
                
                ctk.CTkButton(card, text="⬇️ PDF", width=60, height=28, fg_color="#27AE60", hover_color="#2ECC71",
                              command=lambda i=id_plano, c=cliente, n=num: self.baixar_pdf_historico(i, c, n)).pack(side="right", padx=10)
        except Exception as e:
            ctk.CTkLabel(self.lista_planos, text="Erro ao carregar histórico.", text_color="red").pack()

    def baixar_pdf_historico(self, id_plano, cliente, numero_plano):
        """Gera o PDF reconstruindo os dados salvos no banco de dados"""
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            initialfile=f"Laudo_Rigging_{numero_plano}_{cliente.replace(' ', '_')}.pdf", 
            title="Baixar Laudo PDF Salvo",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not arquivo: return

        try:
            cur = self.db.cursor
            # 1. Puxar Cabeçalho
            cur.execute("SELECT numeroPlano, cliente, local, dataOperacao, crea, art, lanca_m, raioOperacao, carga_bruta_kg, capacidade_kg, tu_guindaste, statusAprovacao, ID_guindaste, esforco_sapata_kgf, rmet_kgf_cm2, resistencia_terreno FROM PlanoRigging WHERE ID_plano = ?", (id_plano,))
            cab = cur.fetchone()
            
            # 2. Puxar Carga
            cur.execute("SELECT descricao, pesoLiquido_kg, comprimento_m, largura_m, altura_m FROM Carga WHERE ID_plano = ?", (id_plano,))
            carga = cur.fetchone() or ("Desconhecida", 0, "", "", "")
            
            # 3. Puxar Guindaste
            cur.execute("SELECT modelo, fabricante FROM Guindaste WHERE ID_guindaste = ?", (cab[12],))
            g = cur.fetchone() or ("Desconhecido", "Desconhecido")
            
            # 4. Puxar Acessórios
            cur.execute("""
                SELECT r.quantidade_usada, a.codIdentificacao, t.nome_tipo, r.tu_percentual, r.carga_aplicada_kg 
                FROM Rel_Plano_Acessorio r 
                JOIN Acessorio a ON r.ID_acessorio = a.ID_acessorio 
                LEFT JOIN Tipo_acessorio t ON a.ID_tipo_acessorio = t.ID_tipo_acessorio 
                WHERE r.ID_plano = ?
            """, (id_plano,))
            acessorios = cur.fetchall()

            # --- MONTAR PDF BASEADO NO BANCO ---
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(15, 15, 15)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "GUINDASTES RIBAS - PLANO DE RIGGING", ln=True, align='C')
            pdf.ln(5)

            def add_linha(label, valor):
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(45, 6, label, border=0)
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, str(valor), border=0, ln=True)
                
            def add_titulo(texto):
                pdf.ln(4)
                pdf.set_font("Arial", 'B', 11)
                pdf.set_fill_color(220, 220, 220)
                pdf.cell(0, 8, f"  {texto}", border=1, ln=True, fill=True)
                pdf.ln(2)

            add_linha("Nº DO PLANO:", cab[0])
            add_linha("CLIENTE:", cab[1])
            add_linha("LOCAL:", cab[2] if cab[2] else "-")
            add_linha("DATA DA OPERAÇÃO:", cab[3])
            add_linha("CREA DO RESP.:", cab[4] if cab[4] else "-")
            add_linha("Nº DA ART:", cab[5] if cab[5] else "-")
            
            add_titulo("1. DADOS DA CARGA")
            add_linha("Descrição:", carga[0])
            add_linha("Peso Líquido:", f"{carga[1]} kg")
            add_linha("Dimensões (C x L x A):", f"{carga[2] or '-'}m x {carga[3] or '-'}m x {carga[4] or '-'}m")

            add_titulo("2. COMPOSIÇÃO E GUINDASTE")
            add_linha("Equipamento:", f"{g[1]} {g[0]}")
            add_linha("Lança Configurad:", f"{cab[6]} m")
            add_linha("Raio de Operação:", f"{cab[7]} m")
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, f"CARGA BRUTA TOTAL: {cab[8]} kg", ln=True)
            pdf.cell(0, 6, f"CAPACIDADE DA TABELA: {cab[9]} kg", ln=True)
            
            status_g = 'OK' if cab[11] == 1 else 'REPROVADO'
            pdf.cell(0, 6, f"TAXA DE UTIL. (TU): {cab[10]}% -> STATUS: {status_g}", ln=True)

            add_titulo("3. ACESSÓRIOS UTILIZADOS")
            pdf.set_font("Arial", '', 10)
            if not acessorios:
                pdf.cell(0, 6, "Nenhum acessório salvo.", ln=True)
            for a in acessorios:
                linha_txt = f"- {a[0]}x {a[1]} ({a[2]}): Carga Aplic. {a[4]} kg | TU {a[3]}%"
                pdf.multi_cell(0, 6, linha_txt)
                
            add_titulo("4. REAÇÕES DE APOIO E TERRENO")
            if cab[13]: # Se tem esforço sapata salvo
                add_linha("Esforço na Sapata:", f"{cab[13]} kgf")
                add_linha("RMET Exigida:", f"{cab[14]} kgf/cm²")
                add_linha("Resistência Solo:", f"{cab[15] if cab[15] else 'Não informada'} kgf/cm²")
            else:
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 6, "Dados de sapatas não informados para este plano.")

            add_titulo("PARECER FINAL")
            pdf.set_font("Arial", 'B', 14)
            if cab[11] == 1:
                pdf.set_text_color(39, 174, 96) 
                pdf.cell(0, 10, "IÇAMENTO APROVADO", ln=True, align='C')
            else:
                pdf.set_text_color(231, 76, 60)
                pdf.cell(0, 10, "IÇAMENTO REPROVADO", ln=True, align='C')

            pdf.output(arquivo)
            messagebox.showinfo("Sucesso", f"Plano {numero_plano} exportado com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF do histórico: {e}")

    # ==========================================
    # FUNÇÕES DA SIMULAÇÃO
    # ==========================================
    def abrir_tabela_selecao(self):
        nome_selecionado = self.combo_guindaste.get()
        id_guindaste = self.mapa_guindastes.get(nome_selecionado)
        
        if not id_guindaste:
            messagebox.showwarning("Aviso", "Selecione um guindaste válido.")
            return
        
        guindaste_db = self.repo_guindaste.buscar_por_id(id_guindaste)
        tabela_carga = guindaste_db.get("tabela_carga", {})
        if not tabela_carga:
            messagebox.showinfo("Aviso", "Este guindaste não possui tabela.")
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Tabela - {nome_selecionado}")
        modal.geometry("450x500")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        ctk.CTkLabel(modal, text="Dê um duplo-clique para preencher a simulação:", font=("Roboto", 14, "bold")).pack(pady=(15, 5))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30)
        style.map("Treeview", background=[("selected", "#3498DB")])

        colunas = ("lanca", "raio", "capacidade")
        tree = ttk.Treeview(modal, columns=colunas, show="headings", height=12)
        tree.heading("lanca", text="Lança (m)")
        tree.heading("raio", text="Raio (m)")
        tree.heading("capacidade", text="Carga Máxima (kg)")
        
        tree.column("lanca", width=120, anchor="center")
        tree.column("raio", width=120, anchor="center")
        tree.column("capacidade", width=150, anchor="center")
        tree.pack(padx=20, pady=10, fill="both", expand=True)

        for lanca_str, raios_dict in tabela_carga.items():
            for raio_str, peso in raios_dict.items():
                tree.insert("", "end", values=(lanca_str, raio_str, peso))

        def selecionar_item(event):
            selecionado = tree.selection()
            if selecionado:
                v_lanca, v_raio, v_capacidade = tree.item(selecionado[0])["values"]
                self.input_lanca.delete(0, 'end'); self.input_lanca.insert(0, str(v_lanca))
                self.input_raio.delete(0, 'end'); self.input_raio.insert(0, str(v_raio))
                self.input_carga.delete(0, 'end'); self.input_carga.insert(0, str(v_capacidade))
                modal.destroy()

        tree.bind("<Double-1>", selecionar_item)
        ctk.CTkButton(modal, text="Fechar", command=modal.destroy, fg_color="gray").pack(pady=10)

    def executar_simulacao(self):
        try:
            lanca = float(self.input_lanca.get().replace(",", "."))
            raio = float(self.input_raio.get().replace(",", "."))
            carga = float(self.input_carga.get().replace(",", "."))
            id_guindaste = self.mapa_guindastes.get(self.combo_guindaste.get())
            
            if not id_guindaste: raise ValueError("Guindaste inválido.")

            guindaste_db = self.repo_guindaste.buscar_por_id(id_guindaste)
            capacidade_nominal = CalculadorRigging.interpolar_capacidade(guindaste_db["tabela_carga"], lanca, raio)
            resultado_tu = CalculadorRigging.calcular_taxa_utilizacao(carga, capacidade_nominal)
            
            self.frame_resultado.pack(padx=15, fill="x", pady=(0, 10))
            self.lbl_capacidade.configure(text=f"Capacidade: {capacidade_nominal:,.0f} kg".replace(",", "."))
            self.lbl_tu.configure(text=f"TU: {resultado_tu['tu_percentual']}%")
            
            if resultado_tu['aprovado']: self.lbl_status.configure(text="IÇAMENTO APROVADO", text_color="#2ECC71")
            else: self.lbl_status.configure(text="REPROVADO (> 85%)", text_color="#E74C3C")
                
        except ValueError as e:
            self.frame_resultado.pack(padx=15, fill="x", pady=(0, 10))
            self.lbl_capacidade.configure(text="Erro de Cálculo")
            self.lbl_tu.configure(text=str(e))
            self.lbl_status.configure(text="INVÁLIDO", text_color="#E74C3C")
        except Exception:
            self.frame_resultado.pack(padx=15, fill="x", pady=(0, 10)) 
            self.lbl_capacidade.configure(text="Erro Inesperado")
            self.lbl_tu.configure(text="Digite somente números")
            self.lbl_status.configure(text="ERRO",text_color="#E74C3C")

    def atualizar_dados(self):
        self.lista_acessorios = self.repo_acessorio.listar_todos()
        self.lista_guindastes = self.repo_guindaste.listar_todos()

        self.mapa_guindastes = {f"{g[2]} {g[1]}": g[0] for g in self.lista_guindastes}
        nomes_guindastes = list(self.mapa_guindastes.keys()) if self.mapa_guindastes else ["Nenhum guindaste cadastrado"]

        self.combo_guindaste.configure(values=nomes_guindastes)
        self.carregar_historico_planos()