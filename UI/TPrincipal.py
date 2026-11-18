import os
import sys

if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from UI.TDashboard import TelaOperacao
from TFrota import TelaFrota
from TAcessorios import TelaAcessorios
from TPlano import TelaPlano

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

LARGURA_BTN = 180
ALTURA_BTN = 36

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Guindastes Ribas - Automação de Rigging")
        self.geometry("1100x750") 

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.frame_menu = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.frame_menu, text="RIBAS\nRigging", font=("Roboto", 24, "bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        self.btn_operacao = ctk.CTkButton(self.frame_menu, text="Início / Dashboard", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_operacao)
        self.btn_operacao.grid(row=1, column=0, padx=20, pady=10)

        self.btn_acessorios = ctk.CTkButton(self.frame_menu, text="Gestão de Acessórios", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_acessorios)
        self.btn_acessorios.grid(row=2, column=0, padx=20, pady=10)

        self.btn_frota = ctk.CTkButton(self.frame_menu, text="Gestão de Frota", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_frota)
        self.btn_frota.grid(row=3, column=0, padx=20, pady=10)

        self.btn_plano = ctk.CTkButton(self.frame_menu, text="Plano de Rigging", width=LARGURA_BTN, height=ALTURA_BTN, command=self.abrir_tela_plano)
        self.btn_plano.grid(row=4, column=0, padx=20, pady=10)

        self.frame_principal = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_principal.grid(row=0, column=1, sticky="nsew")
        
        self.telas_cacheadas = {} 
        self.tela_atual = None
        
        self.abrir_tela_operacao()

    def mostrar_tela(self, nome_tela, classe_tela):
        if self.tela_atual:
            self.tela_atual.pack_forget()
            
        if nome_tela not in self.telas_cacheadas:
            nova_tela = classe_tela(self.frame_principal)
            self.telas_cacheadas[nome_tela] = nova_tela
            
        self.tela_atual = self.telas_cacheadas[nome_tela]
        
        if hasattr(self.tela_atual, 'atualizar_dados'):
            self.tela_atual.atualizar_dados()
        
        self.tela_atual.pack(expand=True, fill="both")
        self.update_idletasks()

    # Passamos um "Nome Único" e a Classe da Tela
    def abrir_tela_operacao(self): self.mostrar_tela("Operacao", TelaOperacao)
    def abrir_tela_plano(self):    self.mostrar_tela("Plano", TelaPlano)
    def abrir_tela_frota(self):    self.mostrar_tela("Frota", TelaFrota)
    def abrir_tela_acessorios(self): self.mostrar_tela("Acessorios", TelaAcessorios)

if __name__ == "__main__":
    app = App()
    app.mainloop()