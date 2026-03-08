"""
Dual Momentum — Fondos de Inversión
Aplicación Streamlit para análisis mensual de cartera
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Dual Momentum — Fondos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #1a1a1a;
}

.main { background: #ffffff; }
[data-testid="stAppViewContainer"] { background: #ffffff; }
[data-testid="stSidebar"] { background: #f8f9fa; border-right: 1px solid #e0e0e0; }

h1, h2, h3 { font-family: 'DM Serif Display', serif !important; color: #1a1a1a !important; }

.metric-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.metric-card.green::before { background: linear-gradient(90deg, #00c853, #69f0ae); }
.metric-card.red::before   { background: linear-gradient(90deg, #ff1744, #ff5252); }
.metric-card.amber::before { background: linear-gradient(90deg, #ffa000, #ffd740); }
.metric-card.blue::before  { background: linear-gradient(90deg, #2979ff, #82b1ff); }

.fund-row {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
    transition: all 0.2s;
}
.fund-row:hover { border-color: #2979ff; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.fund-row.selected {
    border-color: #00c853;
    background: linear-gradient(135deg, #f0fff4 0%, #ffffff 100%);
}

.peso-bar-container {
    background: #1e2a40;
    border-radius: 6px;
    height: 8px;
    overflow: hidden;
    margin-top: 6px;
}
.peso-bar {
    height: 100%;
    border-radius: 6px;
    transition: width 0.5s ease;
}

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.badge-green  { background: #1b5e20; color: #69f0ae; }
.badge-red    { background: #7f0000; color: #ff8a80; }
.badge-amber  { background: #7f4500; color: #ffd740; }
.badge-gray   { background: #1c2333; color: #90a4ae; }

.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: #1a1a1a;
    margin: 24px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #e0e0e0;
}

.stButton > button {
    background: linear-gradient(135deg, #1565c0, #1976d2) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    font-size: 14px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1976d2, #1e88e5) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(25,118,210,0.4) !important;
}

div[data-testid="metric-container"] {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 12px;
}

.stDataFrame { background: transparent !important; }

.info-box {
    background: #f0f7ff;
    border: 1px solid #cce3ff;
    border-left: 3px solid #2979ff;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: #455a64;
    margin: 12px 0;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FONDOS CONFIGURACIÓN
# =============================================================================

FONDOS_DEFAULT = {
    "LU0996182563": "Amundi MSCI World",
    "LU1670707527": "M&G Eurp Strat Val",
    "LU1694789451": "DNCA Alpha Bonds",
    "LU1963720757": "Nordea BetaPlus Glb",
    "LU1372006947": "Cobas Lux Selec",
    "LU0996177134": "Amundi MSCI EM",
    "LU0947062542": "SCHRODER EM MARKETS A ACC",
}
MONETARIO_ISIN   = "LU0423950210"
BENCHMARK_ISIN   = "LU0996182563" # MSCI World como benchmark para Alfa/Beta
MONETARIO_NOMBRE = "BNP EUR 3M"

COLORES = ["#2979ff","#00c853","#ffa000","#e91e63","#00bcd4","#9c27b0","#ff5722"]

# =============================================================================
# FUNCIONES DE DATOS
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def descargar_nav(isin: str) -> pd.Series | None:
    try:
        import mstarpy
        end_date   = datetime.today()
        start_date = end_date - timedelta(days=500)
        fund = mstarpy.Funds(isin)
        nav_data = fund.nav(start_date, end_date, frequency="daily")
        if not nav_data:
            return None
        df = pd.DataFrame(nav_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        col = 'totalReturn' if 'totalReturn' in df.columns else 'nav'
        return df[col].dropna().astype(float)
    except Exception as e:
        return None

def calcular_momentum(nav: pd.Series, meses: int) -> float | None:
    try:
        dias = int(meses * 21)
        if len(nav) < dias:
            return None
        return round(float((nav.iloc[-1] / nav.iloc[-dias] - 1) * 100), 2)
    except:
        return None

def calcular_sma200(nav: pd.Series) -> dict:
    try:
        if len(nav) < 200:
            return {'sma200': None, 'nav_actual': float(nav.iloc[-1]), 'sobre_sma': True, 'dist_sma': 0}
        sma = float(nav.rolling(200).mean().iloc[-1])
        nav_act = float(nav.iloc[-1])
        return {
            'sma200':    round(sma, 4),
            'nav_actual': round(nav_act, 4),
            'sobre_sma': nav_act >= sma,
            'dist_sma':  round((nav_act - sma) / sma * 100, 2)
        }
    except:
        return {'sma200': None, 'nav_actual': None, 'sobre_sma': True, 'dist_sma': 0}

def calcular_volatilidad(nav: pd.Series, dias: int = 63) -> float | None:
    try:
        if len(nav) < dias:
            return None
        return round(float(nav.pct_change().dropna().iloc[-dias:].std() * np.sqrt(252) * 100), 1)
    except:
        return None

def calcular_max_drawdown(nav: pd.Series, dias: int = 252) -> float | None:
    try:
        serie = nav.iloc[-dias:] if len(nav) > dias else nav
        rolling_max = serie.expanding().max()
        return round(float(((serie - rolling_max) / rolling_max * 100).min()), 1)
    except:
        return None

def calcular_sharpe_ratio(nav: pd.Series, risk_free_nav: pd.Series, dias: int = 252) -> float | None:
    try:
        if len(nav) < 63 or risk_free_nav is None:
            return None
        # Alinear fechas
        idx_comun = nav.index.intersection(risk_free_nav.index)
        if len(idx_comun) < 20: return None
        
        returns = nav.loc[idx_comun].pct_change().dropna()
        rf_returns = risk_free_nav.loc[idx_comun].pct_change().dropna()
        
        excess_returns = returns - rf_returns
        if len(excess_returns) == 0: return None
        
        mu = excess_returns.mean() * 252
        sigma = excess_returns.std() * np.sqrt(252)
        
        return round(float(mu / sigma), 2) if sigma > 0 else 0.0
    except:
        return None

def calcular_alfa_beta(nav: pd.Series, benchmark_nav: pd.Series, risk_free_nav: pd.Series, dias: int = 252) -> tuple[float | None, float | None]:
    try:
        if len(nav) < 63 or benchmark_nav is None or risk_free_nav is None:
            return None, None
            
        # Alinear fechas
        idx_comun = nav.index.intersection(benchmark_nav.index).intersection(risk_free_nav.index)
        if len(idx_comun) < 20: return None, None
        
        r = nav.loc[idx_comun].pct_change().dropna()
        rb = benchmark_nav.loc[idx_comun].pct_change().dropna()
        rf = risk_free_nav.loc[idx_comun].pct_change().dropna()
        
        y = r - rf
        x = rb - rf
        
        # Beta = Cov(y, x) / Var(x)
        beta = np.cov(y, x)[0, 1] / np.var(x)
        # Alfa (anualizado) = (Return - [Rf + Beta * (Benchmark - Rf)]) * 252
        alfa = (y.mean() - beta * x.mean()) * 252 * 100
        
        return round(float(alfa), 2), round(float(beta), 2)
    except:
        return None, None

def calcular_pesos(candidatos: list, mom_monetario: float, max_peso: float) -> list:
    if not candidatos:
        return []
    for c in candidatos:
        c['mom_relativo'] = max(0.0, (c['momentum_12m'] or 0) - mom_monetario)
    suma = sum(c['mom_relativo'] for c in candidatos)
    if suma <= 0:
        for c in candidatos:
            c['peso_raw'] = 1.0 / len(candidatos)
    else:
        for c in candidatos:
            c['peso_raw'] = c['mom_relativo'] / suma
    pesos = {c['isin']: c['peso_raw'] for c in candidatos}
    for _ in range(10):
        exceso = sum(max(0, p - max_peso) for p in pesos.values())
        if exceso < 0.001:
            break
        libres = [k for k, p in pesos.items() if p < max_peso]
        suma_libres = sum(pesos[k] for k in libres)
        for k in pesos:
            if pesos[k] > max_peso:
                pesos[k] = max_peso
            elif suma_libres > 0:
                pesos[k] += exceso * (pesos[k] / suma_libres)
    for c in candidatos:
        c['peso'] = round(pesos[c['isin']] * 20) / 20
    diff = 1.0 - sum(c['peso'] for c in candidatos)
    if abs(diff) > 0.001 and candidatos:
        candidatos[0]['peso'] = round(candidatos[0]['peso'] + diff, 2)
    return candidatos

def analizar_fondos(fondos: dict, mom_meses: int, max_peso: float) -> dict:
    """Descarga datos y aplica Dual Momentum con pesos."""
    resultados = {}
    nav_mon = descargar_nav(MONETARIO_ISIN)
    nav_ben = descargar_nav(BENCHMARK_ISIN)
    mom_mon = calcular_momentum(nav_mon, mom_meses) if nav_mon is not None else 0.0

    for isin, nombre in fondos.items():
        nav = descargar_nav(isin)
        if nav is None:
            resultados[isin] = {
                'isin': isin, 'nombre': nombre, 'nav': None,
                'momentum_12m': None, 'sma_info': {}, 'volatilidad': None,
                'max_drawdown': None, 'sharpe': None, 'alfa': None, 'beta': None,
                'estado': 'sin_datos', 'peso': 0.0, 'mom_relativo': 0.0,
            }
            continue
        mom      = calcular_momentum(nav, mom_meses)
        sma_info = calcular_sma200(nav)
        vol      = calcular_volatilidad(nav)
        dd       = calcular_max_drawdown(nav)
        sharpe   = calcular_sharpe_ratio(nav, nav_mon)
        alfa, beta = calcular_alfa_beta(nav, nav_ben, nav_mon)

        if mom is None:
            estado = 'sin_datos'
        elif mom <= (mom_mon or 0):
            estado = 'monetario'
        elif not sma_info.get('sobre_sma', True):
            estado = 'bajo_sma200'
        else:
            estado = 'candidato'

        resultados[isin] = {
            'isin': isin, 'nombre': nombre, 'nav': nav,
            'momentum_12m': mom, 'sma_info': sma_info,
            'volatilidad': vol, 'max_drawdown': dd,
            'sharpe': sharpe, 'alfa': alfa, 'beta': beta,
            'estado': estado, 'peso': 0.0, 'mom_relativo': 0.0,
        }

    candidatos    = [v for v in resultados.values() if v['estado'] == 'candidato']
    no_candidatos = [v for v in resultados.values() if v['estado'] != 'candidato']
    candidatos.sort(key=lambda x: x['momentum_12m'] or -999, reverse=True)
    candidatos = calcular_pesos(candidatos, mom_mon or 0, max_peso)
    for c in candidatos:
        resultados[c['isin']] = c

    peso_monetario = max(0.0, round(1.0 - sum(c['peso'] for c in candidatos), 2))

    return {
        'fecha':          datetime.today().strftime('%d/%m/%Y %H:%M'),
        'candidatos':     candidatos,
        'no_candidatos':  no_candidatos,
        'todos':          sorted(list(resultados.values()),
                                 key=lambda x: x['momentum_12m'] or -999, reverse=True),
        'mom_monetario':  round(mom_mon or 0, 2),
        'nav_monetario':  nav_mon,
        'peso_monetario': peso_monetario,
    }

# =============================================================================
# COMPONENTES UI
# =============================================================================

def render_barra_peso(pct: int, color: str):
    st.markdown(f"""
    <div class="peso-bar-container">
      <div class="peso-bar" style="width:{pct}%;background:{color}"></div>
    </div>
    """, unsafe_allow_html=True)

def render_badge(texto: str, tipo: str):
    clases = {'green':'badge-green','red':'badge-red','amber':'badge-amber','gray':'badge-gray'}
    cls = clases.get(tipo, 'badge-gray')
    st.markdown(f'<span class="badge {cls}">{texto}</span>', unsafe_allow_html=True)

def grafico_nav(fondo: dict, nav_monetario: pd.Series | None, mostrar_sma: bool):
    nav = fondo['nav']
    if nav is None:
        st.warning("Sin datos de NAV para este fondo.")
        return

    # Normalizar a 100
    nav_norm = nav / nav.iloc[0] * 100
    fig = go.Figure()

    # NAV normalizado
    fig.add_trace(go.Scatter(
        x=nav_norm.index, y=nav_norm.values,
        name=fondo['nombre'],
        line=dict(color='#2979ff', width=2),
        hovertemplate='%{x|%d/%m/%Y}<br>Índice: %{y:.1f}<extra></extra>'
    ))

    # SMA200
    if mostrar_sma and len(nav) >= 200:
        sma = (nav.rolling(200).mean() / nav.iloc[0] * 100)
        fig.add_trace(go.Scatter(
            x=sma.index, y=sma.values,
            name='SMA 200',
            line=dict(color='#ffa000', width=1.5, dash='dash'),
            hovertemplate='SMA200: %{y:.1f}<extra></extra>'
        ))

    # Monetario normalizado como referencia
    if nav_monetario is not None:
        # Alinear fechas
        idx_comun = nav_norm.index.intersection(nav_monetario.index)
        if len(idx_comun) > 0:
            mon_alin = nav_monetario.loc[idx_comun]
            mon_norm = mon_alin / mon_alin.iloc[0] * 100
            fig.add_trace(go.Scatter(
                x=mon_norm.index, y=mon_norm.values,
                name=MONETARIO_NOMBRE,
                line=dict(color='#546e7a', width=1, dash='dot'),
                hovertemplate='Monetario: %{y:.1f}<extra></extra>'
            ))

    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248,249,250,0.8)',
        height=320,
        margin=dict(t=20, b=20, l=0, r=0),
        legend=dict(orientation='h', y=1.05, font=dict(size=11)),
        xaxis=dict(gridcolor='#e0e0e0', showgrid=True),
        yaxis=dict(gridcolor='#e0e0e0', showgrid=True, title='Base 100'),
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

def grafico_momentum_comparativo(todos: list, mom_monetario: float):
    nombres = [f['nombre'] for f in todos] + [MONETARIO_NOMBRE]
    valores  = [f['momentum_12m'] or 0 for f in todos] + [mom_monetario]
    colores  = []
    for f in todos:
        if f['estado'] == 'candidato':
            colores.append('#00c853')
        elif f['estado'] == 'bajo_sma200':
            colores.append('#ff5722')
        else:
            colores.append('#546e7a')
    colores.append('#ffa000')  # monetario

    fig = go.Figure(go.Bar(
        x=valores, y=nombres,
        orientation='h',
        marker_color=colores,
        text=[f'{v:+.1f}%' for v in valores],
        textposition='outside',
        hovertemplate='%{y}<br>Momentum 12m: %{x:.1f}%<extra></extra>'
    ))
    fig.add_vline(x=mom_monetario, line=dict(color='#ffa000', dash='dash', width=2),
                  annotation_text=f"Umbral: {mom_monetario:.1f}%",
                  annotation_font_color='#ffa000')
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248,249,250,0.8)',
        height=300,
        margin=dict(t=20, b=20, l=0, r=80),
        xaxis=dict(gridcolor='#e0e0e0', title='Rentabilidad 12 meses (%)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)'),
    )
    st.plotly_chart(fig, use_container_width=True)

def grafico_tarta_cartera(candidatos: list, peso_monetario: float):
    labels = [c['nombre'] for c in candidatos]
    values = [c['peso'] * 100 for c in candidatos]
    colors_pie = COLORES[:len(candidatos)]

    if peso_monetario > 0:
        labels.append(MONETARIO_NOMBRE)
        values.append(peso_monetario * 100)
        colors_pie.append('#546e7a')

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors_pie, line=dict(color='#0a0e1a', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12),
        hovertemplate='%{label}<br>Peso: %{value:.0f}%<extra></extra>',
        hole=0.5,
    ))
    fig.add_annotation(text=f"{len(candidatos)}<br>fondos", x=0.5, y=0.5,
                       font=dict(size=16, color='#1a1a1a', family='DM Serif Display'),
                       showarrow=False)
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(t=20, b=20, l=0, r=0),
        legend=dict(orientation='h', y=-0.1, font=dict(size=11)),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 24px">
      <div style="font-family:'DM Serif Display',serif;font-size:26px;color:#1a1a1a">
        Dual Momentum
      </div>
      <div style="font-size:12px;color:#546e7a;margin-top:4px;letter-spacing:1px">
        FONDOS DE INVERSIÓN
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### ⚙️ Parámetros")

    mom_meses = st.slider(
        "Ventana de momentum (meses)",
        min_value=3, max_value=24, value=12, step=1,
        help="Antonacci recomienda 12 meses. Valores menores = más señales, más ruido."
    )
    max_peso_pct = st.slider(
        "Peso máximo por fondo (%)",
        min_value=20, max_value=100, value=50, step=5,
        help="Límite de concentración. 50% = nunca más de la mitad en un fondo."
    )
    mostrar_sma = st.toggle("Mostrar SMA200 en gráficos", value=True)

    st.divider()
    st.markdown("#### 📋 Fondos analizados")

    # Edición de fondos
    fondos_texto = st.text_area(
        "ISIN : Nombre (uno por línea)",
        value="\n".join(f"{k} : {v}" for k, v in FONDOS_DEFAULT.items()),
        height=180,
        help="Puedes añadir o quitar fondos. Formato: ISIN : Nombre"
    )

    # Parsear fondos del textarea
    fondos_custom = {}
    for linea in fondos_texto.strip().split('\n'):
        if ':' in linea:
            partes = linea.split(':', 1)
            isin   = partes[0].strip()
            nombre = partes[1].strip()
            if isin:
                fondos_custom[isin] = nombre

    st.divider()
    st.markdown("""
    <div style="font-size:11px;color:#37474f;line-height:1.6;padding:8px 0">
    📖 <b>Dual Momentum</b> (Antonacci):<br>
    1. Momentum absoluto: fondo vs monetario<br>
    2. Filtro SMA200: tendencia alcista<br>
    3. Peso proporcional al momentum relativo
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# CABECERA PRINCIPAL
# =============================================================================

