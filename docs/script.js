/**
 * ODBSCAN II - Interactive Client-Side Logic
 * - Internationalization (PT / EN) with auto-detection & switcher
 * - Theme Switcher (Light / Dark) with browser preference auto-detection
 * - Live GitHub Releases API Integration
 * - Interactive Showcase Tabs, FAQ Accordion, and Toast Notifications
 */

const GITHUB_REPO = 'lgluiz1/Scan-ODB-II-ELM327';
const GITHUB_API_URL = `https://api.github.com/repos/${GITHUB_REPO}/releases/latest`;
const FALLBACK_DOWNLOAD = `https://github.com/lgluiz1/Scan-ODB-II-ELM327/releases/latest/download/OBDScanner.exe`;
const SHA256_HASH = 'ab38e534e14a3ff7b07d7f61a3213e6625106f1e6f8e78c4568db4eedd6c6dbb';

/* ================= BILINGUAL TRANSLATIONS (PT / EN) ================= */
const TRANSLATIONS = {
  pt: {
    // Nav
    brand_tag: "PORTÁTIL",
    nav_features: "Recursos",
    nav_showcase: "Interface",
    nav_why: "Diferenciais",
    nav_drivers: "Drivers USB",
    nav_faq: "Dúvidas",
    
    // Hero
    badge_portable: "100% Standalone • Sem Instalação • Windows 10 & 11 (64-bit)",
    hero_title: "Diagnóstico Veicular Universal <br><span class='gradient-text'>Direto no Seu Computador.</span>",
    hero_subtitle: "Utilitário automotivo profissional e autônomo para adaptadores ELM327 USB. Baixe um único executável de 45 MB, dê dois cliques e comece a diagnosticar. Sem instalador, sem Python e com auto-atualização integrada.",
    btn_download_label: "Baixar ODBScan II",
    btn_download_portable: "• Portátil",
    btn_view_repo: "Ver Código Aberto",
    spec_fast: "Início Instantâneo (< 2s)",
    spec_offline: "100% Offline e Privado",
    spec_pendrive: "Roda Direto de Pendrive",
    spec_autoupdate: "Auto-Atualizador Integrado",
    toast_copy_sha: "📋 Hash SHA-256 copiado com sucesso!",

    // Showcase
    window_title: "ODBScan II • Painel de Controle de Alta Fidelidade",
    tab_lambda: "📈 Osciloscópio de Sondas Lambda (O2)",
    tab_blackbox: "🚗 Telemetria & Gravação de Viagem",
    tab_dtc: "🔍 Diagnóstico de DTCs & Reset da ECU",

    // Why Choose ODBScan II
    tag_why: "A Filosofia do Software",
    title_why: "Por Que Escolher o ODBScan II?",
    desc_why: "Chega de ferramentas pesadas de 2 GB, instaladores cheios de propagandas ou dependências quebradas. O ODBScan II foi construído para ser leve, direto ao ponto e confiável em qualquer oficina ou garagem.",
    
    why_single_title: "Executável Único & Autônomo",
    why_single_desc: "Um único arquivo de 45 MB com todas as bibliotecas necessárias embutidas. Não precisa de Python, dependências externas ou instaladores demorados.",
    why_update_title: "Auto-Atualização Integrada",
    why_update_desc: "O ODBScan II verifica o GitHub em segundo plano. Com 1 clique, ele baixa a nova versão, substitui o executável e reinicia automaticamente.",
    why_portable_title: "Roda de Qualquer Lugar",
    why_portable_desc: "Salve em um pendrive e leve para a oficina. Não altera o Registro do Windows, e o banco de dados SQLite local fica perfeitamente salvo junto ao aplicativo.",
    why_scroll_title: "Interface Adaptável com Rolagem",
    why_scroll_desc: "Desenvolvido pensando nos notebooks antigos de oficina (telas 1366x768 ou 720p). Nada fica espremido: sistema de rolagem suave e cards de alta visibilidade.",
    why_mock_title: "Modo Simulação (MOCK)",
    why_mock_desc: "Quer demonstrar ou testar o programa sem ir até o veículo? Selecione a porta virtual de testes para simular aceleração, osciloscópio e injeção de falhas.",
    why_safe_title: "100% Seguro para a ECU",
    why_safe_desc: "Comunicação em estrita conformidade com o padrão internacional SAE J1979. Modo somente-leitura por padrão, com confirmações duplas para limpeza de falhas.",

    // Technical Features
    tag_tech: "Poder de Diagnóstico",
    title_tech: "Engenharia Automotiva na Prática",
    desc_tech: "Compatível com qualquer veículo nacional ou importado que utilize o protocolo OBD2 / CAN Bus.",
    tech_lambda_title: "Osciloscópio de Sonda Lambda",
    tech_lambda_desc: "Aquisição em alta taxa (8-10 Hz) da Sonda 1 (Pré-Cat) e Sonda 2 (Pós-Cat). Avalia chaveamento pobre/rico e detecta oscilação na Sonda 2 (perda de eficiência catalítica P0420).",
    tech_blackbox_title: "Telemetria & Caixa-Preta (90s)",
    tech_blackbox_desc: "Detecta falhas intermitentes difíceis de reproduzir na oficina. Mantém um buffer circular contínuo de 60s antes da falha e congela os 30s posteriores com RPM, MAP, TPS, STFT e ECT.",
    tech_dtc_title: "Leitor & Reset DTCs (03, 07, 0A)",
    tech_dtc_desc: "Lê códigos confirmados, pendentes e permanentes com descrição técnica em português, roteiro investigativo de chicote/sensores e painel de correlação de causas raízes.",

    // Drivers
    tag_drivers: "Instalação Prévia",
    title_drivers: "Drivers do Cabo ELM327 USB",
    desc_drivers: "O ODBScan II não precisa de instalação, mas o Windows precisa reconhecer o chip conversor USB-Serial do seu cabo ELM327. Baixe o driver oficial do seu chip abaixo:",
    driver_download_btn: "Baixar Driver ↗",

    // Steps
    tag_steps: "Prático & Direto",
    title_steps: "Como Usar no Carro em 3 Passos",
    step1_title: "Conecte o Adaptador",
    step1_desc: "Plugue o cabo ELM327 na tomada OBD-II do seu veículo e a ponta USB no notebook.",
    step2_title: "Ligue a Ignição",
    step2_desc: "Gire a chave do carro para a posição de ignição (painel totalmente aceso). Não precisa dar a partida no motor.",
    step3_title: "Abra o ODBScan II",
    step3_desc: "Abra o aplicativo, selecione a porta serial identificada (ex: COM3) com velocidade 38400 bps e clique em Conectar!",

    // FAQ
    tag_faq: "Perguntas Frequentes",
    title_faq: "Tire Suas Dúvidas",
    faq1_q: "Preciso instalar Python ou alguma biblioteca para rodar?",
    faq1_a: "<strong>Não!</strong> O aplicativo é 100% autônomo. O arquivo executável já contém o interpretador e todas as dependências embutidas, pronto para uso em qualquer computador com Windows 10 ou 11.",
    faq2_q: "Funciona em quais veículos?",
    faq2_a: "Funciona em <strong>qualquer carro nacional ou importado</strong> compatível com o padrão OBD-II (no Brasil, veículos a partir de 2010; nos EUA/Europa, a partir de 1996/2001).",
    faq3_q: "O aplicativo precisa de internet para funcionar?",
    faq3_a: "<strong>Não.</strong> Todas as funções de diagnóstico, osciloscópio e telemetria rodam 100% offline. A internet é usada exclusivamente caso você queira verificar novas atualizações pelo GitHub.",
    faq4_q: "Como faço para atualizar o programa quando sair uma versão nova?",
    faq4_a: "Basta abrir o aplicativo! Ele avisa automaticamente caso haja novidades. Você também pode clicar no botão <strong>'🔄 Atualizações'</strong> na barra superior do programa para baixar e reiniciar com apenas 1 clique.",

    // Footer
    footer_desc: "Utilitário automotivo universal para diagnóstico OBD-II, análise de osciloscópio de sinal lambda e telemetria veicular para adaptadores ELM327 USB.",
    footer_dev: "👨‍💻 Desenvolvido e criado por Luiz Gustavo",
    footer_downloads: "Downloads",
    footer_history: "Histórico de Releases",
    footer_source: "Código Aberto",
    footer_repo: "Repositório GitHub",
    footer_issues: "Relatar Falha (Issues)",
    footer_license: "Licença MIT",
    footer_copy: "© 2026 ODBScan II. Software de código aberto sob licença MIT.",
    footer_tagline: "Desenvolvido com foco em transparência técnica automotiva.",
    ad_label: "Espaço Publicitário"
  },

  en: {
    // Nav
    brand_tag: "PORTABLE",
    nav_features: "Features",
    nav_showcase: "Interface",
    nav_why: "Why ODBScan",
    nav_drivers: "USB Drivers",
    nav_faq: "FAQ",
    
    // Hero
    badge_portable: "100% Standalone • No Installation • Windows 10 & 11 (64-bit)",
    hero_title: "Universal Automotive Diagnostics <br><span class='gradient-text'>Right On Your PC.</span>",
    hero_subtitle: "Professional and standalone automotive utility for ELM327 USB adapters. Download a single 45 MB executable, double click and start diagnosing. No installer, no Python, and built-in auto-update.",
    btn_download_label: "Download ODBScan II",
    btn_download_portable: "• Portable",
    btn_view_repo: "View Open Source",
    spec_fast: "Instant Startup (< 2s)",
    spec_offline: "100% Offline & Private",
    spec_pendrive: "Runs from Flash Drive",
    spec_autoupdate: "Built-in Auto-Updater",
    toast_copy_sha: "📋 SHA-256 hash copied to clipboard!",

    // Showcase
    window_title: "ODBScan II • High-Fidelity Diagnostic Dashboard",
    tab_lambda: "📈 Lambda (O2) Sensor Oscilloscope",
    tab_blackbox: "🚗 Vehicle Telemetry & Trip Recorder",
    tab_dtc: "🔍 DTC Reader & ECU Reset",

    // Why Choose ODBScan II
    tag_why: "Software Philosophy",
    title_why: "Why Choose ODBScan II?",
    desc_why: "No heavy 2 GB bloated tools, no ad-ridden installers, and no broken dependencies. ODBScan II is built to be lightweight, straightforward, and reliable in any garage or workshop.",
    
    why_single_title: "Single Autonomous Executable",
    why_single_desc: "A single 45 MB file with all necessary libraries bundled inside. No Python required, no external dependencies, and no lengthy installation wizards.",
    why_update_title: "Built-in Auto-Update",
    why_update_desc: "ODBScan II silently queries GitHub Releases. In 1 click, it downloads the latest build, replaces the executable, and relaunches automatically.",
    why_portable_title: "Runs From Anywhere",
    why_portable_desc: "Save to a flash drive and take it to any PC. It leaves no messy Windows Registry keys, and saves its SQLite database right beside the application.",
    why_scroll_title: "Adaptive Responsive UI with Scroll",
    why_scroll_desc: "Designed specifically for older workshop laptops (1366x768 or 720p). Nothing overlaps: smooth scrolling and high-contrast diagnostic cards.",
    why_mock_title: "MOCK Simulation Mode",
    why_mock_desc: "Want to test or demonstrate without going to the car? Select the virtual MOCK port to simulate live ECU RPM, sensor toggles, and fault code injection.",
    why_safe_title: "100% Safe For The ECU",
    why_safe_desc: "Strict adherence to the international SAE J1979 standard. Read-only communication by default, with safety confirmations before DTC clearing.",

    // Technical Features
    tag_tech: "Diagnostic Power",
    title_tech: "Real Automotive Engineering",
    desc_tech: "Fully compatible with any domestic or imported vehicle supporting OBD2 / CAN Bus protocols.",
    tech_lambda_title: "Oxygen Sensor Oscilloscope",
    tech_lambda_desc: "High sample-rate acquisition (8-10 Hz) of Sensor 1 (Pre-Cat) and Sensor 2 (Post-Cat). Evaluates lean/rich switching and flags S2 tandem oscillations (P0420 catalyst efficiency loss).",
    tech_blackbox_title: "Telemetry & Blackbox (90s)",
    tech_blackbox_desc: "Captures intermittent faults that are hard to replicate in the shop. Keeps a circular 60s pre-fault buffer and locks 30s post-fault with RPM, MAP, TPS, STFT, and ECT data.",
    tech_dtc_title: "DTC Reader & Clear (03, 07, 0A)",
    tech_dtc_desc: "Reads confirmed, pending, and permanent fault codes with plain-language diagnostic descriptions, sensor testing checklists, and root-cause correlation analysis.",

    // Drivers
    tag_drivers: "Driver Setup",
    title_drivers: "ELM327 USB Cable Drivers",
    desc_drivers: "ODBScan II requires no installation, but Windows must recognize the USB-to-Serial chip inside your ELM327 adapter. Download the official driver below:",
    driver_download_btn: "Download Driver ↗",

    // Steps
    tag_steps: "Quick & Simple",
    title_steps: "How to Use in Your Car in 3 Steps",
    step1_title: "Plug the Adapter",
    step1_desc: "Connect your ELM327 cable into the vehicle's OBD-II diagnostic socket and the USB end into your laptop.",
    step2_title: "Turn Ignition ON",
    step2_desc: "Turn your car key to the ON position (dashboard fully illuminated). No need to start the engine right away.",
    step3_title: "Launch ODBScan II",
    step3_desc: "Open the executable, select the detected serial COM port at 38400 baud, and click Connect!",

    // FAQ
    tag_faq: "Frequently Asked Questions",
    title_faq: "Common Questions Answered",
    faq1_q: "Do I need to install Python or extra libraries?",
    faq1_a: "<strong>No!</strong> The program is 100% standalone. The executable already bundles the runtime and all dependencies, ready to run on any Windows 10 or 11 system.",
    faq2_q: "Which vehicles are supported?",
    faq2_a: "Works on <strong>any vehicle</strong> compliant with OBD-II standards (US models 1996+, European petrol 2001+, Brazilian 2010+, diesel 2004+).",
    faq3_q: "Does the application require an active Internet connection?",
    faq3_a: "<strong>No.</strong> All diagnostic scans, live telemetry, and oscilloscope scopes run 100% offline. The internet is only used if you choose to check for updates.",
    faq4_q: "How do I upgrade when a new version is released?",
    faq4_a: "Just launch the app! It will alert you when a new release is available on GitHub. You can also click the <strong>'🔄 Updates'</strong> button in the top bar to download and relaunch with 1 click.",

    // Footer
    footer_desc: "Universal automotive utility for OBD-II diagnostics, lambda signal oscilloscope, and vehicle flight telemetry for ELM327 USB adapters.",
    footer_dev: "👨‍💻 Developed and created by Luiz Gustavo",
    footer_downloads: "Downloads",
    footer_history: "Release History",
    footer_source: "Open Source",
    footer_repo: "GitHub Repository",
    footer_issues: "Report Issue (GitHub Issues)",
    footer_license: "MIT License",
    footer_copy: "© 2026 ODBScan II. Open-source software licensed under MIT.",
    footer_tagline: "Built with a focus on automotive diagnostic transparency.",
    ad_label: "Advertisement"
  }
};

