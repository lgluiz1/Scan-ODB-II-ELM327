"""Diagnostic advisor for multi-DTC correlation analysis and technical guidance.
Strictly neutral, non-presumptive investigation advice.
"""
from typing import List, Dict, Any


class DiagnosticAdvisor:
    """Analyzes combinations of active DTCs and provides investigative context."""

    @staticmethod
    def analyze_correlations(dtc_list: List[str]) -> List[Dict[str, Any]]:
        codes = set(c.upper() for c in dtc_list)
        correlations: List[Dict[str, Any]] = []

        # 1. Correlation: MAP (P0106/P0105) + Misfire (P0300/P0301/P0302/P0303)
        map_codes = {"P0105", "P0106", "P0107", "P0108"}
        misfire_codes = {"P0300", "P0301", "P0302", "P0303"}

        active_map = codes.intersection(map_codes)
        active_misfire = codes.intersection(misfire_codes)

        if active_map and active_misfire:
            correlations.append({
                "title": f"Correlação: Pressão do Coletor ({', '.join(sorted(active_map))}) + Falha de Combustão ({', '.join(sorted(active_misfire))})",
                "severity": "Alta Prioridade",
                "summary": "Uma leitura incorreta ou oscilante de pressão do coletor descalibra o cálculo de massa de ar da ECU, podendo causar mistura excessivamente pobre ou rica momentânea e provocar falhas de queima (misfire) sob carga.",
                "checklist": [
                    "Conector e chicote do sensor MAP: verificar firmeza dos terminais, oxidação e se houve intervenção/emenda na fiação (ex: derivações do antigo kit GNV).",
                    "Estanqueidade do coletor de admissão: verificar se as furações/tampões dos antigos bicos de GNV apresentam entrada falsa de ar.",
                    "Alimentação de 5V de referência e aterramento da ECU sob esforço mecânico/vibração do motor.",
                    "Linha de vácuo e vedação das juntas do coletor e corpo de borboleta.",
                    "Condição das velas e bobinas dos 3 cilindros (a falha de queima sob carga em subidas é típica de deficiência no secundário de ignição ou mistura descalibrada)."
                ]
            })

        # 2. Correlation: Sonda Lambda (P0130-P0135) + Mistura Pobre/Rica (P0171/P0172)
        lambda_codes = {"P0130", "P0131", "P0132", "P0133", "P0134", "P0135"}
        fuel_trim_codes = {"P0171", "P0172"}

        active_lambda = codes.intersection(lambda_codes)
        active_trim = codes.intersection(fuel_trim_codes)

        if active_lambda and active_trim:
            correlations.append({
                "title": f"Correlação: Sonda Lambda ({', '.join(sorted(active_lambda))}) + Correção de Mistura ({', '.join(sorted(active_trim))})",
                "severity": "Alta Prioridade",
                "summary": "A ECU acusa falha no controle de malha fechada e atingiu o limite de correção dos fuel trims (STFT/LTFT).",
                "checklist": [
                    "Verificar se o conector da sonda pré-catalisador possui fiação íntegra ou sinais de emenda/emulador de GNV anterior.",
                    "Testar se há entrada falsa de ar no escapamento (junta do coletor de escape ou flexível com trinca antes da sonda).",
                    "Medir a pressão e vazão da linha de combustível na flauta de injeção.",
                    "Inspecionar se a sonda está realmente travada ou se a mistura no cilindro está fisicamente desbalanceada."
                ]
            })

        # 3. Correlation: Misfire (P0300) + Eficiência Catalítica (P0420)
        if active_misfire and "P0420" in codes:
            correlations.append({
                "title": "Correlação: Falha de Ignição/Combustão (Misfire) + Eficiência Catalítica (P0420)",
                "severity": "Alerta Importante",
                "summary": "Combustível não queimado resultante das falhas de ignição é direcionado ao catalisador, elevando sua temperatura e sobrecarregando o elemento.",
                "checklist": [
                    "IMPORTANTE: Não substitua o catalisador antes de solucionar definitivamente as falhas de combustão (P0300 / P0106).",
                    "Corrigir primeiro a causa raiz do misfire e da mistura.",
                    "Após normalizar o funcionamento do motor, monitorar o sinal da sonda pós-catalisador para verificar se o catalisador recupera a eficiência."
                ]
            })

        return correlations