st.markdown("""
<div style="padding:32px 0 24px">
  <div style="font-family:'DM Serif Display',serif;font-size:42px;
              color:#1a1a1a;line-height:1.1">
    Dual Momentum
    <span style="color:#2979ff">Fondos</span>
  </div>
  <div style="color:#546e7a;font-size:14px;margin-top:8px">
    Revisión mensual · Sistema de rotación basado en momentum
  </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# BOTÓN DE ANÁLISIS
# =============================================================================

col_btn, col_info = st.columns([1, 3])
with col_btn:
    analizar = st.button("🔍 Analizar Cartera", type="primary", use_container_width=True)
with col_info:
    st.markdown("""
    <div class="info-box">
    Los datos se descargan de <b>Morningstar</b> en tiempo real.
    La revisión se hace el <b>primer lunes de cada mes</b> — no antes.
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# TABS PRINCIPALES
# =============================================================================

tab_dash, tab_doc = st.tabs(["📊 Dashboard de Cartera", "📖 Guía y Metodología"])

with tab_dash:
    if analizar:
        with st.spinner("Descargando NAV histórico desde Morningstar..."):
            try:
                import mstarpy
            except ImportError:
                st.error("❌ Instala mstarpy: `pip install mstarpy`")
                st.stop()

            progreso = st.progress(0, text="Iniciando descarga...")
            total = len(fondos_custom) + 1
            paso  = 0

            # Forzar descarga secuencial mostrando progreso
            progreso.progress(paso / total, text=f"Descargando {MONETARIO_NOMBRE}...")
            descargar_nav(MONETARIO_ISIN)
            paso += 1

            for isin, nombre in fondos_custom.items():
                progreso.progress(paso / total, text=f"Descargando {nombre}...")
                descargar_nav(isin)
                paso += 1

            progreso.empty()

            resultados = analizar_fondos(fondos_custom, mom_meses, max_peso_pct / 100)
            st.session_state['resultados']   = resultados
            st.session_state['fondos_analizados'] = fondos_custom

    elif 'resultados' in st.session_state:
        resultados = st.session_state['resultados']
        fondos_custom = st.session_state.get('fondos_analizados', fondos_custom)

    if 'resultados' not in st.session_state:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#37474f">
          <div style="font-size:48px;margin-bottom:16px">📊</div>
          <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#546e7a">
            Pulsa "Analizar Cartera" para empezar
          </div>
          <div style="font-size:13px;margin-top:8px">
            Descargará el historial de NAV de todos los fondos y calculará el reparto óptimo
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Datos disponibles ─────────────────────────────────────────────────────────
    res          = st.session_state['resultados']
    candidatos   = res['candidatos']
    no_cands     = res['no_candidatos']
    todos        = res['todos']
    mom_mon      = res['mom_monetario']
    peso_mon     = res['peso_monetario']
    nav_mon      = res['nav_monetario']

    # =============================================================================
    # MÉTRICAS RESUMEN
    # =============================================================================

    st.markdown(f'<div class="section-title">Resumen — {res["fecha"]}</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        tipo = "green" if candidatos else "red"
        st.markdown(f"""
        <div class="metric-card {tipo}">
          <div style="font-size:12px;color:#546e7a;letter-spacing:1px">FONDOS EN CARTERA</div>
          <div style="font-size:36px;font-weight:600;color:#1a1a1a;margin:6px 0">{len(candidatos)}</div>
          <div style="font-size:12px;color:#546e7a">de {len(todos)} analizados</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        rec_nombre = candidatos[0]['nombre'] if candidatos else MONETARIO_NOMBRE
        rec_peso   = int(candidatos[0]['peso'] * 100) if candidatos else int(peso_mon * 100)
        st.markdown(f"""
        <div class="metric-card blue">
          <div style="font-size:12px;color:#546e7a;letter-spacing:1px">POSICIÓN PRINCIPAL</div>
          <div style="font-size:18px;font-weight:600;color:#1565c0;margin:6px 0">{rec_nombre}</div>
          <div style="font-size:24px;font-weight:700;color:#1a1a1a">{rec_peso}%</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        mom_top = candidatos[0]['momentum_12m'] if candidatos else None
        mom_str = f"{mom_top:+.1f}%" if mom_top is not None else "—"
        color_m = "#00c853" if (mom_top or 0) > 0 else "#ff5252"
        st.markdown(f"""
        <div class="metric-card {'green' if (mom_top or 0) > 0 else 'red'}">
          <div style="font-size:12px;color:#546e7a;letter-spacing:1px">MEJOR MOMENTUM 12M</div>
          <div style="font-size:36px;font-weight:600;color:{color_m};margin:6px 0">{mom_str}</div>
          <div style="font-size:12px;color:#546e7a">{candidatos[0]['nombre'] if candidatos else '—'}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        n_excluidos = len([f for f in no_cands if f['estado'] != 'sin_datos'])
        tipo_exc = "amber" if n_excluidos > 0 else "green"
        st.markdown(f"""
        <div class="metric-card {tipo_exc}">
          <div style="font-size:12px;color:#546e7a;letter-spacing:1px">FONDOS EXCLUIDOS</div>
          <div style="font-size:36px;font-weight:600;color:#f57c00;margin:6px 0">{n_excluidos}</div>
          <div style="font-size:12px;color:#546e7a">al refugio monetario</div>
        </div>""", unsafe_allow_html=True)

    # =============================================================================
    # REPARTO DE CARTERA
    # =============================================================================

    st.markdown('<div class="section-title">Reparto de Cartera</div>', unsafe_allow_html=True)

    col_tarta, col_barras = st.columns([1, 2])

    with col_tarta:
        grafico_tarta_cartera(candidatos, peso_mon)

    with col_barras:
        st.markdown("**Desglose por fondo**")
        all_asignados = list(candidatos)
        if peso_mon > 0:
            all_asignados.append({
                'nombre': MONETARIO_NOMBRE, 'peso': peso_mon,
                'momentum_12m': mom_mon, 'mom_relativo': 0, 'isin': MONETARIO_ISIN
            })

        for i, fondo in enumerate(all_asignados):
            pct    = int(fondo['peso'] * 100)
            color  = COLORES[i % len(COLORES)] if fondo['isin'] != MONETARIO_ISIN else '#546e7a'
            mom_r  = fondo.get('mom_relativo', 0)
            mom_str = f"{fondo['momentum_12m']:+.1f}%" if fondo['momentum_12m'] is not None else "—"

            col_n, col_p, col_m = st.columns([3, 1, 1])
            with col_n:
                st.markdown(f"<span style='color:#1a1a1a;font-size:14px'>{fondo['nombre']}</span>",
                            unsafe_allow_html=True)
                render_barra_peso(pct, color)
            with col_p:
                st.markdown(f"<span style='font-size:22px;font-weight:700;color:{color}'>{pct}%</span>",
                            unsafe_allow_html=True)
            with col_m:
                mc = "#00c853" if (fondo['momentum_12m'] or 0) > mom_mon else "#546e7a"
                st.markdown(f"<span style='font-size:13px;color:{mc}'>{mom_str}</span>",
                            unsafe_allow_html=True)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="info-box" style="margin-top:12px">
        Pesos proporcionales al momentum relativo vs {MONETARIO_NOMBRE} ({mom_mon:.1f}%).
        Tope máximo: {max_peso_pct}% por fondo. Redondeo al 5% más cercano.
        </div>
        """, unsafe_allow_html=True)

    # =============================================================================
    # MOMENTUM COMPARATIVO
    # =============================================================================

    st.markdown('<div class="section-title">Momentum 12 Meses — Comparativa</div>',
                unsafe_allow_html=True)
    grafico_momentum_comparativo(todos, mom_mon)

    # =============================================================================
    # TABLA DETALLE DE FONDOS
    # =============================================================================

    st.markdown('<div class="section-title">Detalle de Fondos</div>', unsafe_allow_html=True)

    for fondo in todos:
        estado  = fondo['estado']
        sma_i   = fondo.get('sma_info', {})
        peso    = fondo.get('peso', 0)
        mom     = fondo.get('momentum_12m')
        vol     = fondo.get('volatilidad')
        dd      = fondo.get('max_drawdown')
        sha     = fondo.get('sharpe')
        alf     = fondo.get('alfa')
        bet     = fondo.get('beta')

        es_seleccionado = estado == 'candidato'
        clase = "fund-row selected" if es_seleccionado else "fund-row"

        if estado == 'candidato':
            estado_html = f'<span class="badge badge-green">✅ En cartera {int(peso*100)}%</span>'
        elif estado == 'bajo_sma200':
            estado_html = '<span class="badge badge-red">📉 Bajo SMA200</span>'
        elif estado == 'monetario':
            estado_html = '<span class="badge badge-amber">🛡️ No supera monetario</span>'
        else:
            estado_html = '<span class="badge badge-gray">⚠️ Sin datos</span>'

        sma_color = "#00c853" if sma_i.get('sobre_sma', True) else "#ff5252"
        sma_str   = f"{sma_i.get('dist_sma', 0):+.1f}%" if sma_i.get('sma200') else "—"
        mom_color = "#00c853" if (mom or 0) > mom_mon else "#ff5252"
        mom_str   = f"{mom:+.1f}%" if mom is not None else "—"
        vol_str   = f"{vol:.0f}%" if vol else "—"
        dd_str    = f"{dd:.1f}%" if dd else "—"
        sha_str   = f"{sha:.2f}" if sha is not None else "—"
        alf_str   = f"{alf:+.1f}%" if alf is not None else "—"
        bet_str   = f"{bet:.2f}" if bet is not None else "—"
        nav_str   = f"{sma_i.get('nav_actual', 0):.4f}" if sma_i.get('nav_actual') else "—"

        st.markdown(f"""
        <div class="{clase}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
            <div style="flex: 1; min-width: 250px;">
              <span style="font-size:16px;font-weight:600;color:#1a1a1a">{fondo['nombre']}</span>
              <span style="font-size:11px;color:#757575;margin-left:8px">{fondo['isin']}</span>
              <div style="margin-top:6px">{estado_html}</div>
            </div>
            <div style="display:flex;gap:18px;flex-wrap:wrap; justify-content: flex-end;">
              <div style="text-align:center; min-width: 65px;">
                <div style="font-size:10px;color:#546e7a">Mom. 12m</div>
                <div style="font-size:16px;font-weight:700;color:{mom_color}">{mom_str}</div>
              </div>
              <div style="text-align:center; min-width: 65px;">
                <div style="font-size:10px;color:#546e7a">Dist. SMA200</div>
                <div style="font-size:16px;font-weight:700;color:{sma_color}">{sma_str}</div>
              </div>
              <div style="text-align:center; min-width: 60px;">
                <div style="font-size:10px;color:#546e7a">Ratio Sharpe</div>
                <div style="font-size:16px;font-weight:700;color:#82b1ff">{sha_str}</div>
              </div>
              <div style="text-align:center; min-width: 45px;">
                <div style="font-size:10px;color:#546e7a">Alfa (an.)</div>
                <div style="font-size:16px;font-weight:700;color:#00c853">{alf_str}</div>
              </div>
              <div style="text-align:center; min-width: 45px;">
                <div style="font-size:10px;color:#546e7a">Beta</div>
                <div style="font-size:16px;font-weight:700;color:#ffa000">{bet_str}</div>
              </div>
              <div style="text-align:center; min-width: 55px;">
                <div style="font-size:10px;color:#546e7a">Vol. anual</div>
                <div style="font-size:16px;font-weight:700;color:#90a4ae">{vol_str}</div>
              </div>
              <div style="text-align:center; min-width: 55px;">
                <div style="font-size:10px;color:#546e7a">Max DD</div>
                <div style="font-size:16px;font-weight:700;color:#ef9a9a">{dd_str}</div>
              </div>
              <div style="text-align:center; min-width: 65px;">
                <div style="font-size:10px;color:#546e7a">NAV actual</div>
                <div style="font-size:16px;font-weight:700;color:#1a1a1a">{nav_str}</div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # =============================================================================
    # GRÁFICOS NAV INDIVIDUALES
    # =============================================================================

    st.markdown('<div class="section-title">Evolución del NAV</div>', unsafe_allow_html=True)

    fondos_con_datos = [f for f in todos if f['nav'] is not None]
    if fondos_con_datos:
        fondo_sel = st.selectbox(
            "Seleccionar fondo",
            options=[f['isin'] for f in fondos_con_datos],
            format_func=lambda x: next((f['nombre'] for f in fondos_con_datos if f['isin'] == x), x),
            key="sel_fondo_nav"
        )
        fondo_data = next(f for f in fondos_con_datos if f['isin'] == fondo_sel)
        grafico_nav(fondo_data, nav_mon, mostrar_sma)

        # Mostrar evolución multi-fondo normalizada
        st.markdown("**Comparativa todos los fondos (base 100)**")
        fig_multi = go.Figure()
        for i, f in enumerate(fondos_con_datos):
            nav = f['nav']
            nav_norm = nav / nav.iloc[0] * 100
            color = COLORES[i % len(COLORES)]
            dash  = 'solid' if f['estado'] == 'candidato' else 'dot'
            fig_multi.add_trace(go.Scatter(
                x=nav_norm.index[-252:], y=nav_norm.values[-252:],
                name=f['nombre'],
                line=dict(color=color, width=2 if f['estado'] == 'candidato' else 1, dash=dash),
                hovertemplate=f"{f['nombre']}: %{{y:.1f}}<extra></extra>"
            ))
        if nav_mon is not None:
            mon_norm = nav_mon / nav_mon.iloc[0] * 100
            fig_multi.add_trace(go.Scatter(
                x=mon_norm.index[-252:], y=mon_norm.values[-252:],
                name=MONETARIO_NOMBRE,
                line=dict(color='#546e7a', width=1, dash='dot'),
                hovertemplate=f"Monetario: %{{y:.1f}}<extra></extra>"
            ))
        fig_multi.update_layout(
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(248,249,250,0.8)',
            height=350,
            margin=dict(t=20, b=20, l=0, r=0),
            xaxis=dict(gridcolor='#e0e0e0'),
            yaxis=dict(gridcolor='#e0e0e0', title='Base 100'),
            legend=dict(orientation='h', y=1.08, font=dict(size=11)),
            hovermode='x unified'
        )
        st.plotly_chart(fig_multi, use_container_width=True)

with tab_doc:
    st.markdown('<div class="section-title">Metodología Dual Momentum</div>', unsafe_allow_html=True)
    
    st.markdown("""
    La estrategia de **Dual Momentum**, popularizada por Gary Antonacci, combina dos tipos de momentum para maximizar el retorno y minimizar el riesgo:
    
    1.  **Momentum Relativo**: Compara varios activos entre sí y selecciona los que han tenido mejor comportamiento reciente. En esta app, los fondos compiten por un puesto en la cartera según su rentabilidad a 12 meses.
    2.  **Momentum Absoluto**: Actúa como un interruptor de seguridad. Si los activos analizados no baten la rentabilidad de un activo refugio (el monetario) o están en tendencia bajista, el capital se refugia en liquidez.
    
    ### Criterios de Selección
    Un fondo entra en cartera balanceada solo si cumple **todas** estas condiciones:
    - **Positivo vs Monetario**: Su rentabilidad a 12 meses debe ser superior a la del fondo monetario.
    - **Filtro de Tendencia (SMA200)**: El precio (NAV) actual debe estar por encima de su media móvil de 200 días.
    """)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.info("#### ⚙️ Parámetros de Control\\n"
                "- **Ventana de Momentum**: Periodo de tiempo (meses) para calcular la rentabilidad. El estándar es 12 meses.\\n"
                "- **Peso Máximo**: Límite de concentración para evitar que un solo fondo domine la cartera.\\n"
                "- **Rebalanceo**: El sistema calcula pesos automáticos basados en el exceso de momentum sobre el monetario.")
    
    with col_d2:
        st.info("#### �️ Filtros de Seguridad\n"
                "- **SMA200**: Media móvil de los últimos 200 días. Si el precio está por debajo, el fondo se considera en tendencia bajista y se excluye.\n"
                "- **Umbral Monetario**: Si la rentabilidad del fondo es menor a la del monetario, no compensa el riesgo y se refugia en liquidez.")

    st.markdown("""
    ### 📚 Glosario de Métricas
    Para entender mejor los datos del Dashboard e información técnica:
    
    | Métrica | Definición |
    | :--- | :--- |
    | **Mom. 12m** | **Momentum a 12 meses**: Rentabilidad total del fondo en el último año. Diferencia porcentual entre el NAV actual y el de hace un año. |
    | **Dist. SMA200** | **Distancia a la Media**: Porcentaje que separa al precio actual de su media móvil de 200 días. Indica la tendencia de largo plazo. |
    | **Ratio Sharpe** | **Eficiencia**: Indica cuánto retorno extra genera el fondo por cada unidad de volatilidad. > 1.0 es considerado excelente. |
    | **Alfa (an.)** | **Exceso de Retorno**: Rentabilidad adicional que el fondo consigue frente a su índice de referencia (MSCI World). |
    | **Beta** | **Sensibilidad**: Mide cuánto se mueve el fondo respecto al mercado. Beta 1.0 = igual al mercado. |
    | **Vol. anual** | **Volatilidad**: Intensidad de las oscilaciones del fondo. Refleja el riesgo o variabilidad de los retornos. |
    | **Max DD** | **Máxima Caída**: La mayor caída histórica desde un pico. Indica el riesgo de pérdida temporal máxima sufrida. |
    | **NAV actual** | **Precio/V. Liquidativo**: Precio de una participación del fondo a día de hoy. |

    ---
    ### Preguntas Frecuentes
    **¿Cuándo se debe consultar?**  
    La estrategia está diseñada para una revisión mensual, idealmente el primer lunes de cada mes. No es una estrategia de trading diario.
    
    **¿Qué significa el refugio monetario?**  
    Si ningún fondo es apto o si sobra capital tras aplicar los límites de peso, ese porcentaje aparece asignado al fondo monetario (BNP EUR 3M), que actúa como "caja" o liquidez.
    """)

# =============================================================================
# PIE
# =============================================================================

st.markdown("""
<div style="text-align:center;padding:32px 0 16px;color:#757575;font-size:12px;border-top:1px solid #eeeeee;margin-top:40px">
  ⚠️ **Aviso Legal**: Esta herramienta es de carácter informativo y no constituye asesoramiento financiero.<br>
  Verifica siempre la información con tu entidad financiera antes de invertir.
</div>
""", unsafe_allow_html=True)
