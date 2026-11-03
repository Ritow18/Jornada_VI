import math

class CalculadorRigging:
    
    @staticmethod
    def calcular_carga_bruta(peso_liquido: float, peso_lingada: float, peso_balancim: float = 0.0) -> float:
        if peso_liquido <= 0:
            raise ValueError("O peso líquido da carga deve ser maior que zero.")
        return round(peso_liquido + peso_lingada + peso_balancim, 5)

    @staticmethod
    def calcular_tensao_cinta(peso_aplicado: float, angulo_graus: float, quantidade_pernas: int = 2) -> float:
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
        momento = peso_carga_kgf * raio_operacao_m
        forca_adicional = momento / (dist_eixo_sapata_m + abertura_sapatas_m)
        esforco_sapata = (peso_guindaste_caminhao_kgf / 2) + forca_adicional
        return round(esforco_sapata, 2)

    @staticmethod
    def calcular_rmet(esforco_sapata_kgf: float, largura_dormente_cm: float, 
                      comprimento_dormente_cm: float, qtd_dormentes: int = 1) -> float:
        area_patolamento_cm2 = largura_dormente_cm * comprimento_dormente_cm * qtd_dormentes
        if area_patolamento_cm2 <= 0:
            raise ValueError("A área de patolamento deve ser maior que zero.")
            
        rmet = esforco_sapata_kgf / area_patolamento_cm2
        return round(rmet, 2)

    @staticmethod
    def interpolar_capacidade(tabela_carga: dict, comprimento_lanca: float, raio_operacao: float) -> float:
        chave_lanca = str(float(comprimento_lanca))
        
        if chave_lanca not in tabela_carga:
            chave_lanca_int = str(int(comprimento_lanca))
            if chave_lanca_int in tabela_carga:
                chave_lanca = chave_lanca_int
            else:
                raise ValueError(f"Comprimento de lança ({comprimento_lanca}m) não encontrado na tabela deste guindaste.")

        curva_raios = tabela_carga[chave_lanca]
        raios_disponiveis = sorted([float(r) for r in curva_raios.keys()])
        
        if raio_operacao < raios_disponiveis[0] or raio_operacao > raios_disponiveis[-1]:
            raise ValueError(
                f"Raio de {raio_operacao}m fora dos limites seguros para a lança de {comprimento_lanca}m "
                f"(Mín: {raios_disponiveis[0]}m | Máx: {raios_disponiveis[-1]}m)."
            )

        for r in raios_disponiveis:
            if math.isclose(raio_operacao, r, abs_tol=1e-4):
                chave_r = str(r) if str(r) in curva_raios else str(int(r))
                return round(float(curva_raios[chave_r]), 3) 

        for i in range(len(raios_disponiveis) - 1):
            r1 = raios_disponiveis[i]
            r2 = raios_disponiveis[i + 1]
            
            if r1 < raio_operacao < r2:
                chave_r1 = str(r1) if str(r1) in curva_raios else str(int(r1))
                chave_r2 = str(r2) if str(r2) in curva_raios else str(int(r2))
                
                c1 = float(curva_raios[chave_r1])
                c2 = float(curva_raios[chave_r2])
                
                capacidade_interpolada = c1 + ((raio_operacao - r1) / (r2 - r1)) * (c2 - c1)
                return round(capacidade_interpolada, 3) 

        raise ValueError("Erro inesperado ao processar a interpolação da tabela de carga.")

class MotorFormulasCustomizadas:
    @staticmethod
    def avaliar_expressao(expressao: str, valores_variaveis: dict) -> float:
        ambiente_seguro = {
            "__builtins__": None,
            "abs": abs, "min": min, "max": max, "round": round,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "acos": math.acos, "atan": math.atan,
            "radians": math.radians, "degrees": math.degrees,
            "sqrt": math.sqrt, "pow": math.pow, "log": math.log, "log10": math.log10,
            "pi": math.pi, "e": math.e
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

FORMULAS_FIXAS = [
    {
        "nome": "Carga Bruta",
        "descricao": "Soma o peso líquido da carga com os acessórios (lingada e balancim).",
        "variaveis": "peso_liquido, peso_lingada, peso_balancim",
        "expressao": "peso_liquido + peso_lingada + peso_balancim",
    },
    {
        "nome": "Tensão na Cinta",
        "descricao": "Tensão em cada perna da cinta, considerando a inclinação em relação à vertical.",
        "variaveis": "peso_aplicado, angulo_graus, quantidade_pernas",
        "expressao": "(1 / cos(radians(angulo_graus))) * (peso_aplicado / quantidade_pernas)",
    },
    {
        "nome": "Taxa de Utilização (TU)",
        "descricao": "Percentual da capacidade nominal em uso. Limite de segurança: 85%.",
        "variaveis": "carga_atuante, capacidade_nominal",
        "expressao": "(carga_atuante / capacidade_nominal) * 100",
    },
    {
        "nome": "Esforço nas Sapatas (kgf)",
        "descricao": "Esforço máximo em uma das sapatas do guindaste.",
        "variaveis": "peso_guindaste_caminhao_kgf, peso_carga_kgf, raio_operacao_m, dist_eixo_sapata_m, abertura_sapatas_m",
        "expressao": "(peso_guindaste_caminhao_kgf / 2) + (peso_carga_kgf * raio_operacao_m) / (dist_eixo_sapata_m + abertura_sapatas_m)",
    },
    {
        "nome": "RMET (kgf/cm²)",
        "descricao": "Resistência Mínima Exigida do Terreno, pela área de patolamento.",
        "variaveis": "esforco_sapata_kgf, largura_dormente_cm, comprimento_dormente_cm, qtd_dormentes",
        "expressao": "esforco_sapata_kgf / (largura_dormente_cm * comprimento_dormente_cm * qtd_dormentes)",
    },
    {
        "nome": "Interpolação Linear de Capacidade",
        "descricao": "Capacidade para um raio entre dois pontos (r1, c1) e (r2, c2) da tabela de carga.",
        "variaveis": "raio_operacao, r1, r2, c1, c2",
        "expressao": "c1 + ((raio_operacao - r1) / (r2 - r1)) * (c2 - c1)",
    },
]

if __name__ == "__main__":
    motor = MotorFormulasCustomizadas()
    formula_teste = "max(forca_base, (vento ** 2) * area * cos(radians(angulo)))"
    valores = {"forca_base": 500.0, "vento": 35.5, "area": 12.0, "angulo": 45}
    resultado = motor.avaliar_expressao(formula_teste, valores)
    print(f"Fórmula: {formula_teste}")
    print(f"Resultado final calculado: {resultado:.2f}")