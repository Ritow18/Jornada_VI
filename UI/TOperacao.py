import customtkinter as ctk
from DBs.rep import BancoDeDados, RepGuindaste
from core.calculos import CalculadorRigging

class TelaOperacao(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        
        # Inicia a conexão para preencher os dados da tela
        self.db = BancoDeDados()
        self.repo_guindaste = RepGuindaste(self.db)
        
        # Busca todos os guindastes e cria um dicionário mapeando "Nome (Fabricante)" -> ID
        lista_db = self.repo_guindaste.listar_todos()
        self.mapa_guindastes = {f"{g[1]} ({g[2]})": g[0] for g in lista_db}
        nomes_guindastes = list(self.mapa_guindastes.keys()) if self.mapa_guindastes else ["Nenhum guindaste cadastrado"]

        self.titulo = ctk.CTkLabel(self, text="Simulador de Içamento (Rigging)", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, pady=(30, 20))

        self.frame_inputs = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_inputs.grid(row=1, column=0, pady=10)

        # 1. Seleção do Guindaste (Agora Dinâmico)
        lbl_guindaste = ctk.CTkLabel(self.frame_inputs, text="Selecione o Guindaste:")
        lbl_guindaste.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        self.combo_guindaste = ctk.CTkComboBox(self.frame_inputs, width=250, values=nomes_guindastes)
        self.combo_guindaste.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # 2. Comprimento da Lança
        lbl_lanca = ctk.CTkLabel(self.frame_inputs, text="Comprimento da Lança (m):")
        lbl_lanca.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.input_lanca = ctk.CTkEntry(self.frame_inputs, width=250, placeholder_text="Ex: 30.0")
        self.input_lanca.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # 3. Raio de Operação
        lbl_raio = ctk.CTkLabel(self.frame_inputs, text="Raio de Operação (m):")
        lbl_raio.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.input_raio = ctk.CTkEntry(self.frame_inputs, width=250, placeholder_text="Ex: 9.0")
        self.input_raio.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # 4. Carga Bruta Total
        lbl_carga = ctk.CTkLabel(self.frame_inputs, text="Carga Bruta Total (ton):")
        lbl_carga.grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.input_carga = ctk.CTkEntry(self.frame_inputs, width=250, placeholder_text="Ex: 23.2")
        self.input_carga.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self.btn_simular = ctk.CTkButton(self, text="SIMULAR IÇAMENTO", width=300, height=40, command=self.executar_simulacao)
        self.btn_simular.grid(row=2, column=0, pady=30)

        # --- ÁREA DE RESULTADOS ---
        self.frame_resultado = ctk.CTkFrame(self)
        self.lbl_capacidade = ctk.CTkLabel(self.frame_resultado, text="Capacidade Nominal: --", font=("Roboto", 16))
        self.lbl_capacidade.pack(pady=(15, 5), padx=20)
        self.lbl_tu = ctk.CTkLabel(self.frame_resultado, text="Taxa de Utilização (TU): --", font=("Roboto", 16))
        self.lbl_tu.pack(pady=5, padx=20)
        self.lbl_status = ctk.CTkLabel(self.frame_resultado, text="STATUS", font=("Roboto", 20, "bold"))
        self.lbl_status.pack(pady=(5, 15), padx=20)

    def executar_simulacao(self):
        try:
            lanca = float(self.input_lanca.get())
            raio = float(self.input_raio.get())
            carga = float(self.input_carga.get())
            
            # Pega o ID real baseado na escolha do dropdown
            nome_selecionado = self.combo_guindaste.get()
            id_guindaste = self.mapa_guindastes.get(nome_selecionado)
            
            if not id_guindaste:
                raise ValueError("Selecione um guindaste válido.")

            guindaste_db = self.repo_guindaste.buscar_por_id(id_guindaste)

            capacidade_nominal = CalculadorRigging.interpolar_capacidade(
                tabela_carga=guindaste_db["tabela_carga"],
                comprimento_lanca=lanca,
                raio_operacao=raio
            )
            
            resultado_tu = CalculadorRigging.calcular_taxa_utilizacao(
                carga_atuante=carga,
                capacidade_nominal=capacidade_nominal
            )
            
            self.frame_resultado.grid(row=3, column=0, pady=10, ipadx=40)
            self.lbl_capacidade.configure(text=f"Capacidade Nominal: {capacidade_nominal} ton")
            self.lbl_tu.configure(text=f"Taxa de Utilização (TU): {resultado_tu['tu_percentual']}%")
            
            if resultado_tu['aprovado']:
                self.lbl_status.configure(text="IÇAMENTO APROVADO", text_color="#2ECC71")
            else:
                self.lbl_status.configure(text="IÇAMENTO REPROVADO\n(Acima de 85%)", text_color="#E74C3C")
                
        except ValueError as e:
            self.frame_resultado.grid(row=3, column=0, pady=10, ipadx=20)
            self.lbl_capacidade.configure(text="Falha na Operação")
            self.lbl_tu.configure(text="")
            self.lbl_status.configure(text=str(e), text_color="#E74C3C")