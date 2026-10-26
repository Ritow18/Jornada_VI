import math

class CalculadorRigging:
    
    @staticmethod
    def calcular_carga_bruta(peso_liquido: float, peso_lingada: float, peso_balancim: float = 0.0) -> float:
        # Soma o peso da carga com os acessórios (cintas, manilhas e balancim).
        if peso_liquido <= 0:
            raise ValueError("O peso líquido da carga deve ser maior que zero.")
        return round(peso_liquido + peso_lingada + peso_balancim, 3)

    @staticmethod
    def calcular_tensao_cinta(peso_aplicado: float, angulo_graus: float, quantidade_pernas: int = 2) -> float:
        # Calcula a tensão em cada perna da cinta considerando a inclinação em relação à vertical.
        # Fórmula: Te = (1 / cos(rad)) * (Pa / qtd_pernas)
        if quantidade_pernas <= 0:
            raise ValueError("A quantidade de pernas deve ser maior que zero.")
            
        angulo_rad = math.radians(angulo_graus)
        cos_angulo = math.cos(angulo_rad)
        
        if cos_angulo <= 0:
            raise ValueError("Ângulo de inclinação inválido.")
            
        tensao = (1 / cos_angulo) * (peso_aplicado / quantidade_pernas)
        return round(tensao, 3)

    @staticmethod
    def calcular_taxa_utilizacao(carga_atuante: float, capacidade_nominal: float) -> dict:
        #Calcula a Taxa de Utilização (TU) e verifica se atende ao limite de segurança (máximo 85%).
        if capacidade_nominal <= 0:
            raise ValueError("A capacidade nominal deve ser maior que zero.")
            
        tu_percentual = (carga_atuante / capacidade_nominal) * 100
        aprovado = tu_percentual <= 85.0
        
        return {
            "tu_percentual": round(tu_percentual, 2),
            "aprovado": aprovado,
            "status": "APROVADO" if aprovado else "REPROVADO (Acima do limite de 85%)"
        }

    @staticmethod
    def calcular_esforco_sapatas(peso_carga_kgf: float, raio_operacao_m: float, 
                                 dist_eixo_sapata_m: float, abertura_sapatas_m: float, 
                                 peso_guindaste_caminhao_kgf: float) -> float:
        
        # Calcula o esforço máximo em uma das sapatas (kgf).
        momento = peso_carga_kgf * raio_operacao_m
        forca_adicional = momento / (dist_eixo_sapata_m + abertura_sapatas_m)
        esforco_sapata = (peso_guindaste_caminhao_kgf / 2) + forca_adicional
        return round(esforco_sapata, 2)

    @staticmethod
    def calcular_rmet(esforco_sapata_kgf: float, largura_dormente_cm: float, 
                      comprimento_dormente_cm: float, qtd_dormentes: int = 1) -> float:

        # Calcula a Resistência Mínima Exigida do Terreno (RMET) em kgf/cm².
        area_patolamento_cm2 = largura_dormente_cm * comprimento_dormente_cm * qtd_dormentes
        if area_patolamento_cm2 <= 0:
            raise ValueError("A área de patolamento deve ser maior que zero.")
            
        rmet = esforco_sapata_kgf / area_patolamento_cm2
        return round(rmet, 2)

class MotorFormulasCustomizadas:
    
    # Interpretador seguro completo. trigonometria, logaritmos, exponenciação e comparadores nativos.
    @staticmethod
    def avaliar_expressao(expressao: str, valores_variaveis: dict) -> float:
        # funções matemáticas seguras que um engenheiro pode precisar
        ambiente_seguro = {
            "__builtins__": None,
            # Funções Nativas
            "abs": abs,       # Valor absoluto
            "min": min,       # Retorna o menor valor
            "max": max,       # Retorna o maior valor
            "round": round,   # Arredondamento
            
            # Trigonometria e Conversões
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin, # Arco-seno 
            "acos": math.acos,
            "atan": math.atan,
            "radians": math.radians, # Graus para radianos
            "degrees": math.degrees, # Radianos para graus
            
            # Álgebra e Logaritmos
            "sqrt": math.sqrt,       # Raiz quadrada
            "pow": math.pow,         # Potência (também pode usar ** na fórmula)
            "log": math.log,         # Logaritmo natural
            "log10": math.log10,     # Logaritmo base 10
            
            # Constantes
            "pi": math.pi,
            "e": math.e
        }
        
        ambiente_seguro.update(valores_variaveis)
        
        try:
            resultado = eval(expressao, ambiente_seguro)
            return round(float(resultado), 4)
        except ZeroDivisionError:
            raise ValueError("Erro: A fórmula resultou em uma divisão por zero.")
        except NameError as e:
            raise ValueError(f"Erro: Variável ou função desconhecida na fórmula. Detalhe: {e}")
        except SyntaxError:
            raise ValueError("Erro: A fórmula possui um erro de sintaxe (ex: parênteses faltando).")
        except Exception as e:
            raise ValueError(f"Erro inesperado no cálculo: {e}")

# Teste com fórmula complexa
if __name__ == "__main__":
    motor = MotorFormulasCustomizadas()
    
    # Exemplo: uma força de arrasto que usa max(), potência (**) e trigonometria
    formula_teste = "max(forca_base, (vento ** 2) * area * cos(radians(angulo)))"
    
    valores = {
        "forca_base": 500.0,
        "vento": 35.5,
        "area": 12.0,
        "angulo": 45
    }
    
    resultado = motor.avaliar_expressao(formula_teste, valores)
    print(f"Fórmula: {formula_teste}")
    print(f"Resultado final calculado: {resultado:.2f}")