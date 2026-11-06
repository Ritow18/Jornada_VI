from core.calculos import CalculadorRigging

def eh_cinta(tipo: str) -> bool:
    return "cinta" in (tipo or "").lower()

def eh_balancim(tipo: str) -> bool:
    return "balancim" in (tipo or "").lower()

def capacidade_efetiva(capac_kg: float, desgaste_perc: float) -> float:
    """Capacidade efetiva do acessório em kg descontando o desgaste."""
    if not 0 <= desgaste_perc < 100:
        raise ValueError("O desgaste deve estar entre 0 e 100%.")
    return capac_kg * (1 - desgaste_perc / 100)

def calcular_plano(carga_liquida_kg: float, itens: list, capacidade_nominal_kg: float,
                   raio_m: float, sapatas: dict = None) -> dict:
    
    if carga_liquida_kg <= 0:
        raise ValueError("O peso líquido da carga deve ser maior que zero.")

    avisos = []
    lingada_kg = sum(i["peso_unit_kg"] * i["qtd"] for i in itens if not eh_balancim(i["tipo"]))
    balancim_kg = sum(i["peso_unit_kg"] * i["qtd"] for i in itens if eh_balancim(i["tipo"]))

    for i in itens:
        if not i.get("peso_unit_kg"):
            avisos.append(f"{i['codigo']}: sem peso unitário cadastrado (contado como 0 kg na carga bruta).")

    # 1. Carga Bruta Total (tudo em kg)
    carga_bruta_kg = CalculadorRigging.calcular_carga_bruta(
        carga_liquida_kg, lingada_kg, balancim_kg
    )

    # 2. Taxa de Utilização do Guindaste (Dispara Hard Stop se TU > 100%)
    tu_guindaste = CalculadorRigging.calcular_taxa_utilizacao(carga_bruta_kg, capacidade_nominal_kg)

    # 3. Análise Individual dos Acessórios
    linhas = []
    for i in itens:
        aplicada_kg = i["carga_aplicada_kg"] if i.get("carga_aplicada_kg") else carga_bruta_kg
        
        # Suporta tanto capac_kg quanto a antiga capac_ton (convertendo para kg)
        cap_base_kg = i.get("capac_kg") or (i.get("capac_ton", 0) * 1000)
        cap_ef_kg = capacidade_efetiva(cap_base_kg, i["desgaste_perc"])
        
        if cap_ef_kg <= 0:
            raise ValueError(f"{i['codigo']}: capacidade efetiva zerada (verifique a capacidade cadastrada e o desgaste).")

        if eh_cinta(i["tipo"]):
            esforco_kg = CalculadorRigging.calcular_tensao_cinta(
                aplicada_kg, i.get("angulo") or 0.0, i.get("pernas") or 2
            )
        else:
            esforco_kg = round(aplicada_kg / i["qtd"], 2)

        tu_acessorio = CalculadorRigging.calcular_taxa_utilizacao(esforco_kg, cap_ef_kg)
        
        linhas.append({
            **i,
            "carga_aplicada_kg": round(aplicada_kg, 2),
            "esforco_kg": esforco_kg,
            "capac_efetiva_kg": round(cap_ef_kg, 2),
            "tu_percentual": tu_acessorio["tu_percentual"],
            "aprovado": tu_acessorio["aprovado"],
        })

    # 4. Cálculo de Reação de Apoio nas Sapatas e Solo (RMET)
    res_sapatas = None
    if sapatas:
        esforco_kgf = CalculadorRigging.calcular_esforco_sapatas(
            peso_carga_kg=carga_bruta_kg,
            raio_operacao_m=raio_m,
            dist_eixo_sapata_m=sapatas["dist_eixo_m"],
            abertura_sapatas_m=sapatas["abertura_m"],
            peso_guindaste_caminhao_kg=sapatas["peso_guindaste_kgf"]
        )
        
        rmet = CalculadorRigging.calcular_rmet(
            esforco_sapata_kg=esforco_kgf,
            largura_dormente_cm=sapatas["dormente_larg_cm"],
            comprimento_dormente_cm=sapatas["dormente_comp_cm"],
            qtd_dormentes=sapatas.get("dormente_qtd") or 1
        )
        
        resist = sapatas.get("resistencia_terreno")
        res_sapatas = {
            "esforco_kgf": esforco_kgf,
            "rmet": rmet,
            "resistencia_terreno": resist,
            "aprovado": None if resist is None else rmet <= resist,
        }

    # Parecer técnico global da operação
    aprovado = (tu_guindaste["aprovado"]
                and all(l["aprovado"] for l in linhas)
                and (res_sapatas is None or res_sapatas["aprovado"] is not False))

    return {
        "carga_liquida_kg": carga_liquida_kg,
        "lingada_kg": round(lingada_kg, 2),
        "balancim_kg": round(balancim_kg, 2),
        "carga_bruta_kg": carga_bruta_kg,
        "capacidade_kg": capacidade_nominal_kg,
        "tu_guindaste": tu_guindaste,
        "linhas": linhas,
        "sapatas": res_sapatas,
        "avisos": avisos,
        "aprovado": aprovado,
    }