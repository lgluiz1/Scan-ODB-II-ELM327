"""Diagnostic report generator for HTML and TXT formats.
"""
import datetime
from typing import List, Dict, Any, Optional
from dtc.reader import DTCItem
from dtc.advisor import DiagnosticAdvisor
from app.config import APP_NAME, APP_VERSION, SAFETY_WARNING


class ReportGenerator:
    """Creates formatted professional diagnostic reports."""

    @staticmethod
    def generate_html(
        vehicle_name: str,
        port: str,
        elm_version: str,
        protocol: str,
        voltage: str,
        dtc_items: List[DTCItem],
        correlations: List[Dict[str, Any]],
        raw_log: str = ""
    ) -> str:
        now_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        codes_list = [item.code for item in dtc_items]

        # Stored, pending, permanent breakdown
        stored = [i for i in dtc_items if "Confirmado" in i.status]
        pending = [i for i in dtc_items if "Pendente" in i.status]
        permanent = [i for i in dtc_items if "Permanente" in i.status]

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Diagnóstico OBD2 - {vehicle_name}</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #0f172a;
        color: #e2e8f0;
        margin: 0;
        padding: 30px;
        line-height: 1.5;
    }}
    .container {{
        max-width: 900px;
        margin: 0 auto;
        background: #1e293b;
        padding: 35px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 1px solid #334155;
    }}
    .header {{
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 18px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .title {{
        margin: 0;
        font-size: 26px;
        color: #f8fafc;
        font-weight: 700;
    }}
    .subtitle {{
        color: #94a3b8;
        font-size: 14px;
        margin-top: 4px;
    }}
    .badge-date {{
        background: #334155;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        color: #38bdf8;
    }}
    .grid-info {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 25px;
    }}
    .card-info {{
        background: #0f172a;
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #1e293b;
    }}
    .card-info .label {{
        font-size: 11px;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}
    .card-info .val {{
        font-size: 15px;
        font-weight: 600;
        color: #f1f5f9;
    }}
    .alert-banner {{
        background: rgba(234, 179, 8, 0.1);
        border-left: 4px solid #eab308;
        padding: 14px 18px;
        border-radius: 4px;
        margin-bottom: 25px;
        font-size: 13px;
        color: #fef08a;
    }}
    h2 {{
        font-size: 18px;
        color: #38bdf8;
        border-bottom: 1px solid #334155;
        padding-bottom: 8px;
        margin-top: 30px;
        margin-bottom: 16px;
    }}
    .dtc-card {{
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
    }}
    .dtc-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
    }}
    .dtc-badge {{
        background: #ef4444;
        color: white;
        font-weight: 700;
        font-size: 18px;
        padding: 4px 12px;
        border-radius: 6px;
        letter-spacing: 1px;
    }}
    .dtc-status {{
        background: #475569;
        color: #f8fafc;
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 12px;
    }}
    .dtc-system {{
        color: #94a3b8;
        font-size: 13px;
    }}
    .dtc-desc {{
        font-size: 15px;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 10px;
    }}
    .dtc-advice {{
        background: #1e293b;
        padding: 12px;
        border-radius: 6px;
        font-size: 13px;
        color: #cbd5e1;
        border-left: 3px solid #3b82f6;
        margin-bottom: 10px;
    }}
    .dtc-checklist {{
        margin: 0;
        padding-left: 20px;
        font-size: 13px;
        color: #94a3b8;
    }}
    .dtc-checklist li {{
        margin-bottom: 4px;
    }}
    .correlation-box {{
        background: #1e1b4b;
        border: 1px solid #4338ca;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
    }}
    .correlation-title {{
        color: #a5b4fc;
        font-weight: 700;
        font-size: 16px;
        margin-bottom: 6px;
    }}
    .correlation-desc {{
        font-size: 13px;
        color: #e0e7ff;
        margin-bottom: 10px;
    }}
    .raw-log {{
        background: #020617;
        padding: 14px;
        border-radius: 6px;
        font-family: Consolas, monospace;
        font-size: 12px;
        color: #a5f3fc;
        max-height: 250px;
        overflow-y: auto;
        white-space: pre-wrap;
    }}
    .footer {{
        margin-top: 35px;
        text-align: center;
        font-size: 12px;
        color: #64748b;
        border-top: 1px solid #334155;
        padding-top: 15px;
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1 class="title">DIAGNÓSTICO ELETRÔNICO OBD2</h1>
            <div class="subtitle">{APP_NAME} v{APP_VERSION} — Ferramenta de Análise Segura</div>
        </div>
        <div class="badge-date">{now_str}</div>
    </div>

    <div class="alert-banner">
        <strong>⚠️ AVISO TÉCNICO IMPORTANTE:</strong> Os códigos de falha (DTCs) indicam leituras fora dos parâmetros de fábrica medidas pela ECU, e <u>NÃO</u> confirmam defeito direto no componente citado. Teste sempre o chicote, conexões, alimentação e integridade mecânica antes de substituir peças.
    </div>

    <div class="grid-info">
        <div class="card-info">
            <div class="label">Veículo</div>
            <div class="val">{vehicle_name}</div>
        </div>
        <div class="card-info">
            <div class="label">Adaptador</div>
            <div class="val">{elm_version}</div>
        </div>
        <div class="card-info">
            <div class="label">Porta Serial</div>
            <div class="val">{port}</div>
        </div>
        <div class="card-info">
            <div class="label">Protocolo OBD2</div>
            <div class="val">{protocol}</div>
        </div>
        <div class="card-info">
            <div class="label">Tensão Medida</div>
            <div class="val">{voltage}</div>
        </div>
        <div class="card-info">
            <div class="label">Códigos Ativos</div>
            <div class="val">{len(dtc_items)} Código(s)</div>
        </div>
    </div>
"""

        # Section: Correlations
        if correlations:
            html += "<h2>🧠 ANÁLISE INVESTIGATIVA & CORRELAÇÕES</h2>"
            for corr in correlations:
                checklist_html = "".join(f"<li>{item}</li>" for item in corr.get("checklist", []))
                html += f"""
                <div class="correlation-box">
                    <div class="correlation-title">{corr['title']}</div>
                    <div class="correlation-desc">{corr['summary']}</div>
                    <ul class="dtc-checklist">
                        {checklist_html}
                    </ul>
                </div>
                """

        # Section: DTC Details
        html += "<h2>📋 CÓDIGOS DE FALHA IDENTIFICADOS</h2>"
        if not dtc_items:
            html += """
            <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; padding: 18px; border-radius: 8px; color: #86efac; text-align: center;">
                ✔️ Nenhum código de falha ativo retornado pela ECU no momento do escaneamento.
            </div>
            """
        else:
            for item in dtc_items:
                checklist_html = "".join(f"<li>{c}</li>" for c in item.meta.checklist)
                html += f"""
                <div class="dtc-card">
                    <div class="dtc-header">
                        <span class="dtc-badge">{item.code}</span>
                        <span class="dtc-status">{item.status}</span>
                        <span class="dtc-system">Sistema: {item.meta.system}</span>
                    </div>
                    <div class="dtc-desc">{item.meta.description}</div>
                    <div class="dtc-advice">
                        <strong>Orientação diagnóstica:</strong> {item.meta.neutral_advice}
                    </div>
                    <div style="font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 4px;">Roteiro de Verificação Recomendado:</div>
                    <ul class="dtc-checklist">
                        {checklist_html}
                    </ul>
                </div>
                """

        # Section: Raw Log
        if raw_log:
            html += f"""
            <h2>📡 REGISTRO TÉCNICO DE COMUNICAÇÃO SERIAL (LOG)</h2>
            <div class="raw-log">{raw_log}</div>
            """

        html += f"""
        <div class="footer">
            Gerado automaticamente por {APP_NAME} v{APP_VERSION} em {now_str}<br>
            Diagnóstico estritamente em modo de leitura (Read-Only).
        </div>
    </div>
</body>
</html>
"""
        return html

    @staticmethod
    def generate_txt(
        vehicle_name: str,
        port: str,
        elm_version: str,
        protocol: str,
        voltage: str,
        dtc_items: List[DTCItem],
        correlations: List[Dict[str, Any]],
        raw_log: str = ""
    ) -> str:
        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        lines = []
        lines.append("=" * 70)
        lines.append("RELATÓRIO DE DIAGNÓSTICO OBD2 - " + APP_NAME)
        lines.append("=" * 70)
        lines.append(f"Data/Hora:        {now_str}")
        lines.append(f"Veículo:          {vehicle_name}")
        lines.append(f"Adaptador ELM:    {elm_version}")
        lines.append(f"Porta COM:        {port}")
        lines.append(f"Protocolo ECU:    {protocol}")
        lines.append(f"Tensão Bateria:   {voltage}")
        lines.append(f"Total de Códigos: {len(dtc_items)}")
        lines.append("-" * 70)
        lines.append("AVISO: Os códigos são informativos. Não confirmam defeito no componente.")
        lines.append("-" * 70)

        if correlations:
            lines.append("\n[ANÁLISE DE CORRELAÇÃO DE CÓDIGOS]")
            for corr in correlations:
                lines.append(f"\n* {corr['title']}")
                lines.append(f"  Resumo: {corr['summary']}")
                lines.append("  Verificações recomendadas:")
                for check in corr.get("checklist", []):
                    lines.append(f"    - {check}")

        lines.append("\n[CÓDIGOS DE FALHA IDENTIFICADOS]")
        if not dtc_items:
            lines.append("Nenhum código de falha encontrado.")
        else:
            for item in dtc_items:
                lines.append(f"\nCódigo:     {item.code} ({item.status})")
                lines.append(f"Sistema:    {item.meta.system}")
                lines.append(f"Descrição:  {item.meta.description}")
                lines.append(f"Orientação: {item.meta.neutral_advice}")
                lines.append("Checklist:")
                for c in item.meta.checklist:
                    lines.append(f"  - {c}")

        if raw_log:
            lines.append("\n" + "=" * 70)
            lines.append("REGISTRO DE COMUNICAÇÃO SERIAL (LOG)")
            lines.append("=" * 70)
            lines.append(raw_log)

        return "\n".join(lines)
