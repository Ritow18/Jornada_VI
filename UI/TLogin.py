import customtkinter as ctk

class TelaLogin(ctk.CTkFrame):
    def __init__(self, master, callback_sucesso):
        super().__init__(master)
        # Esse callback é a função que vai "matar" o login e chamar o dashboard
        self.callback_sucesso = callback_sucesso 
        
        # --- Desenhando a Tela ---
        self.titulo = ctk.CTkLabel(self, text="Rigging System - Acesso", font=("Roboto", 24, "bold"))
        self.titulo.pack(pady=(40, 20))

        self.input_crea = ctk.CTkEntry(self, placeholder_text="Registro (CREA/Matrícula)", width=250)
        self.input_crea.pack(pady=10)

        self.input_senha = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=250)
        self.input_senha.pack(pady=10)

        self.btn_entrar = ctk.CTkButton(self, text="ENTRAR", width=250, command=self.validar_login)
        self.btn_entrar.pack(pady=20)
        
        self.mensagem_erro = ctk.CTkLabel(self, text="", text_color="red")
        self.mensagem_erro.pack()

    def validar_login(self):
        # Teste estático inicial (Depois vamos ligar isso no SQLite!)
        usuario = self.input_crea.get()
        senha = self.input_senha.get()
        
        if usuario == "admin" and senha == "123":
            self.mensagem_erro.configure(text="")
            print("Autenticado! Indo para o sistema...")
            self.callback_sucesso() # Chama a troca de tela
        else:
            self.mensagem_erro.configure(text="Credenciais inválidas. Tente admin / 123")