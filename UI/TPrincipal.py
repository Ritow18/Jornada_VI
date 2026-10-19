import customtkinter as ctk
from TLogin import TelaLogin

# Configuração visual padrão do sistema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Guindastes Ribas - Automação de Rigging")
        self.geometry("800x600")
        
        # Inicia mostrando a tela de login
        self.frame_atual = None
        self.mostrar_tela_login()

    def mostrar_tela_login(self):
        if self.frame_atual:
            self.frame_atual.destroy() # Limpa a tela anterior
            
        # Cria a tela de login passando a função de sucesso
        self.frame_atual = TelaLogin(self, callback_sucesso=self.mostrar_dashboard)
        self.frame_atual.pack(expand=True, fill="both", padx=20, pady=20)

    def mostrar_dashboard(self):
        if self.frame_atual:
            self.frame_atual.destroy()
            
        # Por enquanto, só uma mensagem provando que o login funcionou
        self.frame_atual = ctk.CTkFrame(self)
        self.frame_atual.pack(expand=True, fill="both", padx=20, pady=20)
        
        titulo = ctk.CTkLabel(self.frame_atual, text="Bem-vindo ao Sistema de Rigging!", font=("Roboto", 28))
        titulo.pack(pady=100)

if __name__ == "__main__":
    app = App()
    app.mainloop() # Mantém a janela aberta