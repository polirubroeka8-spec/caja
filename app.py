import streamlit as st
import requests
import pandas as pd
import time

# CREDENCIALES
TOKEN_MP = "APP_USR-2109822195706525-070122-23e9a6051330a533196e8de5669d6782-188405054"
CLAVE_ACCESO = "polirubroeka1y2"

st.set_page_config(page_title="Monitor Polirubro", page_icon="⚡", layout="wide")

# Inicializar memoria para las notificaciones en vivo
if "lista_webhooks" not in st.session_state:
    st.session_state["lista_webhooks"] = []

# 1. SEGURIDAD
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔒 Panel Restringido - Polirubro")
    pass_input = st.text_input("Introduce la contraseña de la caja:", type="password", key="pass")
    if st.button("Ingresar al Panel", use_container_width=True):
        if pass_input == CLAVE_ACCESO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# 2. PANEL EN VIVO
st.title("⚡ Monitor por Notificación Instantánea (Webhooks)")
hora_actual = time.strftime("%H:%M:%S")
st.caption(f"🔄 Esperando alertas en tiempo real de Mercado Pago... [Último control: {hora_actual}]")

# Capturar si Mercado Pago nos envía un aviso directo por los parámetros de la URL web
query_params = st.query_params
if "data.id" in query_params or "id" in query_params:
    id_pago = query_params.get("data.id") or query_params.get("id")
    
    # Si recibimos un ID nuevo, consultamos sus detalles específicos a Mercado Pago de inmediato
    if id_pago and id_pago not in [x.get("ID Operación") for x in st.session_state["lista_webhooks"]]:
        url_pago = f"https://mercadopago.com{id_pago}"
        headers = {"Authorization": f"Bearer {TOKEN_MP}"}
        try:
            res = requests.get(url_pago, headers=headers, timeout=2.0)
            if res.status_code == 200:
                pago_data = res.json()
                if pago_data.get("status") == "approved":
                    monto = float(pago_data.get("transaction_amount", 0))
                    desc = pago_data.get("description") or "Transferencia por Alias / CVU"
                    
                    # Guardamos la transferencia en la pantalla
                    st.session_state["lista_webhooks"].insert(0, {
                        "Hora": time.strftime("%H:%M"),
                        "Monto Recibido ($)": monto,
                        "Origen / Detalle": desc,
                        "ID Operación": str(id_pago)
                    })
        except:
            pass

# Convertir las alertas recibidas en tabla
if st.session_state["lista_webhooks"]:
    tabla_viva = pd.DataFrame(st.session_state["lista_webhooks"])
else:
    tabla_viva = pd.DataFrame(columns=["Hora", "Monto Recibido ($)", "Origen / Detalle", "ID Operación"])

# MOSTRAR MÉTRICAS
col1, col2 = st.columns(2)
if not tabla_viva.empty:
    ultima = tabla_viva.iloc[0]
    monto_ult = f"${ultima['Monto Recibido ($)']:,.2f}"
    det_ult = f"{ultima['Hora']} - {ultima['Origen / Detalle']}"
    total_acumulado = tabla_viva["Monto Recibido ($)"].sum()
else:
    monto_ult = "$0.00"
    det_ult = "Esperando primera notificación..."
    total_acumulado = 0.0

with col1:
    st.metric(label="🚨 ÚLTIMO INGRESO NOTIFICADO", value=monto_ult, delta=det_ult)
with col2:
    st.metric(label="💰 TOTAL ACUMULADO EN CAJA", value=f"${total_acumulado:,.2f}")

st.markdown("---")
st.subheader("📋 Registro de Alertas en Tiempo Real")
if not tabla_viva.empty:
    st.dataframe(tabla_viva, use_container_width=True, height=400)
else:
    st.info("Configurá la URL de esta página en tus Webhooks de Mercado Pago para empezar a recibir las transferencias automáticamente.")

# Recarga corta de 2 segundos para chequear si entró algún parámetro nuevo por red
time.sleep(2)
st.rerun()