/* ================= APP INITIALIZATION ================= */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initLanguage();
  initGitHubReleaseInfo();
  initShowcaseTabs();
  initChecksumCopy();
  initFaqAccordion();
});

/**
 * Theme initialization and switcher (Default: Light Mode, adapts to OS prefers-color-scheme)
 */
function initTheme() {
  const themeBtn = document.getElementById('theme-toggle-btn');
  const storedTheme = localStorage.getItem('odbscan_theme');
  
  let activeTheme = storedTheme;
  if (!activeTheme) {
    // Check OS preference: if prefers-color-scheme is dark, dark; else light
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    activeTheme = prefersDark ? 'dark' : 'light';
  }

  applyTheme(activeTheme);

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
      localStorage.setItem('odbscan_theme', nextTheme);
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const themeIcon = document.getElementById('theme-icon');
  const themeText = document.getElementById('theme-text');
  if (themeIcon) {
    themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
  }
  if (themeText) {
    themeText.textContent = theme === 'dark' ? 'Dark' : 'Light';
  }
}

/**
 * Internationalization setup (PT / EN with automatic browser detection)
 */
let currentLanguage = 'pt';

function initLanguage() {
  const langBtn = document.getElementById('lang-toggle-btn');
  const storedLang = localStorage.getItem('odbscan_lang');

  if (storedLang && (storedLang === 'pt' || storedLang === 'en')) {
    currentLanguage = storedLang;
  } else {
    // Auto-detect browser language
    const browserLang = (navigator.language || navigator.userLanguage || 'pt').toLowerCase();
    currentLanguage = browserLang.startsWith('en') ? 'en' : 'pt';
  }

  applyLanguage(currentLanguage);

  if (langBtn) {
    langBtn.addEventListener('click', () => {
      const nextLang = currentLanguage === 'pt' ? 'en' : 'pt';
      currentLanguage = nextLang;
      localStorage.setItem('odbscan_lang', nextLang);
      applyLanguage(nextLang);
    });
  }
}

