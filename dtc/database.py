"""OBD2 Diagnostic Trouble Code (DTC) database with neutral diagnostic guidance.
Strictly adheres to professional diagnostic standards without assuming component failure.
"""
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class DTCMeta:
    code: str
    description: str
    system: str
    neutral_advice: str
    checklist: List[str]


# Curated database of standard OBD2 DTCs with focus on powertrain, sensors, ignition, and fuel trim
DTC_CATALOG: Dict[str, DTCMeta] = {
    # MAP & Manifold Pressure
    "P0105": DTCMeta(
        code="P0105",
        description="Sensor de Pressão Absoluta do Coletor (MAP) / Barométrico — Mau funcionamento do circuito",
        system="Admissão de Ar",
        neutral_advice="A ECU detectou falha elétrica ou sinal inconsistente no circuito do sensor MAP. Não indica necessariamente que o sensor está danificado.",
        checklist=[
            "Tensão de referência de 5V no conector do sensor",
            "Continuidade e isolamento do sinal até a ECU",
            "Aterramento do circuito do sensor",
            "Presença de oxidação, pinos frouxos ou chicote modificado/reparado",
            "Estanqueidade da tomada de vácuo do coletor"
        ]
    ),
    "P0106": DTCMeta(
        code="P0106",
        description="Sensor de Pressão Absoluta do Coletor (MAP) — Faixa / Desempenho incorreto",
        system="Admissão de Ar / Vácuo",
        neutral_advice="O sinal de pressão do coletor está fora da faixa esperada para a rotação e carga atuais do motor. Pode ser causado por entrada falsa de ar, problema elétrico ou vácuo deficiente.",
        checklist=[
            "Entradas falsas de ar no coletor de admissão, juntas e mangueiras",
            "Tensão de alimentação (5V) e sinal de retorno do sensor MAP",
            "Conector elétrico e chicote (verificar emendas ou derivações antigas)",
            "Vácuo real do motor (verificar estanqueidade das válvulas / compressão)",
            "Corpo de borboleta sujo ou descalibrado",
            "Sensor MAP (verificar resposta com bomba de vácuo)"
        ]
    ),
    "P0107": DTCMeta(
        code="P0107",
        description="Sensor de Pressão Absoluta do Coletor (MAP) — Sinal de entrada baixo",
        system="Admissão de Ar",
        neutral_advice="A tensão do sinal lida pela ECU está abaixo do limite mínimo (possível curto ao terra ou circuito aberto no sinal/alimentação).",
        checklist=[
            "Alimentação de 5V do sensor",
            "Circuito de sinal em curto com a massa ou rompido",
            "Pinos do conector do sensor MAP com mau contato",
            "Pino correspondente no conector da ECU"
        ]
    ),
    "P0108": DTCMeta(
        code="P0108",
        description="Sensor de Pressão Absoluta do Coletor (MAP) — Sinal de entrada alto",
        system="Admissão de Ar",
        neutral_advice="A tensão do sinal lida pela ECU está acima do limite máximo (possível curto ao positivo ou circuito de terra do sensor rompido).",
        checklist=[
            "Continuidade do aterramento do sensor",
            "Curto-circuito do fio de sinal com o positivo (5V ou 12V)",
            "Vácuo excessivamente baixo no coletor por grande entrada de ar ou motor fora de sincronismo"
        ]
    ),

    # Oxygen Sensor & Fuel Trim (Sonda Lambda e Mistura)
    "P0130": DTCMeta(
        code="P0130",
        description="Sensor de Oxigênio (Sonda Lambda Banco 1 Sensor 1) — Mau funcionamento do circuito",
        system="Controle de Emissões / Combustão",
        neutral_advice="Falha detectada no circuito elétrico da sonda pré-catalisador. Verifique fiação, aquecedor e conectores antes de condenar a sonda.",
        checklist=[
            "Chicote elétrico e conector da sonda lambda pré-catalisador",
            "Alimentação de 12V do aquecedor e chaveamento da ECU",
            "Resistência ôhmica do elemento aquecedor da sonda",
            "Aterramentos do motor e da ECU",
            "Sinal de tensão oscilando entre 0.1V e 0.9V em malha fechada"
        ]
    ),
    "P0131": DTCMeta(
        code="P0131",
        description="Sensor de Oxigênio (Sonda Lambda Banco 1 Sensor 1) — Baixa tensão (Sinal pobre)",
        system="Controle de Emissões / Combustão",
        neutral_advice="Sinal da sonda pré-catalisador fixo em valor baixo (< 0.15V). Pode indicar mistura excessivamente pobre real ou falha de leitura.",
        checklist=[
            "Entradas de ar falso no coletor ou antes/próximo à sonda no escape",
            "Pressão e vazão da linha de combustível",
            "Bicos injetores entupidos ou com vazão irregular",
            "Curto do fio de sinal da sonda com a massa"
        ]
    ),
    "P0132": DTCMeta(
        code="P0132",
        description="Sensor de Oxigênio (Sonda Lambda Banco 1 Sensor 1) — Alta tensão (Sinal rico)",
        system="Controle de Emissões / Combustão",
        neutral_advice="Sinal da sonda pré-catalisador fixo em valor alto (> 0.85V). Pode indicar mistura excessivamente rica real ou contaminação.",
        checklist=[
            "Pressão excessiva de combustível",
            "Injetores gotejando ou travados abertos",
            "Sensor MAP ou de temperatura informando valores irreais",
            "Curto do fio de sinal da sonda com tensão positiva"
        ]
    ),
    "P0133": DTCMeta(
        code="P0133",
        description="Sensor de Oxigênio (Sonda Lambda Banco 1 Sensor 1) — Resposta lenta",
        system="Controle de Emissões / Combustão",
        neutral_advice="A sonda está demorando para alternar entre rico e pobre. Pode indicar envelhecimento, contaminação do elemento ou vazamento de escape.",
        checklist=[
            "Vazamentos nas juntas do coletor de escape antes da sonda",
            "Contaminação do sensor por óleo, líquido de arrefecimento ou combustível adulterado",
            "Tempo de resposta do aquecedor"
        ]
    ),
    "P0134": DTCMeta(
        code="P0134",
        description="Sensor de Oxigênio (Sonda Lambda Banco 1 Sensor 1) — Nenhuma atividade detectada",
        system="Controle de Emissões / Combustão",
        neutral_advice="A ECU não detecta variação na leitura da sonda (permanece em tensão de polarização aberta).",
        checklist=[
            "Conexão física e travas do plugue da sonda",
            "Fio de sinal interrompido",
            "Aquecedor inoperante impedindo a sonda de atingir temperatura de trabalho"
        ]
    ),
    "P0135": DTCMeta(
        code="P0135",
        description="Sensor de Oxigênio (Sonda Lambda Banco 1 Sensor 1) — Mau funcionamento do circuito do aquecedor",
        system="Controle de Emissões / Combustão",
        neutral_advice="O circuito do aquecedor da sonda pré-catalisador não está drenando a corrente esperada.",
        checklist=[
            "Fusível de alimentação do aquecedor da sonda",
            "Resistência ôhmica interna do aquecedor (com multímetro nos pinos)",
            "Chicote quanto a rompimento ou atrito no bloco do motor",
            "Sinal de chaveamento de massa vindo da ECU"
        ]
    ),

    # Mistura de Combustível (Fuel Trims)
    "P0171": DTCMeta(
        code="P0171",
        description="Sistema de Combustível Muito Pobre (Banco 1)",
        system="Alimentação de Combustível / Admissão",
        neutral_advice="A ECU atingiu o limite máximo de enriquecimento (STFT/LTFT alto positivo) para compensar excesso de ar ou falta de combustível.",
        checklist=[
            "Entradas de ar falso no coletor de admissão, vácuo do servo-freio e cânister",
            "Pressão e vazão da bomba de combustível e filtro",
            "Vazão e estanqueidade dos bicos injetores",
            "Sinal do sensor MAP indicando pressão menor que a real",
            "Vazamentos no coletor de escape antes da sonda pré"
        ]
    ),
    "P0172": DTCMeta(
        code="P0172",
        description="Sistema de Combustível Muito Rico (Banco 1)",
        system="Alimentação de Combustível / Admissão",
        neutral_advice="A ECU atingiu o limite de empobrecimento (STFT/LTFT alto negativo) para compensar excesso de combustível ou falta de ar.",
        checklist=[
            "Válvula do cânister travada aberta",
            "Pressão de combustível acima do especificado",
            "Bicos injetores travados ou gotejando",
            "Sensor de temperatura do motor (ECT) indicando motor frio indevidamente",
            "Filtro de ar excessivamente obstruído"
        ]
    ),

    # Falhas de Combustão / Misfire (Especialmente relevante para motor 3 cilindros)
    "P0300": DTCMeta(
        code="P0300",
        description="Falha de Combustão Múltipla / Aleatória Detectada (Misfire)",
        system="Ignição e Combustão",
        neutral_advice="A ECU detectou irregularidade na aceleração angular do virabrequim em múltiplos cilindros. Não aponte peças isoladas sem testar ignição, compressão e alimentação.",
        checklist=[
            "Velas de ignição (desgaste, folga dos eletrodos e carbonização)",
            "Bobinas de ignição (tensão, trincas e cabos/conectores)",
            "Alimentação e pulsos dos bicos injetores",
            "Pressão da linha de combustível e qualidade do combustível",
            "Compressão mecânica dos cilindros e vedação das válvulas",
            "Sensor de rotação/fase e roda fônica quanto a sujeira ou oscilação"
        ]
    ),
    "P0301": DTCMeta(
        code="P0301",
        description="Falha de Combustão Detectada — Cilindro 1",
        system="Ignição e Combustão",
        neutral_advice="Falha de combustão específica identificada no cilindro 1.",
        checklist=[
            "Vela e bobina do cilindro 1 (teste invertendo a bobina com o cilindro 2)",
            "Bico injetor do cilindro 1 (vazão e pulso)",
            "Compressão mecânica do cilindro 1",
            "Fiação e conector da bobina/injetor do cilindro 1"
        ]
    ),
    "P0302": DTCMeta(
        code="P0302",
        description="Falha de Combustão Detectada — Cilindro 2",
        system="Ignição e Combustão",
        neutral_advice="Falha de combustão específica identificada no cilindro 2.",
        checklist=[
            "Vela e bobina do cilindro 2 (teste invertendo a bobina com outro cilindro)",
            "Bico injetor do cilindro 2 (vazão e pulso)",
            "Compressão mecânica do cilindro 2",
            "Fiação e conector da bobina/injetor do cilindro 2"
        ]
    ),
    "P0303": DTCMeta(
        code="P0303",
        description="Falha de Combustão Detectada — Cilindro 3",
        system="Ignição e Combustão",
        neutral_advice="Falha de combustão específica identificada no cilindro 3.",
        checklist=[
            "Vela e bobina do cilindro 3 (teste invertendo a bobina com outro cilindro)",
            "Bico injetor do cilindro 3 (vazão e pulso)",
            "Compressão mecânica do cilindro 3",
            "Fiação e conector da bobina/injetor do cilindro 3"
        ]
    ),

    # Eficiência Catalítica
    "P0420": DTCMeta(
        code="P0420",
        description="Eficiência do Sistema Catalítico Abaixo do Limite (Banco 1)",
        system="Emissões / Catalisador",
        neutral_advice="A sonda pós-catalisador está oscilando de forma semelhante à sonda pré-catalisador, indicando redução na capacidade de oxidação do catalisador. Frequentemente consequência de falhas prévias de mistura ou ignição.",
        checklist=[
            "Histórico de falhas de ignição (misfire P0300) que enviaram combustível cru ao catalisador",
            "Histórico de mistura rica ou uso de GNV com regulagem inadequada",
            "Vazamentos de escapamento entre a sonda pré e a sonda pós",
            "Comportamento do sinal da sonda pós-catalisador (deve ser estável em ~0.45V - 0.7V)",
            "Integridade física do miolo do catalisador"
        ]
    ),

    # Temperatura e Admissão
    "P0110": DTCMeta(
        code="P0110",
        description="Sensor de Temperatura do Ar de Admissão (IAT) — Mau funcionamento do circuito",
        system="Admissão de Ar",
        neutral_advice="Sinal elétrico fora da faixa aceitável para o sensor IAT (geralmente integrado ao sensor MAP).",
        checklist=[
            "Conector compartilhado MAP/IAT",
            "Resistência do termistor de temperatura do ar",
            "Fiação e chicote elétrico"
        ]
    ),
    "P0115": DTCMeta(
        code="P0115",
        description="Sensor de Temperatura do Líquido de Arrefecimento (ECT) — Mau funcionamento do circuito",
        system="Arrefecimento / Injeção",
        neutral_advice="Falha elétrica no circuito do sensor de temperatura do motor.",
        checklist=[
            "Conector e chicote do sensor ECT",
            "Sinal de tensão e aterramento do sensor",
            "Funcionamento da válvula termostática"
        ]
    ),

    # Posição de Borboleta e Pedal
    "P0120": DTCMeta(
        code="P0120",
        description="Sensor de Posição da Borboleta / Pedal (TPS) — Mau funcionamento do circuito A",
        system="Aceleração / Borboleta",
        neutral_advice="Falha no circuito do potenciômetro de posição da borboleta ou pedal do acelerador.",
        checklist=[
            "Conector e chicote do corpo de borboleta ou pedal",
            "Tensão de alimentação de 5V e pistas resistivas",
            "Limpeza mecânica da borboleta"
        ]
    ),

    # Rotação e Sincronismo
    "P0335": DTCMeta(
        code="P0335",
        description="Sensor de Posição do Virabrequim (CKP) — Mau funcionamento do circuito",
        system="Sincronismo / Ignição",
        neutral_advice="A ECU não recebe sinal confiável de rotação do motor.",
        checklist=[
            "Conector e fiação do sensor de rotação",
            "Distância (entreferro) e sujeira metálica na ponta do sensor",
            "Integridade dos dentes da roda fônica"
        ]
    ),

    # Tensão do Sistema
    "P0562": DTCMeta(
        code="P0562",
        description="Tensão do Sistema Elétrico — Baixa",
        system="Elétrica / Bateria",
        neutral_advice="A tensão detectada na ECU está abaixo do limite de operação estável (< 10V).",
        checklist=[
            "Tensão de repouso e sob partida da bateria",
            "Regulador de voltagem do alternador",
            "Cabos principais de massa do motor e da carroceria"
        ]
    ),

    # Rede e Comunicação
    "U0100": DTCMeta(
        code="U0100",
        description="Perda de Comunicação com a Unidade de Controle do Motor (ECM/PCM)",
        system="Rede CAN / Barramento",
        neutral_advice="Módulos da rede não conseguiram comunicação temporária ou permanente com a ECU do motor.",
        checklist=[
            "Linhas CAN High e CAN Low (continuidade e resistência de terminação de 60 ohms)",
            "Alimentação principal da ECU (relé de injeção e fusíveis)",
            "Aterramentos da ECU"
        ]
    )
}


