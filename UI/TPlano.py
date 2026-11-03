import customtkinter as ctk
from datetime import datetime

from DBs.rep import BancoDeDados, RepGuindaste
from DBs.rep_plano import RepPlano
from core.calculos import CalculadorRigging
from core.plano import calcular_plano, eh_cinta

VERDE, VERMELHO, AMARELO = "#2ECC71", "#E74C3C", "#F1C40F"


class TelaPlano(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.db = BancoDeDados()
        self.repo_guindaste = RepGuindaste(self.db)
        self.repo_plano = RepPlano(self.db)

        self.itens = {}      # ID_acessorio -> dados da linha da lingada
        self.ultimo = None   # último cálculo válido (usado ao salvar)

        guindastes = self.repo_guindaste.listar_todos()
        self.mapa_guindastes = {f"{g[1]} ({g[2]})": g[0] for g in guindastes}
        nomes_g = list(self.mapa_guindastes) or ["Nenhum guindaste cadastrado"]

        self.mapa_acessorios = {
            f"{a['codigo']} - {a['tipo']} ({a['capac_ton']} t)": a
            for a in self.repo_plano.listar_acessorios()
        }
        nomes_a = list(self.mapa_acessorios) or ["Nenhum acessório cadastrado"]

        ctk.CTkLabel(self, text="Plano de Rigging", font=("Roboto", 24, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(20, 10))

        # ================= ESQUERDA: FORMULÁRIO =================
        esq = ctk.CTkScrollableFrame(self)
        esq.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nsew")

        self._secao(esq, "1. Identificação")
        self.lbl_numero = ctk.CTkLabel(
            esq, text=f"Nº do plano (gerado ao salvar): {self.repo_plano.proximo_numero()}", anchor="w")
        self.lbl_numero.pack(fill="x", padx=10)
        self.inp_cliente = self._entrada(esq, "Cliente", "Ex: Kaefer Rip Serviços Industriais")
        self.inp_local = self._entrada(esq, "Local", "Ex: Curitiba")
        self.inp_data = self._entrada(esq, "Data", "dd/mm/aaaa")
        self.inp_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        self._secao(esq, "2. Guindaste e operação")
        linha = ctk.CTkFrame(esq, fg_color="transparent")
        linha.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(linha, text="Guindaste", width=150, anchor="w").pack(side="left")
        self.combo_guindaste = ctk.CTkComboBox(linha, width=260, values=nomes_g)
        self.combo_guindaste.pack(side="left")
        self.inp_lanca = self._entrada(esq, "Lança (m)", "Ex: 5.1")
        self.inp_raio = self._entrada(esq, "Raio de operação (m)", "Ex: 5.0")
        self.inp_vento = self._entrada(esq, "Vento (km/h) - opcional")

        self._secao(esq, "3. Carga")
        self.inp_desc = self._entrada(esq, "Descrição", "Ex: Chiller")
        self.inp_peso = self._entrada(esq, "Peso líquido (kg)", "Ex: 3450")
        self.inp_comp = self._entrada(esq, "Comprimento (m) - opc.")
        self.inp_larg = self._entrada(esq, "Largura (m) - opc.")
        self.inp_alt = self._entrada(esq, "Altura (m) - opc.")

        self._secao(esq, "4. Lingada / acessórios")
        linha = ctk.CTkFrame(esq, fg_color="transparent")
        linha.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(linha, text="Acessório", width=150, anchor="w").pack(side="left")
        self.combo_acessorio = ctk.CTkComboBox(linha, width=260, values=nomes_a)
        self.combo_acessorio.pack(side="left")
        self.inp_qtd = self._entrada(esq, "Quantidade", "Ex: 2")
        self.inp_angulo = self._entrada(esq, "Ângulo c/ vertical (°)", "Só cintas. Ex: 28")
        self.inp_pernas = self._entrada(esq, "Pernas", "Só cintas. Padrão: 2")
        self.inp_aplicada = self._entrada(esq, "Carga aplicada (kg)", "Vazio = carga bruta")
        ctk.CTkButton(esq, text="Adicionar / atualizar acessório", command=self.adicionar_item,
                      fg_color="#3498DB", hover_color="#2980B9").pack(pady=8)
        self.frame_itens = ctk.CTkFrame(esq, fg_color="transparent")
        self.frame_itens.pack(fill="x", padx=5)
        self._redesenhar_itens()

        self._secao(esq, "5. Sapatas e terreno (opcional)")
        self.inp_pg = self._entrada(esq, "Guindaste+caminhão (kgf)", "Ex: 11550")
        self.inp_dist = self._entrada(esq, "Eixo → sapata (m)", "Ex: 2.95")
        self.inp_abert = self._entrada(esq, "Abertura sapatas (m)", "Ex: 5.7")
        self.inp_dl = self._entrada(esq, "Dormente largura (cm)", "Ex: 50")
        self.inp_dc = self._entrada(esq, "Dormente comprimento (cm)", "Ex: 50")
        self.inp_dq = self._entrada(esq, "Qtd. dormentes", "Padrão: 1")
        self.inp_terreno = self._entrada(esq, "Resistência terreno (kgf/cm²)", "Opcional")

        botoes = ctk.CTkFrame(esq, fg_color="transparent")
        botoes.pack(pady=15)
        ctk.CTkButton(botoes, text="CALCULAR", width=150, height=40, command=self.calcular).pack(side="left", padx=5)
        ctk.CTkButton(botoes, text="SALVAR PLANO", width=150, height=40, command=self.salvar,
                      fg_color="#2ECC71", hover_color="#27AE60").pack(side="left", padx=5)

        # ================= DIREITA: RESULTADO =================
        dir_ = ctk.CTkFrame(self)
        dir_.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="nsew")
        dir_.grid_rowconfigure(1, weight=1)
        dir_.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(dir_, text="Preencha o formulário e clique em CALCULAR",
                                       font=("Roboto", 18, "bold"), wraplength=420)
        self.lbl_status.grid(row=0, column=0, pady=15, padx=10)
        self.txt_resultado = ctk.CTkTextbox(dir_, font=("Consolas", 13), wrap="word")
        self.txt_resultado.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.txt_resultado.configure(state="disabled")

    # ------------------------------------------------------------ helpers de UI
    @staticmethod
    def _secao(parent, titulo):
        ctk.CTkLabel(parent, text=titulo, font=("Roboto", 15, "bold"), anchor="w").pack(
            fill="x", padx=5, pady=(15, 4))

    @staticmethod
    def _entrada(parent, rotulo, placeholder=""):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(linha, text=rotulo, width=150, anchor="w").pack(side="left")
        entrada = ctk.CTkEntry(linha, width=260, placeholder_text=placeholder)
        entrada.pack(side="left")
        return entrada

    @staticmethod
    def _num(entrada, nome, obrigatorio=True):
        """Lê número aceitando vírgula decimal (3,45)."""
        txt = entrada.get().strip().replace(",", ".")
        if not txt:
            if obrigatorio:
                raise ValueError(f"Preencha o campo: {nome}.")
            return None
        try:
            return float(txt)
        except ValueError:
            raise ValueError(f"Valor inválido no campo: {nome}.")

    def _mostrar(self, status, cor, texto=""):
        self.lbl_status.configure(text=status, text_color=cor)
        self.txt_resultado.configure(state="normal")
        self.txt_resultado.delete("0.0", "end")
        self.txt_resultado.insert("0.0", texto)
        self.txt_resultado.configure(state="disabled")

    # ------------------------------------------------------------ acessórios
    def adicionar_item(self):
        try:
            acessorio = self.mapa_acessorios.get(self.combo_acessorio.get())
            if not acessorio:
                raise ValueError("Selecione um acessório cadastrado.")
            qtd = self._num(self.inp_qtd, "Quantidade")
            if qtd <= 0 or qtd != int(qtd):
                raise ValueError("A quantidade deve ser um número inteiro maior que zero.")
            pernas = self._num(self.inp_pernas, "Pernas", obrigatorio=False)
            self.itens[acessorio["id"]] = {
                "id": acessorio["id"],
                "tipo": acessorio["tipo"],
                "codigo": acessorio["codigo"],
                "capac_ton": acessorio["capac_ton"],
                "desgaste_perc": acessorio["desgaste_perc"],
                "peso_unit_kg": acessorio["peso_unit_kg"],
                "qtd": int(qtd),
                "angulo": self._num(self.inp_angulo, "Ângulo", obrigatorio=False),
                "pernas": int(pernas) if pernas else 2,
                "carga_aplicada_kg": self._num(self.inp_aplicada, "Carga aplicada", obrigatorio=False),
            }
            for e in (self.inp_qtd, self.inp_angulo, self.inp_pernas, self.inp_aplicada):
                e.delete(0, "end")
            self._redesenhar_itens()
        except ValueError as e:
            self._mostrar(str(e), VERMELHO)

    def remover_item(self, id_acessorio):
        self.itens.pop(id_acessorio, None)
        self._redesenhar_itens()

    def _redesenhar_itens(self):
        for w in self.frame_itens.winfo_children():
            w.destroy()
        if not self.itens:
            ctk.CTkLabel(self.frame_itens, text="Nenhum acessório na lingada.", text_color="gray").pack(pady=4)
            return
        for i in self.itens.values():
            card = ctk.CTkFrame(self.frame_itens, fg_color="#2b2b2b")
            card.pack(fill="x", pady=3)
            extra = f" | {i['angulo'] or 0:g}° | {i['pernas']} pernas" if eh_cinta(i["tipo"]) else ""
            ctk.CTkLabel(card, text=f"{i['qtd']}x {i['codigo']} ({i['tipo']}){extra}", anchor="w").pack(
                side="left", padx=10, pady=6)
            ctk.CTkButton(card, text="X", width=30, fg_color=VERMELHO, hover_color="#C0392B",
                          command=lambda k=i["id"]: self.remover_item(k)).pack(side="right", padx=8, pady=6)

    # ------------------------------------------------------------ cálculo
    def _ler_sapatas(self):
        campos = [self.inp_pg, self.inp_dist, self.inp_abert, self.inp_dl, self.inp_dc]
        if not any(c.get().strip() for c in campos):
            return None  # bloco opcional não preenchido
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
            if not cliente:
                raise ValueError("Preencha o campo: Cliente.")
            try:
                data_iso = datetime.strptime(self.inp_data.get().strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError("Data inválida. Use o formato dd/mm/aaaa.")

            id_guindaste = self.mapa_guindastes.get(self.combo_guindaste.get())
            if not id_guindaste:
                raise ValueError("Selecione um guindaste cadastrado.")
            guindaste = self.repo_guindaste.buscar_por_id(id_guindaste)
            lanca = self._num(self.inp_lanca, "Lança")
            raio = self._num(self.inp_raio, "Raio de operação")

            descricao = self.inp_desc.get().strip()
            if not descricao:
                raise ValueError("Preencha o campo: Descrição da carga.")
            peso_kg = self._num(self.inp_peso, "Peso líquido")

            if not self.itens:
                raise ValueError("Adicione ao menos um acessório à lingada.")

            capacidade = CalculadorRigging.interpolar_capacidade(guindaste["tabela_carga"], lanca, raio)
            sapatas = self._ler_sapatas()
            res = calcular_plano(peso_kg, list(self.itens.values()), capacidade, raio, sapatas)

            self.ultimo = {
                "cab": {
                    "id_guindaste": id_guindaste, "cliente": cliente, "local": self.inp_local.get().strip(),
                    "data_iso": data_iso, "raio_m": raio, "lanca_m": lanca,
                    "vento": self._num(self.inp_vento, "Vento", obrigatorio=False),
                    "sapatas_entrada": sapatas,
                },
                "carga": {
                    "descricao": descricao, "peso_kg": peso_kg,
                    "comp_m": self._num(self.inp_comp, "Comprimento", obrigatorio=False),
                    "larg_m": self._num(self.inp_larg, "Largura", obrigatorio=False),
                    "alt_m": self._num(self.inp_alt, "Altura", obrigatorio=False),
                },
                "res": res,
            }
            self._exibir_resultado(guindaste, lanca, raio, res)
            return True
        except ValueError as e:
            self._mostrar(str(e), VERMELHO)
            return False

    def _exibir_resultado(self, guindaste, lanca, raio, r):
        tu_g = r["tu_guindaste"]
        ok = lambda b: "OK" if b else "REPROVADO"
        t = [
            "CARGA BRUTA",
            f"  Carga líquida ....... {r['carga_liquida_kg']:.2f} kg",
            f"  Lingada ............. {r['lingada_kg']:.2f} kg",
            f"  Balancim ............ {r['balancim_kg']:.2f} kg",
            f"  TOTAL ............... {r['carga_bruta_ton'] * 1000:.2f} kg",
            "",
            f"GUINDASTE: {guindaste['fabricante']} {guindaste['modelo']}",
            f"  Lança {lanca:g} m | Raio {raio:g} m",
            f"  Capacidade .......... {r['capacidade_ton']} t",
            f"  TU .................. {tu_g['tu_percentual']}%  [{ok(tu_g['aprovado'])}]",
            "",
            "ACESSÓRIOS (limite TU 85%)",
        ]
        for l in r["linhas"]:
            t.append(f"  {l['qtd']}x {l['codigo']} ({l['tipo']})")
            t.append(f"     esforço {l['esforco_ton']} t | cap. efetiva {l['capac_efetiva_ton']} t "
                     f"| TU {l['tu_percentual']}%  [{ok(l['aprovado'])}]")
        s = r["sapatas"]
        if s:
            t += ["", "SAPATAS E TERRENO",
                  f"  Esforço na sapata ... {s['esforco_kgf']} kgf",
                  f"  RMET ................ {s['rmet']} kgf/cm²"]
            if s["resistencia_terreno"] is not None:
                t.append(f"  Terreno informado ... {s['resistencia_terreno']} kgf/cm²  [{ok(s['aprovado'])}]")
            else:
                t.append("  (informe a resistência do terreno para validar)")
        if r["avisos"]:
            t += ["", "AVISOS"] + [f"  - {a}" for a in r["avisos"]]

        if r["aprovado"]:
            self._mostrar("IÇAMENTO APROVADO", VERDE, "\n".join(t))
        else:
            self._mostrar("IÇAMENTO REPROVADO", VERMELHO, "\n".join(t))

    # ------------------------------------------------------------ salvar
    def salvar(self):
        if not self.calcular():
            return
        u = self.ultimo
        try:
            numero = self.repo_plano.salvar_plano(u["cab"], u["carga"], list(self.itens.values()), u["res"])
        except Exception as e:
            self._mostrar(f"Erro ao salvar o plano: {e}", VERMELHO)
            return
        self.lbl_numero.configure(
            text=f"Nº do plano (gerado ao salvar): {self.repo_plano.proximo_numero()}")
        status = "APROVADO" if u["res"]["aprovado"] else "REPROVADO"
        self.lbl_status.configure(text=f"Plano {numero} salvo ({status})",
                                 text_color=VERDE if u["res"]["aprovado"] else AMARELO)