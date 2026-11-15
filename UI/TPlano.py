import customtkinter as ctk
from datetime import datetime
import tkinter.filedialog as filedialog
from fpdf import FPDF

from DBs.rep import BancoDeDados, RepGuindaste
from DBs.rep_plano import RepPlano
from core.calculos import CalculadorRigging

# Import da orquestração do plano (certifique-se que essa função está no seu core/plano.py)
from core.plano import calcular_plano

VERDE, VERMELHO, AMARELO = "#2ECC71", "#E74C3C", "#F39C12"

# Resolvemos o problema do "eh_cinta" criando ele localmente aqui na tela!
def eh_cinta(tipo):
    return "cinta" in str(tipo).lower()

class TelaPlano(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.db = BancoDeDados()
        self.repo_guindaste = RepGuindaste(self.db)
        self.repo_plano = RepPlano(self.db)

        self.itens = {}      
        self.ultimo = None   
        self.guindaste_atual = None # Guarda o guindaste selecionado para usar nos comboboxes

        guindastes = self.repo_guindaste.listar_todos()
        self.mapa_guindastes = {f"{g[1]} ({g[2]})": g[0] for g in guindastes}
        nomes_g = list(self.mapa_guindastes.keys()) or ["Nenhum guindaste cadastrado"]

        self.mapa_acessorios = {
            f"{a['codigo']} - {a['tipo']} ({a.get('capac_kg', a.get('capac_ton', 0))} kg)": a
            for a in self.repo_plano.listar_acessorios()
        }
        nomes_a = list(self.mapa_acessorios.keys()) or ["Nenhum acessório cadastrado"]

        ctk.CTkLabel(self, text="Plano de Rigging", font=("Roboto", 24, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(20, 10))

        # ================= ESQUERDA: FORMULÁRIO =================
        esq = ctk.CTkScrollableFrame(self, fg_color="transparent")
        esq.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nsew")

        # --- SEÇÃO 1: Identificação ---
        sec_id = self._secao(esq, "1. Identificação")
        self.lbl_numero = ctk.CTkLabel(sec_id, text=f"Nº do plano: {self.repo_plano.proximo_numero()}", text_color="#aaaaaa")
        self.lbl_numero.pack(anchor="w", padx=10, pady=(0, 5))
        self.inp_cliente = self._entrada(sec_id, "Cliente", "Ex: Kaefer Rip")
        self.inp_local = self._entrada(sec_id, "Local", "Ex: Curitiba")
        self.inp_data = self._entrada(sec_id, "Data", "dd/mm/aaaa")
        self.inp_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        # AJUSTE: Campos CREA e ART
        self.inp_crea = self._entrada(sec_id, "CREA do Responsável", "Ex: 123456-D")
        self.inp_art = self._entrada(sec_id, "Número da ART", "Ex: 9876543210")

        # --- SEÇÃO 2: Guindaste e operação ---
        sec_operacao = self._secao(esq, "2. Guindaste e operação")
        self.combo_guindaste = self._combo(sec_operacao, "Guindaste", valores=nomes_g, comando=self.atualizar_lancas)
        self.combo_guindaste.configure(state="readonly") # <-- TRAVADO
        
        self.combo_lanca = self._combo(sec_operacao, "Lança (m)", valores=["Selecione o guindaste"], comando=self.atualizar_raios)
        self.combo_lanca.configure(state="readonly") # <-- TRAVADO
        
        self.combo_raio = self._combo(sec_operacao, "Raio de operação (m)", valores=["Selecione a lança"])
        self.combo_raio.configure(state="readonly") # <-- TRAVADO
        
        self.inp_vento = self._entrada(sec_operacao, "Vento (km/h) - opcional")

        # --- SEÇÃO 3: Carga ---
        sec_carga = self._secao(esq, "3. Carga")
        self.inp_desc = self._entrada(sec_carga, "Descrição", "Ex: Chiller")
        self.inp_peso = self._entrada(sec_carga, "Peso líquido (kg)", "Ex: 3450")
        self.inp_comp = self._entrada(sec_carga, "Comprimento (m) - opc.")
        self.inp_larg = self._entrada(sec_carga, "Largura (m) - opc.")
        self.inp_alt = self._entrada(sec_carga, "Altura (m) - opc.")

        # --- SEÇÃO 4: Acessórios ---
        sec_acessorios = self._secao(esq, "4. Lingada / acessórios")
        self.combo_acessorio = self._combo(sec_acessorios, "Acessório", valores=nomes_a)
        
        self.inp_qtd = self._entrada(sec_acessorios, "Quantidade", "Ex: 2")
        self.inp_angulo = self._entrada(sec_acessorios, "Ângulo (°)", "Só cintas. Ex: 28")
        self.inp_pernas = self._entrada(sec_acessorios, "Pernas", "Só cintas. Padrão: 2")
        self.inp_aplicada = self._entrada(sec_acessorios, "Carga aplicada (kg)", "Vazio = carga bruta")
        
        ctk.CTkButton(sec_acessorios, text="+ Adicionar à Lingada", command=self.adicionar_item,
                      fg_color="#3498DB", hover_color="#2980B9").pack(pady=10)
        self.frame_itens = ctk.CTkFrame(sec_acessorios, fg_color="transparent")
        self.frame_itens.pack(fill="x", padx=5)
        self._redesenhar_itens()

        # --- SEÇÃO 5: Sapatas ---
        sec_sapatas = self._secao(esq, "5. Sapatas e terreno (opcional)")
        self.inp_pg = self._entrada(sec_sapatas, "Guindaste+Caminhão (kg)", "Ex: 11550")
        self.inp_dist = self._entrada(sec_sapatas, "Eixo → sapata (m)", "Ex: 2.95")
        self.inp_abert = self._entrada(sec_sapatas, "Abertura sapatas (m)", "Ex: 5.7")
        self.inp_dl = self._entrada(sec_sapatas, "Dormente largura (cm)", "Ex: 50")
        self.inp_dc = self._entrada(sec_sapatas, "Dormente comp. (cm)", "Ex: 50")
        self.inp_dq = self._entrada(sec_sapatas, "Qtd. dormentes", "Padrão: 1")
        self.inp_terreno = self._entrada(sec_sapatas, "Resist. solo (kgf/cm²)", "Opcional")

        # --- BOTÕES DE AÇÃO ---
        botoes = ctk.CTkFrame(esq, fg_color="transparent")
        botoes.pack(pady=20)
        ctk.CTkButton(botoes, text="CALCULAR", width=120, height=40, command=self.calcular,
                      fg_color="#F39C12", hover_color="#E67E22").pack(side="left", padx=5)
        ctk.CTkButton(botoes, text="SALVAR", width=120, height=40, command=self.salvar,
                      fg_color="#2ECC71", hover_color="#27AE60").pack(side="left", padx=5)
        ctk.CTkButton(botoes, text="EXPORTAR PDF", width=120, height=40, command=self.exportar_relatorio,
                      fg_color="#9B59B6", hover_color="#8E44AD").pack(side="left", padx=5)

        # ================= DIREITA: RESULTADO =================
        dir_ = ctk.CTkFrame(self)
        dir_.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="nsew")
        dir_.grid_rowconfigure(1, weight=1)
        dir_.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(dir_, text="Preencha o formulário e clique em CALCULAR",
                                       font=("Roboto", 18, "bold"), wraplength=420)
        self.lbl_status.grid(row=0, column=0, pady=20, padx=10)
        self.txt_resultado = ctk.CTkTextbox(dir_, font=("Consolas", 13), wrap="word", fg_color="#1a1a1a", border_width=1, border_color="#444")
        self.txt_resultado.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.txt_resultado.configure(state="disabled")

    # ------------------------------------------------------------ helpers de UI
    @staticmethod
    def _secao(parent, titulo):
        card = ctk.CTkFrame(parent, fg_color="#2a2a2a", corner_radius=8)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text=titulo, font=("Roboto", 15, "bold"), text_color="#F39C12").pack(anchor="w", padx=15, pady=(10, 5))
        frame_interno = ctk.CTkFrame(card, fg_color="transparent")
        frame_interno.pack(fill="x", padx=10, pady=(0, 10))
        return frame_interno

    @staticmethod
    def _entrada(parent, rotulo, placeholder=""):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=5, pady=4)
        ctk.CTkLabel(linha, text=rotulo, width=140, anchor="w").pack(side="left")
        entrada = ctk.CTkEntry(linha, width=260, placeholder_text=placeholder, fg_color="#222222", border_color="#555")
        entrada.pack(side="left")
        return entrada
        
    @staticmethod
    def _combo(parent, rotulo, valores, comando=None):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=5, pady=4)
        ctk.CTkLabel(linha, text=rotulo, width=140, anchor="w").pack(side="left")
        combo = ctk.CTkComboBox(linha, width=260, values=valores, fg_color="#222222", border_color="#555", command=comando)
        combo.pack(side="left")
        return combo

    @staticmethod
    def _num(entrada_ou_str, nome, obrigatorio=True):
        # Aceita tanto CTkEntry quanto CTkComboBox
        txt = entrada_ou_str.get().strip().replace(",", ".") if hasattr(entrada_ou_str, 'get') else str(entrada_ou_str)
        if not txt or txt.startswith("Selecione"):
            if obrigatorio: raise ValueError(f"Preencha/Selecione o campo: {nome}.")
            return None
        try: return float(txt)
        except ValueError: raise ValueError(f"Valor inválido no campo: {nome}.")

    def _mostrar(self, status, cor, texto=""):
        self.lbl_status.configure(text=status, text_color=cor)
        self.txt_resultado.configure(state="normal")
        self.txt_resultado.delete("0.0", "end")
        self.txt_resultado.insert("0.0", texto)
        self.txt_resultado.configure(state="disabled")

    # ------------------------------------------------------------ comboboxes dinâmicos
    def atualizar_lancas(self, selecao):
        id_g = self.mapa_guindastes.get(selecao)
        if not id_g: return
        self.guindaste_atual = self.repo_guindaste.buscar_por_id(id_g)
        if self.guindaste_atual and "tabela_carga" in self.guindaste_atual:
            lancas = list(self.guindaste_atual["tabela_carga"].keys())
            self.combo_lanca.configure(values=lancas)
            self.combo_lanca.set(lancas[0] if lancas else "Sem lanças cadastradas")
            self.atualizar_raios(self.combo_lanca.get())

    def atualizar_raios(self, lanca_selecionada):
        if not self.guindaste_atual or "tabela_carga" not in self.guindaste_atual: return
        tabela = self.guindaste_atual["tabela_carga"]
        if lanca_selecionada in tabela:
            raios = list(tabela[lanca_selecionada].keys())
            self.combo_raio.configure(values=raios)
            self.combo_raio.set(raios[0] if raios else "Sem raios cadastrados")

    # ------------------------------------------------------------ acessórios
    def adicionar_item(self):
        try:
            acessorio = self.mapa_acessorios.get(self.combo_acessorio.get())
            if not acessorio: raise ValueError("Selecione um acessório cadastrado.")
            qtd = self._num(self.inp_qtd, "Quantidade")
            if qtd <= 0 or qtd != int(qtd): raise ValueError("A quantidade deve ser inteira e maior que zero.")
            pernas = self._num(self.inp_pernas, "Pernas", obrigatorio=False)
            
            self.itens[acessorio["id"]] = {
                "id": acessorio["id"], "tipo": acessorio["tipo"], "codigo": acessorio["codigo"],
                "capac_ton": acessorio["capac_ton"], "desgaste_perc": acessorio["desgaste_perc"],
                "peso_unit_kg": acessorio["peso_unit_kg"], "qtd": int(qtd),
                "angulo": self._num(self.inp_angulo, "Ângulo", obrigatorio=False),
                "pernas": int(pernas) if pernas else 2,
                "carga_aplicada_kg": self._num(self.inp_aplicada, "Carga aplicada", obrigatorio=False),
            }
            for e in (self.inp_qtd, self.inp_angulo, self.inp_pernas, self.inp_aplicada): e.delete(0, "end")
            self._redesenhar_itens()
        except ValueError as e:
            self._mostrar(str(e), VERMELHO)

    def remover_item(self, id_acessorio):
        self.itens.pop(id_acessorio, None)
        self._redesenhar_itens()

    def _redesenhar_itens(self):
        for w in self.frame_itens.winfo_children(): w.destroy()
        if not self.itens:
            ctk.CTkLabel(self.frame_itens, text="Nenhum acessório na lingada.", text_color="gray").pack(pady=4)
            return
        for i in self.itens.values():
            card = ctk.CTkFrame(self.frame_itens, fg_color="#1a1a1a", border_width=1, border_color="#444")
            card.pack(fill="x", pady=3)
            extra = f" | {i['angulo'] or 0:g}° | {i['pernas']} pernas" if eh_cinta(i["tipo"]) else ""
            ctk.CTkLabel(card, text=f"{i['qtd']}x {i['codigo']} ({i['tipo']}){extra}", anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkButton(card, text="X", width=30, fg_color=VERMELHO, hover_color="#C0392B",
                          command=lambda k=i["id"]: self.remover_item(k)).pack(side="right", padx=8, pady=6)

    # ------------------------------------------------------------ cálculo e exportação
    def _ler_sapatas(self):
        campos = [self.inp_pg, self.inp_dist, self.inp_abert, self.inp_dl, self.inp_dc]
        if not any(c.get().strip() for c in campos): return None
        qtd = self._num(self.inp_dq, "Qtd. dormentes", obrigatorio=False)
        return {
            "peso_guindaste_kgf": self._num(self.inp_pg, "Guindaste+caminhão"),
            "dist_eixo_m": self._num(self.inp_dist, "Eixo → sapata"),
            "abertura_m": self._num(self.inp_abert, "Abertura das sapatas"),
            "dormente_larg_cm": self._num(self.inp_dl, "Dormente largura"),
            "dormente_comp_cm": self._num(self.inp_dc, "Dormente comprimento"),
            "dormente_qtd": int(qtd) if qtd else 1,
            "resistencia_terreno": self._num(self.inp_terreno, "Resistência do terreno", obrigatorio=False),
        }

    def calcular(self) -> bool:
        self.ultimo = None
        try:
            cliente = self.inp_cliente.get().strip()
            if not cliente: raise ValueError("Preencha o campo: Cliente.")
            crea = self.inp_crea.get().strip()
            art = self.inp_art.get().strip()
            
            try: data_iso = datetime.strptime(self.inp_data.get().strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError: raise ValueError("Data inválida. Use dd/mm/aaaa.")
            
            id_guindaste = self.mapa_guindastes.get(self.combo_guindaste.get())
            if not id_guindaste: raise ValueError("Selecione um guindaste.")
            
            guindaste = self.repo_guindaste.buscar_por_id(id_guindaste)
            
            # Lança e raio agora vêm dos comboboxes formatados
            lanca = self._num(self.combo_lanca, "Lança")
            raio = self._num(self.combo_raio, "Raio de operação")
            
            descricao = self.inp_desc.get().strip()
            if not descricao: raise ValueError("Preencha o campo: Descrição da carga.")
            peso_kg = self._num(self.inp_peso, "Peso líquido")
            
            if not self.itens: raise ValueError("Adicione ao menos um acessório.")

            capacidade_kg = CalculadorRigging.interpolar_capacidade(guindaste["tabela_carga"], lanca, raio)
            sapatas = self._ler_sapatas()
            
            res = ServicoPlanoRigging(peso_kg, list(self.itens.values()), capacidade_kg, raio, sapatas)

            self.ultimo = {
                "cab": {"id_guindaste": id_guindaste, "cliente": cliente, "crea": crea, "art": art, "local": self.inp_local.get().strip(), "data_iso": data_iso, "raio_m": raio, "lanca_m": lanca, "sapatas_entrada": sapatas},
                "carga": {"descricao": descricao, "peso_kg": peso_kg, "comp_m": self._num(self.inp_comp, "Compr.", False), "larg_m": self._num(self.inp_larg, "Larg.", False), "alt_m": self._num(self.inp_alt, "Alt.", False)},
                "res": res, "guindaste_info": guindaste
            }
            self._exibir_resultado(guindaste, lanca, raio, res)
            return True
        except ValueError as e:
            self._mostrar(str(e), VERMELHO)
            return False

    def _exibir_resultado(self, guindaste, lanca, raio, r):
        tu_g = r["tu_guindaste"]
        ok = lambda b: "OK" if b else "REPROVADO"
        
        # AJUSTE: Tudo mostrado em KG na tela
        carga_bruta_kg = r.get('carga_bruta_kg', r.get('carga_bruta_ton', 0) * 1000)
        capacidade_kg = r.get('capacidade_kg', r.get('capacidade_ton', 0) * 1000)
        
        t = [
            "CARGA BRUTA", f"  Carga líquida ....... {r['carga_liquida_kg']:.2f} kg", f"  Lingada ............. {r['lingada_kg']:.2f} kg",
            f"  Balancim ............ {r['balancim_kg']:.2f} kg", f"  TOTAL ............... {carga_bruta_kg:.2f} kg", "",
            f"GUINDASTE: {guindaste['fabricante']} {guindaste['modelo']}", f"  Lança {lanca:g} m | Raio {raio:g} m",
            f"  Capacidade .......... {capacidade_kg} kg", f"  TU .................. {tu_g['tu_percentual']}%  [{ok(tu_g['aprovado'])}]", "", "ACESSÓRIOS (limite TU 85%)"
        ]
        for l in r["linhas"]:
            esf_kg = l.get('esforco_kg', l.get('esforco_ton', 0) * 1000)
            cap_ef_kg = l.get('capac_efetiva_kg', l.get('capac_efetiva_ton', 0) * 1000)
            t.extend([f"  {l['qtd']}x {l['codigo']} ({l['tipo']})", f"     esforço {esf_kg} kg | cap. efetiva {cap_ef_kg} kg | TU {l['tu_percentual']}%  [{ok(l['aprovado'])}]"])
        
        s = r["sapatas"]
        if s:
            t.extend(["", "SAPATAS E TERRENO", f"  Esforço na sapata ... {s['esforco_kgf']} kgf", f"  RMET ................ {s['rmet']} kgf/cm²"])
            t.append(f"  Terreno informado ... {s['resistencia_terreno']} kgf/cm²  [{ok(s['aprovado'])}]" if s["resistencia_terreno"] is not None else "  (informe a resistência do terreno para validar)")
        if r["avisos"]: t.extend(["", "AVISOS"] + [f"  - {a}" for a in r["avisos"]])
        self._mostrar("IÇAMENTO APROVADO" if r["aprovado"] else "IÇAMENTO REPROVADO", VERDE if r["aprovado"] else VERMELHO, "\n".join(t))

    def salvar(self):
        if not self.calcular(): return
        u = self.ultimo
        try: numero = self.repo_plano.salvar_plano(u["cab"], u["carga"], list(self.itens.values()), u["res"])
        except Exception as e:
            self._mostrar(f"Erro ao salvar: {e}", VERMELHO)
            return
        self.lbl_numero.configure(text=f"Nº do plano: {self.repo_plano.proximo_numero()}")
        self.lbl_status.configure(text=f"Plano {numero} salvo com sucesso!", text_color=VERDE if u["res"]["aprovado"] else AMARELO)

    def exportar_relatorio(self): 
        if not self.ultimo:
            self.lbl_status.configure(text="Calcule um plano válido antes de exportar.", text_color=AMARELO)
            return
            
        u = self.ultimo
        res, cab, carga, g = u["res"], u["cab"], u["carga"], u["guindaste_info"]
        sap = res.get("sapatas") or {}
        
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            initialfile=f"Laudo_Rigging_{cab['cliente'].replace(' ', '_')}.pdf", 
            title="Salvar Laudo PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if not arquivo:
            return
            
        # --- INÍCIO DA CRIAÇÃO DO PDF ---
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(left=15, top=15, right=15)
        
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

        # 1. Identificação
        num_plano = self.lbl_numero.cget("text").split(": ")[-1] if ":" in self.lbl_numero.cget("text") else "-"
        add_linha("Nº DO PLANO:", num_plano)
        add_linha("CLIENTE:", cab['cliente'])
        add_linha("LOCAL:", cab['local'])
        add_linha("DATA DA OPERAÇÃO:", cab['data_iso'])
        add_linha("CREA DO RESP.:", cab.get('crea', '-'))
        add_linha("Nº DA ART:", cab.get('art', '-'))
        
        # 2. Dados da Carga
        add_titulo("1. DADOS DA CARGA")
        add_linha("Descrição:", carga['descricao'])
        add_linha("Peso Líquido:", f"{carga['peso_kg']} kg")
        add_linha("Dimensões (C x L x A):", f"{carga['comp_m'] or '-'}m x {carga['larg_m'] or '-'}m x {carga['alt_m'] or '-'}m")

        # 3. Composição Carga Bruta
        carga_bruta_kg = res.get('carga_bruta_kg', res.get('carga_bruta_ton', 0) * 1000)
        
        add_titulo("2. COMPOSIÇÃO DA CARGA BRUTA")
        add_linha("Peso Líquido:", f"{carga['peso_kg']} kg")
        add_linha("Peso da Lingada:", f"{res['lingada_kg']} kg")
        add_linha("Peso do Balancim:", f"{res['balancim_kg']} kg")
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, f"CARGA BRUTA TOTAL: {carga_bruta_kg} kg", ln=True)

        # 4. Guindaste
        capacidade_kg = res.get('capacidade_kg', res.get('capacidade_ton', 0) * 1000)
        
        add_titulo("3. INFORMAÇÕES DO GUINDASTE E OPERAÇÃO")
        add_linha("Equipamento:", f"{g['fabricante']} {g['modelo']}")
        add_linha("Lança Configurad:", f"{cab['lanca_m']} m")
        add_linha("Raio de Operação:", f"{cab['raio_m']} m")
        add_linha("Capacidade Tabel.:", f"{capacidade_kg} kg")
        status_g = 'OK' if res['tu_guindaste']['aprovado'] else 'REPROVADO'
        add_linha("Taxa de Util. (TU):", f"{res['tu_guindaste']['tu_percentual']}% -> STATUS: {status_g}")

        # 5. Acessórios
        add_titulo("4. ACESSÓRIOS UTILIZADOS")
        pdf.set_font("Arial", '', 10)
        for l in res["linhas"]:
            st = 'OK' if l['aprovado'] else 'REPROVADO'
            cap_ef_kg = l.get('capac_efetiva_kg', l.get('capac_efetiva_ton', 0) * 1000)
            linha_txt = f"- {l['qtd']}x {l['codigo']} ({l['tipo']}): Cap. Efetiva {cap_ef_kg} kg | TU {l['tu_percentual']}% [{st}]"
            pdf.multi_cell(0, 6, linha_txt)
            
        # 6. Sapatas
        add_titulo("5. REAÇÕES DE APOIO E TERRENO")
        if sap:
            add_linha("Esforço na Sapata:", f"{sap.get('esforco_kgf')} kgf")
            add_linha("RMET Exigida:", f"{sap.get('rmet')} kgf/cm²")
            terreno = sap.get('resistencia_terreno')
            add_linha("Resistência Solo:", f"{terreno if terreno else 'Não informada'} kgf/cm²")
        else:
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, "Dados de sapatas não informados para este plano.")

        # 7. Parecer Final
        add_titulo("PARECER FINAL")
        pdf.set_font("Arial", 'B', 14)
        if res['aprovado']:
            pdf.set_text_color(39, 174, 96) 
            pdf.cell(0, 10, "IÇAMENTO APROVADO", ln=True, align='C')
        else:
            pdf.set_text_color(231, 76, 60)
            pdf.cell(0, 10, "IÇAMENTO REPROVADO", ln=True, align='C')
            
        pdf.set_text_color(0, 0, 0)
        pdf.ln(25) 
        
        # 8. Assinaturas
        y = pdf.get_y()
        pdf.line(20, y, 90, y)
        pdf.line(120, y, 190, y)
        pdf.set_xy(20, y)
        pdf.set_font("Arial", '', 10)
        pdf.cell(70, 5, "Engenheiro Rigger", align='C')
        pdf.set_xy(120, y)
        pdf.cell(70, 5, "Supervisor Responsável", align='C')
        
        try:
            pdf.output(arquivo)
            self.lbl_status.configure(text=f"Relatório PDF exportado com sucesso!", text_color=VERDE)
        except Exception as e:
            self.lbl_status.configure(text=f"Erro ao salvar PDF: {e}", text_color=VERMELHO)