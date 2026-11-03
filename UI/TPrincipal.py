import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

import customtkinter as ctk
from TFormulas import TelaCriarFormula
from TOperacao import TelaOperacao
from TFrota import TelaFrota
from TAcessorios import TelaAcessorios

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

LARGURA_BTN = 180
ALTURA_BTN = 36

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Guindastes Ribas - Automação de Rigging")
        self.geometry("1000x700")

        # Configurando o grid da janela principal (1 linha, 2 colunas)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== BARRA LATERAL ====================
        self.frame_menu = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_rowconfigure(5, weight=1) # Empurra o resto para cima

        self.logo_label = ctk.CTkLabel(self.frame_menu, text="RIBAS\nRigging", font=("Roboto", 24, "bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        self.btn_operacao = ctk.CTkButton(self.frame_menu, text="Simular Içamento", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_operacao)
        self.btn_operacao.grid(row=1, column=0, padx=20, pady=10)

        self.btn_formulas = ctk.CTkButton(self.frame_menu, text="Fórmulas Customizadas", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_formulas)
        self.btn_formulas.grid(row=2, column=0, padx=20, pady=10)

        self.btn_frota = ctk.CTkButton(self.frame_menu, text="Gestão de Frota", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_frota)
        self.btn_frota.grid(row=3, column=0, padx=20, pady=10)

        self.btn_acessorios = ctk.CTkButton(self.frame_menu, text="Gestão de Acessórios", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_acessorios)
        self.btn_acessorios.grid(row=4, column=0, padx=20, pady=10)

        # É aqui dentro que as telas vão aparecer
        self.frame_principal = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_principal.grid(row=0, column=1, sticky="nsew")
        
        self.tela_atual = None

        # O aplicativo já inicia abrindo a tela de Operação por padrão
        self.abrir_tela_operacao()

    def mostrar_tela(self, classe_tela):
        # Destrói a tela anterior antes de desenhar a nova
        if self.tela_atual:
            self.tela_atual.destroy()
        
        # Cria a nova tela passando o frame_principal como 'master'
        self.tela_atual = classe_tela(self.frame_principal)
        self.tela_atual.pack(expand=True, fill="both")

    def abrir_tela_operacao(self):
        self.mostrar_tela(TelaOperacao)

    def abrir_tela_formulas(self):
        self.mostrar_tela(TelaCriarFormula)

    def abrir_tela_frota(self):
        self.mostrar_tela(TelaFrota)

    def abrir_tela_acessorios(self):
        self.mostrar_tela(TelaAcessorios)

if __name__ == "__main__":
    app = App()
    app.mainloop()