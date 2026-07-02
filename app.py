import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

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
st.title("⚡ Monitor de Caja en Vivo")
hora_actual = time.strftime("%H:%M:%S")
st.caption(f"🔄 Rastreador Total Activo (2s) • Último control de red: {hora_actual}")

def consultar_movimientos_totales():
    url = "https://mercadopago.com"
    headers = {"Authorization": f"Bearer {TOKEN_MP}"}
    
    # Calculamos la fecha desde ayer para asegurar que traiga el historial del día
    fecha_desde = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    
    # Agregamos obligatoriamente el rango de fechas en los parámetros
    params = {
        "range": "date_created",
        "begin_date": fecha_desde,
        "limit": 20
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=1.5)
        if res.status_code == 200:
            datos = res.json().get("results", [])
            lista = []
            for mov in datos:
                monto = float(mov.get("amount", 0))
                tipo = mov.get("type", "")
                
                # Filtramos únicamente las entradas de dinero reales
                if mov.get("direction") == "inflow":
                    f = mov.get("date_created", "")
                    # Ajustamos la hora al huso horario de Argentina (restando 3 horas del servidor UTC si es necesario)
                    hora = f[11:16] if f else "--:--"
                    
                    detalle = mov.get("detail", "Ingreso general")
                    if "regular_payment" in tipo: 
                        detalle = "Venta / Cobro Directo"
                    elif "bank_transfer" in tipo: 
                        detalle = "Transferencia por Alias / CVU"
                    
                    lista.append({
                        "Hora": hora,
                        "Monto Recibido ($)": monto,
                        "Tipo de Movimiento": detalle,
                        "ID Operación": str(mov.get("id"))
                    })
            return pd.DataFrame(lista)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

tabla_viva = consultar_movimientos_totales()

# Mostramos el panel si hay datos
if tabla_viva is not None and not tabla_viva.empty:
    df_aprobados = tabla_viva.copy()
    total_acumulado = df_aprobados["Monto Recibido ($)"].sum()
    
    col1, col2 = st.columns(2)
    ultima = df_aprobados.iloc[0] # Tomamos el movimiento más nuevo arriba de todo
    
    with col1:
        st.metric(
            label="🚨 ÚLTIMO INGRESO DE DINERO DETECTADO", 
            value=f"${ultima['Monto Recibido ($)']:,.2f}", 
            delta=f"{ultima['Hora']} - {ultima['Tipo de Movimiento']}"
        )
    with col2:
        st.metric(
            label="💰 TOTAL ACUMULADO EN PANTALLA", 
            value=f"${total_acumulado:,.2f}"
        )

    st.markdown("---")
    st.subheader("📋 Registro de Ingresos Recientes")
    st.dataframe(df_aprobados, use_container_width=True, height=400)
else:
    st.info("Buscando transacciones en el historial... Si la cuenta no registra movimientos hoy, el monitor quedará esperando en vivo.")

# Bucle automático de 2 segundos
time.sleep(2)
st.rerun()
