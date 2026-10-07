# ⚡ OBD Scanner & Caixa-Preta (ELM327 USB)

[![Versão](https://img.shields.io/badge/Vers%C3%A3o-v1.2.0-blue.svg)](https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%2010%20%7C%2011%20(64--bit)-0078d7.svg)](https://github.com/lgluiz1/Scan-ODB-II-ELM327)
[![Executável Portátil](https://img.shields.io/badge/Execut%C3%A1vel-Stand--alone%20(.exe)-success.svg)](https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases/latest/download/OBDScanner.exe)
[![Protocolo](https://img.shields.io/badge/Protocolo-OBD2%20%2F%20EOBD%20(SAE%20J1979)-orange.svg)](https://github.com/lgluiz1/Scan-ODB-II-ELM327)
[![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-lightgrey.svg)](LICENSE)

Ferramenta profissional e intuitiva de **diagnóstico eletrônico automotivo (OBD2)**, **osciloscópio de sinal das sondas lambda** e **caixa-preta de telemetria contínua (Modo Viagem)** para adaptadores **ELM327 USB** no Windows.

Projetada com foco técnico nas particularidades do **Renault Logan Authentique 2018 1.0 12V 3 Cilindros (Motor B4D Flex)**, mas 100% compatível com qualquer veículo nacional ou importado que utilize o padrão OBD-II / CAN Bus.

---

## 📥 Download do Aplicativo (.exe Pronto para Uso)

Você **NÃO precisa instalar Python**, bibliotecas ou ferramentas de desenvolvimento. O programa roda de forma 100% autônoma no Windows.

* 🚀 **Download Direto da Última Versão:**  
  👉 **[Baixar OBDScanner.exe (v1.2.0)](https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases/latest/download/OBDScanner.exe)**
* 📦 **Repositório oficial e versões anteriores:**  
  👉 [Página de Releases no GitHub](https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases)
* 💾 **No próprio repositório clonado:**  
  O executável compilado fica localizado em [`dist/OBDScanner.exe`](dist/OBDScanner.exe).

---

## ⚠️ IMPORTANTE: Drivers do Cabo ELM327 USB (Instale Antes de Usar)

Para que o Windows reconheça o adaptador ELM327 USB conectado à tomada de diagnóstico do veículo, é **obrigatório** ter o driver do chip conversor USB-Serial instalado no seu computador.

Geralmente, os adaptadores ELM327 USB utilizam um dos seguintes chips controladores:

### 1. Chip CH340 / CH341 (O mais comum nos cabos ELM327 azuis e pretos)
* 📥 **Download do Instalador:** [CH341SER.EXE (Driver Oficial WCH)](http://www.wch-ic.com/downloads/CH341SER_EXE.html)
* **Como instalar:** Baixe o arquivo, dê dois cliques e clique no botão **"INSTALL"**.

### 2. Chip FTDI (FT232R / FT232RL - Cabos profissionais ou com chave seletora)
* 📥 **Download do Instalador:** [FTDI VCP Drivers (Virtual COM Port)](https://ftdichip.com/drivers/vcp-drivers/)
* **Como instalar:** Baixe o executável "setup executable" e siga o instalador padrão da FTDI.

### 3. Chip Prolific PL2303 / Silicon Labs CP2102
* 📥 **Prolific PL2303:** [Prolific USB-to-Serial Driver](https://www.prolific.com.tw/US/ShowProduct.aspx?p_id=225&pcid=41)
* 📥 **Silicon Labs CP210x:** [CP210x Universal Windows Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)

### 🔍 Como testar se o cabo foi reconhecido pelo Windows:
1. Conecte o cabo ELM327 em uma porta USB do seu notebook.
2. Pressione no teclado `Windows + X` e selecione **Gerenciador de Dispositivos**.
3. Expanda a categoria **Portas (COM e LPT)**.
4. Você deverá ver algo como:
   * `USB-SERIAL CH340 (COM3)`
   * ou `USB Serial Port (COM4)`
5. Se a porta aparecer **sem pontos de exclamação amarelos**, o adaptador está 100% pronto! Abra o `OBDScanner.exe`, selecione essa porta COM e clique em **CONECTAR**.

---

## 🌟 Principais Funcionalidades

### 1. 🔍 Diagnóstico Completo de Falhas (DTC Reader)
* Consulta todos os modos obrigatórios da norma SAE J1979:
  * **Modo 03:** Códigos confirmados que acendem a luz de injeção (MIL).
  * **Modo 07:** Códigos pendentes que ainda não completaram o ciclo de falha.
  * **Modo 0A:** Códigos permanentes gravados na memória não volátil da ECU.
* Descrição clara em português com roteiro investigativo neutro (testes de alimentação 5V, aterramento, estanqueidade de coletor, chicote e sensores).
* **Painel de Correlação Investigativa:** Quando múltiplos códigos ocorrem juntos (como P0106 + P0300 ou P0130 + P0171), o app cruza as causas raízes comuns.

### 2. 🗑️ Limpeza de Códigos de Falha (Mode 04 / Reset da ECU)
* Permite limpar a memória de falhas e apagar a luz da injeção eletrônica no painel.
* **Travas de Segurança:** Confirmação em duas etapas para evitar que você apague os códigos antes de salvar o relatório técnico.
* Alerta de segurança reforçando: procedimento deve ser executado com **ignição ligada e motor desligado**.

### 3. 📈 Osciloscópio em Tempo Real das Sondas Lambda (O2)
* Gráficos em tempo real comparando a **Sonda 1 (Pré-Catalisador / Ciano)** e a **Sonda 2 (Pós-Catalisador / Laranja)**.
* Linha guia amarela na tensão estequiométrica (**0.45V** / $\lambda = 1.0$).
* **Diagnóstico Inteligente do Catalisador (P0420):**
  * Detecta se a Sonda 1 está com chaveamento ativo rápido (0.1V a 0.9V).
  * Detecta se a mistura ficou travada em pobre (< 0.25V) ou rica (> 0.75V).
  * Avalia se a Sonda 2 permanece lisa e estável (~0.55V) ou se começou a oscilar em tandem com a Sonda 1 (sintoma típico de perda de cerâmica ou eficiência catalítica P0420).
* **Alertas Visuais Dinâmicos:** Os cards mudam dinamicamente de cor (verde para saudável, âmbar para atenção e vermelho vivo para falha crítica).

### 4. 🚗 Caixa-Preta do Veículo (Modo Viagem)
* Criado especificamente para diagnosticar **falhas intermitentes** (como cortes em subidas de serra, solavancos com ar-condicionado ou perdas de potência aleatórias).
* **Operação Mãos-Livres:** Você inicia a viagem, coloca o notebook no banco do passageiro e dirige normalmente.
* **Buffer Circular Inteligente:** O aplicativo mantém continuamente em memória os últimos **60 segundos de telemetria**. Se a ECU acusar uma falha, o app congela os **60s anteriores + os 30s posteriores** (totalizando 90 segundos) e salva no banco de dados local.

### 5. 📊 Análise de Padrões Operacionais
* Cruza estatisticamente as medições de telemetria no instante em que as falhas ocorreram:
  * Rotação do motor (RPM)
  * Pressão absoluta no coletor (MAP em kPa)
  * Abertura da borboleta (TPS em %)
  * Correção de combustível de curto prazo (STFT em %)
  * Temperatura do líquido de arrefecimento (ECT em °C)
* Permite descobrir exatamente se o carro falha sob alta carga, em marcha lenta ou em regimes específicos de temperatura.

### 6. 📱 Interface 100% Responsiva com Scroll
* Totalmente adaptada para telas de qualquer formato: desde monitores modernos Full HD / 4K até **notebooks antigos de oficina mecânica (1366x768 ou 720p)**.
* Sistema de rolagem suave (QScrollArea) que impede que cards, gráficos ou textos fiquem espremidos ou sobrepostos.

### 7. 🧪 Modo Simulação (MOCK) para Testes sem Veículo
* Não precisa estar no carro para testar!
* Basta selecionar a porta **`🧪 MODO SIMULAÇÃO (MOCK) - Teste Virtual`** para simular o comportamento da ECU do Logan, incluindo injeção de falhas, osciloscópio das sondas lambda e gravação de viagens.

---

## 🚗 Guia Rápido de Uso no Carro

1. Conecte o cabo **ELM327 USB** na porta USB do notebook e na porta OBD2 do veículo (no Renault Logan, fica dentro do porta-luvas).
2. Gire a chave do carro para a posição **IGNIÇÃO LIGADA (Painel aceso)**.
3. Abra o **`OBDScanner.exe`**.
4. Selecione a porta serial identificada (ex: `COM3`) e mantenha o baudrate em `38400`.
5. Clique em **`🔌 CONECTAR`**.
6. Aguarde a confirmação dos 3 cartões de status:
   * `Adaptador ELM327: Conectado`
   * `Comunicação ECU: Conectada`
   * `Tensão Bateria: 12.x V`
7. Navegue pelas abas para ler códigos de falha, inspecionar as sondas ou iniciar a Caixa-Preta de gravação contínua.

---

## 📜 Histórico de Versões

### 🔹 v1.2.0 (Versão Atual)
* **Novo Osciloscópio de Sondas Lambda (O2):** Aquisição contínua em alta taxa (8-10 Hz) das tensões da Sonda 1 (PID 0114), Sonda 2 (PID 0115) e razão de equivalência $\lambda$ (PID 0124).
* **Diagnóstico de Eficiência Catalítica (P0420):** Algoritmo automático de correlação entre Pré-Cat e Pós-Cat.
* **Limpeza de Códigos de Falha (Mode 04 / Reset ECU):** Botão com confirmação de segurança e dupla validação com a ECU.
* **Interface Responsiva com Rolagem (Scroll):** Redesenho completo do layout para telas de baixa resolução (1366x768 / 720p). Barras superiores condensadas, economizando 160px de espaço vertical.
* **Alertas Visuais Dinâmicos:** Cards de status com bordas e fundos luminosos reativos (Verde / Âmbar / Vermelho).

### 🔹 v1.1.0
* **Sistema de Caixa-Preta (Modo Viagem):** Gravação segundo a segundo com buffer circular (60s pré + 30s pós-evento).
* **Análise de Padrões Operacionais:** Relatórios estatísticos cruzando MAP, RPM, TPS e STFT.
* **Recuperação de Sessões Interrompidas:** Proteção contra desligamentos inesperados do notebook ou desconexões do cabo.

### 🔹 v1.0.0
* Leitor completo de DTCs nos Modos 03, 07 e 0A.
* Módulo consultor de diagnósticos neutros e guia de inspeção física.
* Exportação de relatórios técnicos em HTML e TXT.
* Terminal Serial TX/RX ao vivo e persistência em banco de dados SQLite.
* Modo Simulação (MOCK) virtual.

---

## 🛠️ Executando a Partir do Código-Fonte (Python)

Se você for desenvolvedor e preferir rodar diretamente pelo Python:

```bash
# 1. Clone o repositório
git clone https://github.com/lgluiz1/Scan-ODB-II-ELM327.git
cd Scan-ODB-II-ELM327

# 2. Crie e ative um ambiente virtual
python -m venv venv
.\venv\Scripts\activate   # No Windows PowerShell

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o aplicativo
python main.py

# 5. Para compilar o executável standalone (.exe)
python build_exe.py
```

---

## 👨‍💻 Desenvolvedor & Autor

Projeto criado com foco em precisão técnica, segurança e diagnóstico automotivo transparente.

* **Criado e Desenvolvido por:** **Luiz Gustavo**
* **GitHub:** [@lgluiz1](https://github.com/lgluiz1)
* **Repositório:** [https://github.com/lgluiz1/Scan-ODB-II-ELM327](https://github.com/lgluiz1/Scan-ODB-II-ELM327)

---

## ⚖️ Isenção de Responsabilidade

Este software é fornecido para fins educacionais, de diagnóstico e monitoramento veicular. Sempre realize verificações físicas no veículo e siga os manuais oficiais da montadora antes de substituir componentes ou realizar intervenções mecânicas/elétricas.
