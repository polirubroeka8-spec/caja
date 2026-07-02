import streamlit as st
import requests
import pandas as pd
import time

# CREDENCIALES FIJAS Y SEGURAS
TOKEN_MP = "APP_USR-2109822195706525-070122-23e9a6051330a533196e8de5669d6782-188405054"
CLAVE_ACCESO = "polirubroeka1y2"

st.set_page_config(page_title="Monitor Polirubro", page_icon="⚡", layout="wide")

# 1. PANTALLA DE SEGURIDAD DIRECTA
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

# 2. PANEL EN VIVO AUTOMÁTICO
st.title("⚡ Monitor de Transferencias por Alias / CVU")
hora_actual = time.strftime("%H:%M:%S")
st.caption(f"🔄 Modo ráfaga activo • Buscando transferencias cada 2 segundos... [Último control: {hora_actual}]")

def consultar_transferencias_alias():
    # Buscador de movimientos de cuenta (lee transferencias directas de CBU/Alias)
    url = "https://mercadopago.com"
    headers = {"Authorization": f"Bearer {TOKEN_MP}"}
    params = {"limit": 20}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=2.0)
        if res.status_code == 200:
            datos = res.json().get("results", [])
            lista_transferencias = []
            
            for mov in datos:
                # Solo tomamos dinero que ENTRA ('inflow')
                if mov.get("direction") == "inflow":
                    monto = float(mov.get("amount", 0))
                    tipo = mov.get("type", "")
                    
                    f = mov.get("date_created", "")
                    hora = f[11:16] if f else "--:--"
                    
                    detalle = mov.get("detail", "Ingreso de dinero")
                    if "bank_transfer" in tipo or "transfer" in tipo:
                        detalle = "Transferencia por Alias / CVU"
                    elif "mp_transfer" in tipo:
                        detalle = "Envío desde otra cuenta MP"
                    
                    lista_transferencias.append({
                        "Hora": hora,
                        "Monto Recibido ($)": monto,
                        "Origen / Tipo": detalle,
                        "ID Operación": str(mov.get("id"))
                    })
            return pd.DataFrame(lista_transferencias)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

tabla_viva = consultar_transferencias_alias()

if tabla_viva is not None and not tabla_viva.empty:
    df_aprobados = tabla_viva.copy()
    total_acumulado = df_aprobados["Monto Recibido ($)"].sum()
    
    col1, col2 = st.columns(2)
    ultima = df_aprobados.iloc[0] # El movimiento más nuevo arriba de todo
    
    with col1:
        st.metric(
            label="🚨 ÚLTIMA TRANSFERENCIA DETECTADA", 
            value=f"${ultima['Monto Recibido ($)']:,.2f}", 
            delta=f"{ultima['Hora']} - {ultima['Origen / Tipo']}"
        )
    with col2:
        st.metric(
            label="💰 TOTAL RECIBIDO RECIENTE", 
            value=f"${total_acumulado:,.2f}"
        )

    st.markdown("---")
    st.subheader("📋 Registro de Transferencias Recientes")
    st.dataframe(df_aprobados, use_container_width=True, height=400)
else:
    st.info("No se registran transferencias recientes. El monitor está activo esperando ingresos por Alias...")

# Bucle automático de ráfaga de 2 segundos
time.sleep(2)
st.rerun()