def get_dtc_info(code: str) -> DTCMeta:
    """
    Retrieve DTC information from catalog, or return structured fallback
    for any generic standard OBD2 DTC.
    """
    clean_code = code.strip().upper()
    if clean_code in DTC_CATALOG:
        return DTC_CATALOG[clean_code]

    # Dynamic generic interpretation based on standard OBD2 prefix
    category = "Desconhecido"
    prefix = clean_code[0] if clean_code else ""
    if prefix == "P":
        category = "Trem de Força (Powertrain - Motor/Câmbio)"
    elif prefix == "C":
        category = "Chassi (Freios/Suspensão/Direção)"
    elif prefix == "B":
        category = "Carroceria (Body - Airbag/Conforto)"
    elif prefix == "U":
        category = "Rede de Comunicação (Network/CAN)"

    return DTCMeta(
        code=clean_code,
        description=f"Código de Diagnóstico Padrão OBD2 ({category})",
        system=category,
        neutral_advice="Código registrado pela unidade de controle. A presença deste código não confirma defeito direto no componente citado; realize testes com multímetro, osciloscópio e inspeção visual antes de qualquer substituição.",
        checklist=[
            "Verificar integridade do chicote elétrico e conectores do sistema correspondente",
            "Verificar alimentação elétrica (+12V, +5V de referência) e aterramentos",
            "Verificar se há sinais de intervenções anteriores, emendas ou mau contato",
            "Consultar valores em tempo real correspondentes para verificar resposta do sensor/atuador"
        ]
    )
