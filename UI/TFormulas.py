import customtkinter as ctk
from DBs.rep import BancoDeDados, RepFormula
from core.calculos import FORMULAS_FIXAS

class TelaCriarFormula(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1) # Mantém a esticada correta para as duas colunas

        self.db = BancoDeDados()
        self.repo = RepFormula(self.db)

        self.titulo = ctk.CTkLabel(self, text="Gestão de Fórmulas", font=("Roboto", 24, "bold"))
        self.titulo.grid(row=0, column=0, columnspan=2, pady=(20, 20))

        # ================= ESQUERDA: CADASTRO (Agora com Scroll para não achatar) =================
        self.frame_cadastro = ctk.CTkScrollableFrame(self)
        self.frame_cadastro.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_cadastro, text="Nova Fórmula", font=("Roboto", 18, "bold")).pack(pady=10)

        self.inp_nome = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Nome (Ex: Fator Vento)", width=300)
        self.inp_nome.pack(pady=5)
        
        self.inp_desc = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Descrição breve", width=300)
        self.inp_desc.pack(pady=5)

        self.inp_vars = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Variáveis (Ex: vento, area)", width=300)
        self.inp_vars.pack(pady=5)

        self.inp_expr = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Fórmula (Use os botões abaixo)", width=300)
        self.inp_expr.pack(pady=(15, 5))

        # --- TECLADO DA CALCULADORA CIENTÍFICA ---
        self.criar_teclado()

        self.btn_salvar = ctk.CTkButton(self.frame_cadastro, text="Salvar Fórmula", command=self.salvar_nova, fg_color="#2ECC71", hover_color="#27AE60", height=40)
        self.btn_salvar.pack(pady=20)

        # ================= DIREITA: FIXAS (em cima) + CADASTRADAS (embaixo) =================
        frame_direita = ctk.CTkFrame(self, fg_color="transparent")
        frame_direita.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        frame_direita.grid_columnconfigure(0, weight=1)
        frame_direita.grid_rowconfigure(0, weight=1)
        frame_direita.grid_rowconfigure(1, weight=1)

        self.frame_fixas = ctk.CTkScrollableFrame(frame_direita, label_text="Fórmulas Fixas (clique para usar)")
        self.frame_fixas.grid(row=0, column=0, pady=(0, 5), sticky="nsew")

        self.frame_lista = ctk.CTkScrollableFrame(frame_direita, label_text="Fórmulas Cadastradas (clique para usar)")
        self.frame_lista.grid(row=1, column=0, pady=(5, 0), sticky="nsew")

        self.carregar_fixas()
        self.carregar_lista()

    def criar_teclado(self):
        frame_calc = ctk.CTkFrame(self.frame_cadastro, fg_color="transparent")
        frame_calc.pack(pady=5)
        
        # Matriz completa baseada na biblioteca math
        botoes = [
            ('sin(', 'cos(', 'tan(', 'pi', 'sqrt('),
            ('asin(', 'acos(', 'atan(', 'pow(', 'log('),
            ('radians(', 'degrees(', 'log10(', '(', ')'),
            ('7', '8', '9', '/', 'C'),
            ('4', '5', '6', '*', '**'),
            ('1', '2', '3', '-', ' '),
            ('0', '.', ' ', '+', ' ')
        ]

        for c in range(5): 
            frame_calc.grid_columnconfigure(c, weight=1)
        
        for r, linha in enumerate(botoes):
            # Garante que as colunas fiquem centralizadas e uniformes
            frame_calc.grid_columnconfigure(r, weight=1) 
            for c, texto in enumerate(linha):
                if texto == ' ': 
                    continue
                
                # Identifica se é um número, operação básica ou função científica
                if texto.isdigit() or texto == '.':
                    cor_fundo, cor_hover = "#3A3A3A", "#4A4A4A"
                elif texto in ['/', '*', '-', '+', '**', 'C', '(', ')']:
                    cor_fundo, cor_hover = "#3498DB", "#2980B9"
                else: # Funções do Math
                    cor_fundo, cor_hover = "#9B59B6", "#8E44AD" 
                
                if texto == 'C':
                    cor_fundo, cor_hover = "#E74C3C", "#C0392B"

                texto_exibicao = texto.replace('(', '') if texto != '(' else '('
                btn = ctk.CTkButton(frame_calc, text=texto_exibicao, width=50, height=35, 
                                    font=("Roboto", 12, "bold"),
                                    fg_color=cor_fundo, hover_color=cor_hover,
                                    command=lambda t=texto: self.inserir_simbolo(t))
                btn.grid(row=r, column=c, padx=3, pady=3, sticky="ew")

    def inserir_simbolo(self, simbolo):
        if simbolo == 'C':
            self.inp_expr.delete(0, 'end')
        else:
            self.inp_expr.insert('end', simbolo)

    def usar_formula(self, variaveis, expressao):
        # Joga a fórmula escolhida na calculadora (campos Variáveis e Fórmula)
        self.inp_vars.delete(0, 'end')
        self.inp_vars.insert(0, variaveis)
        self.inp_expr.delete(0, 'end')
        self.inp_expr.insert(0, expressao)

    @staticmethod
    def _tornar_clicavel(widgets, comando):
        for w in widgets:
            w.bind("<Button-1>", lambda e, cmd=comando: cmd())

    def carregar_fixas(self):
        # Fórmulas fixas vêm do catálogo FORMULAS_FIXAS em core/calculos.py
        for f in FORMULAS_FIXAS:
            card = ctk.CTkFrame(self.frame_fixas, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=5)

            lbl_nome = ctk.CTkLabel(card, text=f["nome"], font=("Roboto", 13, "bold"), anchor="w", justify="left")
            lbl_nome.pack(anchor="w", padx=10, pady=(8, 0))

            detalhes = f"{f['descricao']}\nVars: {f['variaveis']}\nExpr: {f['expressao']}"
            lbl_info = ctk.CTkLabel(card, text=detalhes, font=("Roboto", 11), anchor="w", justify="left", wraplength=280)
            lbl_info.pack(anchor="w", padx=10, pady=(0, 8))

            self._tornar_clicavel([card, lbl_nome, lbl_info],
                                  lambda v=f["variaveis"], x=f["expressao"]: self.usar_formula(v, x))

    def carregar_lista(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        formulas = self.repo.listar_todas()

        if not formulas:
            ctk.CTkLabel(self.frame_lista, text="Nenhuma fórmula cadastrada.").pack(pady=20)
            return

        for f in formulas:
            id_f, nome, vars_esp, expr = f[0], f[1], f[2], f[3]

            card = ctk.CTkFrame(self.frame_lista, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5, padx=5)

            btn_del = ctk.CTkButton(card, text="Excluir", width=60, fg_color="#E74C3C", hover_color="#C0392B",
                                    command=lambda i=id_f: self.deletar(i))
            btn_del.pack(side="right", padx=10, pady=10)

            info = f"{nome}\nVars: {vars_esp} | Expr: {expr}"
            lbl_info = ctk.CTkLabel(card, text=info, font=("Roboto", 12), justify="left", anchor="w", wraplength=210)
            lbl_info.pack(side="left", padx=10, pady=10)

            self._tornar_clicavel([card, lbl_info],
                                  lambda v=vars_esp, x=expr: self.usar_formula(v, x))

    def salvar_nova(self):
        nome = self.inp_nome.get()
        desc = self.inp_desc.get()
        vars_esp = self.inp_vars.get()
        expr = self.inp_expr.get()
        
        if nome and vars_esp and expr:
            self.repo.salvar_formula(nome, desc, vars_esp, expr)
            
            self.inp_nome.delete(0, 'end')
            self.inp_desc.delete(0, 'end')
            self.inp_vars.delete(0, 'end')
            self.inp_expr.delete(0, 'end')
            
            self.carregar_lista()

    def deletar(self, id_formula):
        self.repo.deletar_formula(id_formula)
        self.carregar_lista()