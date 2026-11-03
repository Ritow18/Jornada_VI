"""Orquestra os cálculos de um Plano de Rigging completo.

Sem interface e sem banco: recebe dados simples e devolve um dicionário com
todos os resultados. Usa as fórmulas já existentes em CalculadorRigging.
"""
from core.calculos import CalculadorRigging


def eh_cinta(tipo: str) -> bool:
    return "cinta" in (tipo or "").lower()


def eh_balancim(tipo: str) -> bool:
    return "balancim" in (tipo or "").lower()


def capacidade_efetiva(capac_ton: float, desgaste_perc: float) -> float:
    """Capacidade do acessório descontando o desgaste cadastrado."""
    if not 0 <= desgaste_perc < 100:
        raise ValueError("O desgaste deve estar entre 0 e 100%.")
    return capac_ton * (1 - desgaste_perc / 100)


def calcular_plano(carga_liquida_kg: float, itens: list, capacidade_nominal_ton: float,
                   raio_m: float, sapatas: dict = None) -> dict:
    """
    itens: lista de dicts com
        tipo, codigo, qtd, peso_unit_kg, capac_ton, desgaste_perc,
        angulo (cintas), pernas (cintas), carga_aplicada_kg (opcional)
    sapatas (opcional): peso_guindaste_kgf, dist_eixo_m, abertura_m,
        dormente_larg_cm, dormente_comp_cm, dormente_qtd, resistencia_terreno
    """
    if carga_liquida_kg <= 0:
        raise ValueError("O peso líquido da carga deve ser maior que zero.")

    avisos = []
    lingada_kg = sum(i["peso_unit_kg"] * i["qtd"] for i in itens if not eh_balancim(i["tipo"]))
    balancim_kg = sum(i["peso_unit_kg"] * i["qtd"] for i in itens if eh_balancim(i["tipo"]))

    for i in itens:
        if not i["peso_unit_kg"]:
            avisos.append(f"{i['codigo']}: sem peso unitário cadastrado (contado como 0 kg na carga bruta).")

    bruta_ton = CalculadorRigging.calcular_carga_bruta(
        carga_liquida_kg / 1000, lingada_kg / 1000, balancim_kg / 1000)

    tu_guindaste = CalculadorRigging.calcular_taxa_utilizacao(bruta_ton, capacidade_nominal_ton)

    linhas = []
    for i in itens:
        aplicada_ton = i["carga_aplicada_kg"] / 1000 if i.get("carga_aplicada_kg") else bruta_ton
        cap_ef = capacidade_efetiva(i["capac_ton"], i["desgaste_perc"])
        if cap_ef <= 0:
            raise ValueError(f"{i['codigo']}: capacidade efetiva zerada (verifique capacidade e desgaste).")

        if eh_cinta(i["tipo"]):
            esforco = CalculadorRigging.calcular_tensao_cinta(
                aplicada_ton, i.get("angulo") or 0.0, i.get("pernas") or 2)
        else:
            esforco = round(aplicada_ton / i["qtd"], 3)

        tu = CalculadorRigging.calcular_taxa_utilizacao(esforco, cap_ef)
        linhas.append({
            **i,
            "carga_aplicada_ton": round(aplicada_ton, 3),
            "esforco_ton": esforco,
            "capac_efetiva_ton": round(cap_ef, 3),
            "tu_percentual": tu["tu_percentual"],
            "aprovado": tu["aprovado"],
        })

    res_sapatas = None
    if sapatas:
        esforco_kgf = CalculadorRigging.calcular_esforco_sapatas(
            peso_carga_kgf=bruta_ton * 1000,
            raio_operacao_m=raio_m,
            dist_eixo_sapata_m=sapatas["dist_eixo_m"],
            abertura_sapatas_m=sapatas["abertura_m"],
            peso_guindaste_caminhao_kgf=sapatas["peso_guindaste_kgf"])
        rmet = CalculadorRigging.calcular_rmet(
            esforco_kgf, sapatas["dormente_larg_cm"], sapatas["dormente_comp_cm"],
            sapatas.get("dormente_qtd") or 1)
        resist = sapatas.get("resistencia_terreno")
        res_sapatas = {
            "esforco_kgf": esforco_kgf,
            "rmet": rmet,
            "resistencia_terreno": resist,
            "aprovado": None if resist is None else rmet <= resist,
        }

    aprovado = (tu_guindaste["aprovado"]
                and all(l["aprovado"] for l in linhas)
                and (res_sapatas is None or res_sapatas["aprovado"] is not False))

    return {
        "carga_liquida_kg": carga_liquida_kg,
        "lingada_kg": round(lingada_kg, 3),
        "balancim_kg": round(balancim_kg, 3),
        "carga_bruta_ton": bruta_ton,
        "capacidade_ton": capacidade_nominal_ton,
        "tu_guindaste": tu_guindaste,
        "linhas": linhas,
        "sapatas": res_sapatas,
        "avisos": avisos,
        "aprovado": aprovado,
    }