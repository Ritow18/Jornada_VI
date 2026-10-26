import customtkinter as ctk

class TelaCriarFormula(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # O columnspan=2 faz o título ocupar as duas colunas do nosso grid invisível
        titulo = ctk.CTkLabel(self, text="Cadastrar Nova Fórmula", font=("Roboto", 24, "bold"))
        titulo.grid(row=0, column=0, columnspan=2, pady=(30, 20))

        # LINHA 1: Nome do Cálculo
        # sticky="e" alinha o texto à direita (East) para encostar na caixa de texto
        lbl_nome = ctk.CTkLabel(self, text="Nome do Cálculo:")
        lbl_nome.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.input_nome = ctk.CTkEntry(self, width=400, placeholder_text="Ex: Fator de Vento Extra")
        self.input_nome.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # LINHA 2: Variáveis
        lbl_vars = ctk.CTkLabel(self, text="Variáveis (separadas por vírgula):")
        lbl_vars.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        
        self.input_vars = ctk.CTkEntry(self, width=400, placeholder_text="Ex: velocidade, area, constante")
        self.input_vars.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # LINHA 3: Fórmula Matemática
        lbl_expr = ctk.CTkLabel(self, text="Fórmula Matemática:")
        lbl_expr.grid(row=3, column=0, padx=10, pady=10, sticky="e")
        
        self.input_expr = ctk.CTkEntry(self, width=400, placeholder_text="Ex: (velocidade ** 2) * area / constante")
        self.input_expr.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # LINHA 4: Botão Salvar 
        btn_salvar = ctk.CTkButton(self, text="SALVAR FÓRMULA", command=self.simular_salvamento)
        btn_salvar.grid(row=4, column=0, columnspan=2, pady=30)

    def simular_salvamento(self):
        # Aqui depois será chamado o repositorio.py para gravar no SQLite
        print(f"Salvando no Banco:")
        print(f"Nome: {self.input_nome.get()}")
        print(f"Vars: {self.input_vars.get()}")
        print(f"Expr: {self.input_expr.get()}")
        print("-" * 30)