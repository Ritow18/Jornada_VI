import customtkinter as ctk
from TFormulas import TelaCriarFormula

# Configuração visual padrão do sistema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Guindastes Ribas - Automação de Rigging")
        self.geometry("800x600")
        
        self.frame_atual = None
        
        # Pula qualquer login e já chama o Dashboard/Fórmulas direto na inicialização
        self.mostrar_dashboard() 

    def mostrar_dashboard(self):
        if self.frame_atual:
            self.frame_atual.destroy()
            
        self.frame_atual = TelaCriarFormula(self)
        self.frame_atual.pack(expand=True, fill="both", padx=20, pady=20)

if __name__ == "__main__":
    app = App()
    app.mainloop()