function applyLanguage(lang) {
  currentLanguage = lang;
  const dict = TRANSLATIONS[lang] || TRANSLATIONS['pt'];

  // Update all elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.innerHTML = dict[key];
    }
  });

  // Update language toggle button text
  const langLabel = document.getElementById('lang-current-label');
  if (langLabel) {
    langLabel.textContent = lang === 'pt' ? '🇧🇷 PT' : '🇺🇸 EN';
  }

  // Update HTML lang attribute
  document.documentElement.setAttribute('lang', lang === 'pt' ? 'pt-BR' : 'en');
}

/**
 * Live GitHub Releases API Integration
 */
async function initGitHubReleaseInfo() {
  const btnLink = document.getElementById('btn-download-link');
  const btnVersion = document.getElementById('btn-version-text');
  const btnSize = document.getElementById('btn-size-text');

  try {
    const res = await fetch(GITHUB_API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const tag = data.tag_name || 'v1.3.0';
    if (btnVersion) btnVersion.textContent = `(${tag})`;

    let exeAsset = null;
    if (data.assets && data.assets.length > 0) {
      exeAsset = data.assets.find(a => a.name.toLowerCase().endsWith('.exe'));
    }

    if (exeAsset) {
      if (btnLink) btnLink.href = exeAsset.browser_download_url;
      if (btnSize && exeAsset.size) {
        const mb = (exeAsset.size / (1024 * 1024)).toFixed(1);
        btnSize.textContent = `• ${mb} MB`;
      }
    } else {
      if (btnLink) btnLink.href = FALLBACK_DOWNLOAD;
    }
  } catch (err) {
    console.warn('[ODBScan II] Release fetch fallback:', err);
    if (btnLink) btnLink.href = FALLBACK_DOWNLOAD;
    if (btnVersion) btnVersion.textContent = '(v1.3.0)';
    if (btnSize) btnSize.textContent = '• 44.6 MB';
  }
}

/**
 * Showcase Tab Switcher
 */
function initShowcaseTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  const images = document.querySelectorAll('.showcase-img');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-target');

      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      images.forEach(img => {
        if (img.id === targetId) {
          img.classList.add('active');
        } else {
          img.classList.remove('active');
        }
      });
    });
  });
}

/**
 * SHA-256 Checksum Quick Copy
 */
function initChecksumCopy() {
  const box = document.getElementById('checksum-box');
  if (!box) return;

  box.addEventListener('click', async () => {
    const msg = TRANSLATIONS[currentLanguage].toast_copy_sha || '📋 SHA-256 Copiado!';
    try {
      await navigator.clipboard.writeText(SHA256_HASH);
      showToast(msg);
    } catch {
      showToast(`Hash: ${SHA256_HASH}`);
    }
  });
}

/**
 * FAQ Accordion Expand/Collapse
 */
function initFaqAccordion() {
  const items = document.querySelectorAll('.faq-item');
  items.forEach(item => {
    const questionBtn = item.querySelector('.faq-question');
    if (questionBtn) {
      questionBtn.addEventListener('click', () => {
        const isOpen = item.classList.contains('open');
        items.forEach(i => i.classList.remove('open'));
        if (!isOpen) {
          item.classList.add('open');
        }
      });
    }
  });
}

/**
 * Toast Notification Popup
 */
function showToast(message) {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3200);
}
