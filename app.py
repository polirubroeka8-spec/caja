import streamlit as st
import requests
import pandas as pd
import time

# CREDENCIALES FIJAS Y SEGURAS
TOKEN_MP = "APP_USR-2109822195706525-070122-23e9a6051330a533196e8de5669d6782-188405054"
CLAVE_ACCESO = "polirubroeka1y2"

st.set_page_config(page_title="Monitor Polirubro", page_icon="⚡", layout="wide")

# 1. PANTALLA DE SEGURIDAD
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔒 Panel Restringido - Polirubro")
    pass_input = st.text_input("Introduce la contraseña de la caja:", type="password")
    if st.button("Ingresar al Panel"):
        if pass_input == CLAVE_ACCESO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# 2. PANEL EN VIVO (SÓLO ENTRA SI LA CLAVE ES CORRECTA)
st.title("⚡ Monitor de Transferencias en Tiempo Real")
hora_actual = time.strftime("%H:%M:%S")
st.caption(f"🔄 Modo ráfaga activo. Controlando Mercado Pago cada 2 segundos... [Último control: {hora_actual}]")

# Consulta directa a la API de Mercado Pago
def consultar_mercado_pago():
    url = "https://mercadopago.com"
    headers = {"Authorization": f"Bearer {TOKEN_MP}"}
    params = {"sort": "date_created", "criteria": "desc", "limit": 10}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=1.5)
        if res.status_code == 200:
            datos = res.json().get("results", [])
            lista = []
            for pago in datos:
                f = pago.get("date_created", "")
                hora = f[11:16] if f else "--:--"
                cliente = pago.get("description") or pago.get("card", {}).get("cardholder", {}).get("name") or "Transferencia Recibida"
                lista.append({
                    "Hora": hora,
                    "Monto ($)": float(pago.get("transaction_amount", 0)),
                    "Neto Recibido ($)": float(pago.get("transaction_details", {}).get("net_received_amount", 0)),
                    "Cliente / Detalle": cliente,
                    "Medio": pago.get("payment_method_id", "Otros").upper(),
                    "Estado": pago.get("status")
                })
            return pd.DataFrame(lista)
        return None
    except:
        return None

tabla_viva = consultar_mercado_pago()

if tabla_viva is not None and not tabla_viva.empty:
    df_aprobados = tabla_viva[tabla_viva["Estado"] == "approved"]
    
    # Métricas en grande
    col1, col2, col3 = st.columns(3)
    ultima = tabla_viva.iloc[0]
    with col1:
        st.metric(label="🚨 ÚLTIMO INGRESO", value=f"${ultima['Monto ($)']:,.2f}", delta=f"{ultima['Hora']} - {ultima['Cliente / Detalle'][:15]}")
    with col2:
        st.metric(label="💰 Total Bruto Reciente", value=f"${df_aprobados['Monto ($)'].sum():,.2f}")
    with col3:
        st.metric(label="🏦 Total Neto Real", value=f"${df_aprobados['Neto Recibido ($)'].sum():,.2f}")
        
    st.markdown("---")
    
    # Tabla interactiva con colores
    def colorear(val):
        if val == "approved": return "background-color: #d4edda; color: #155724; font-weight: bold;"
        if val == "in_process": return "background-color: #fff3cd; color: #856404;"
        return "background-color: #f8d7da; color: #721c24;"
        
    st.dataframe(tabla_viva.style.map(colorear, subset=["Estado"]), use_container_width=True, height=350)
else:
    st.info("Sincronizando flujo de datos...")

# Reloj de recarga automática cada 2 segundos
time.sleep(2)
st.rerun()
