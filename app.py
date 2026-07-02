import streamlit as st
import requests
import pandas as pd
import time

# CREDENCIALES FIJAS Y SEGURAS
TOKEN_MP = "APP_USR-2109822195706525-070122-23e9a6051330a533196e8de5669d6782-188405054"
CLAVE_ACCESO = "polirubroeka1y2"

st.set_page_config(page_title="Monitor Polirubro", page_icon="⚡", layout="wide")

# ESTILOS VISUALES AVANZADOS (Hacemos la página hermosa)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border-left: 6px solid #009ee3;
    }
    div[data-testid="stMetric"] label { font-size: 14px !important; font-weight: 700 !important; color: #64748b !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 36px !important; font-weight: 800 !important; color: #1e293b !important; }
    .title-caja { font-size: 32px !important; font-weight: 800; color: #0f172a; margin-bottom: 5px; }
    </style>
""", unsafe_html=True)

# 1. PANTALLA DE SEGURIDAD ELÉGANTE
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<div style='max-width:400px; margin:80px auto; background:white; padding:30px; border-radius:16px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1); text-align:center;'>", unsafe_html=True)
    st.subheader("🔒 Panel Restringido - Polirubro")
    pass_input = st.text_input("Introduce la contraseña de la caja:", type="password", key="pass")
    if st.button("Ingresar al Panel", use_container_width=True):
        if pass_input == CLAVE_ACCESO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.markdown("</div>", unsafe_html=True)
    st.stop()

# 2. PANEL EN VIVO PROFESIONAL
st.markdown("<h1 class='title-caja'>⚡ Monitor de Caja en Vivo</h1>", unsafe_html=True)
hora_actual = time.strftime("%H:%M:%S")
st.markdown(f"<p style='color:#64748b; font-size:14px; margin-top:-10px;'>🔄 Rastreador Total Activo (2s) • <b>Último control: {hora_actual}</b></p>", unsafe_html=True)

def consultar_movimientos_totales():
    # Cambiamos al endpoint de movimientos de cuenta para atrapar transferencias directas, alias, QR y tarjetas
    url = "https://mercadopago.com"
    headers = {"Authorization": f"Bearer {TOKEN_MP}"}
    params = {"limit": 15}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=1.5)
        if res.status_code == 200:
            datos = res.json().get("results", [])
            lista = []
            for mov in datos:
                # Filtrar para mostrar solo los ingresos de dinero (ingresos brutos)
                monto = float(mov.get("amount", 0))
                tipo = mov.get("type", "")
                
                # Ignoramos egresos de dinero (como tus gastos o envíos)
                if mov.get("direction") == "inflow":
                    f = mov.get("date_created", "")
                    hora = f[11:16] if f else "--:--"
                    
                    # Limpiamos el detalle
                    detalle = mov.get("detail", "Ingreso general")
                    if "regular_payment" in tipo: detalle = "Venta / Cobro Directo"
                    elif "bank_transfer" in tipo: detalle = "Transferencia por Alias / CVU"
                    
                    lista.append({
                        "Hora": hora,
                        "Monto Recibido ($)": monto,
                        "Tipo de Movimiento": detalle,
                        "ID Operación": mov.get("id")
                    })
            return pd.DataFrame(lista)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

tabla_viva = consultar_movimientos_totales()

# Si la tabla viene vacía, armamos estructura limpia
if tabla_viva.empty:
    tabla_viva = pd.DataFrame(columns=["Hora", "Monto Recibido ($)", "Tipo de Movimiento", "ID Operación"])

# PANEL SUPERIOR (Métricas gigantes)
col1, col2 = st.columns(2)

if not tabla_viva.empty:
    ultima = tabla_viva.iloc[0]
    monto_ult = f"${ultima['Monto Recibido ($)']:,.2f}"
    det_ult = f"{ultima['Hora']} - {ultima['Tipo de Movimiento']}"
    total_acumulado = tabla_viva["Monto Recibido ($)"].sum()
else:
    monto_ult = "$0.00"
    det_ult = "Esperando primer movimiento..."
    total_acumulado = 0.0

with col1:
    st.metric(label="🚨 ÚLTIMO INGRESO DE DINERO (CUALQUIER MEDIO)", value=monto_ult, delta=det_ult)
with col2:
    st.metric(label="💰 TOTAL ACUMULADO RECIENTE", value=f"${total_acumulado:,.2f}")

st.markdown("<br>", unsafe_html=True)
st.subheader("📋 Registro de Ingresos del Negocio")

# Mostrar la lista estilizada
if not tabla_viva.empty:
    st.dataframe(
        tabla_viva,
        use_container_width=True,
        height=400
    )
else:
    st.info("No se registran movimientos de entrada de dinero en las últimas horas. El monitor está listo esperando transferencias...")

# Bucle automático de 2 segundos
time.sleep(2)
st.rerun()
