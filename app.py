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

def consultar_todos_los_ingresos():
    url = "https://mercadopago.com"
    headers = {"Authorization": f"Bearer {TOKEN_MP}"}
    
    # Traemos los últimos 30 movimientos mezclando transferencias y cobros comerciales
    params = {
        "sort": "date_created",
        "criteria": "desc",
        "limit": 30
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=2.0)
        if res.status_code == 200:
            datos = res.json().get("results", [])
            lista_final = []
            
            for pago in datos:
                estado = pago.get("status", "")
                tipo_operacion = pago.get("operation_type", "")
                
                # Filtramos únicamente los ingresos que estén aprobados (dinero real en tu cuenta)
                if estado == "approved":
                    f = pago.get("date_created", "")
                    hora = f[11:16] if f else "--:--"
                    
                    monto = float(pago.get("transaction_amount", 0))
                    medio = pago.get("payment_method_id", "Otros").upper()
                    
                    # Identificamos el origen real de la transferencia por Alias o banco externo
                    detalle = pago.get("description")
                    if not detalle:
                        tarjeta_nombre = pago.get("card", {}).get("cardholder", {}).get("name")
                        if tarjeta_nombre:
                            detalle = tarjeta_nombre
                        elif "bank_transfer" in tipo_operacion or medio == "BANK_TRANSFER":
                            detalle = "Transferencia Bancaria (Alias/CBU)"
                        elif medio == "ACCOUNT_MONEY":
                            detalle = "Transferencia desde otra cuenta MP"
                        else:
                            detalle = "Ingreso de Dinero"
                    
                    lista_final.append({
                        "Hora": hora,
                        "Monto Recibido ($)": monto,
                        "Origen / Tipo": detalle,
                        "Medio": medio,
                        "ID Operación": str(pago.get("id"))
                    })
            return pd.DataFrame(lista_final)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

tabla_viva = consultar_todos_los_ingresos()

# Si la tabla viene vacía, armamos estructura limpia
if tabla_viva.empty:
    tabla_viva = pd.DataFrame(columns=["Hora", "Monto Recibido ($)", "Origen / Tipo", "Medio", "ID Operación"])

# PANEL SUPERIOR (Métricas gigantes)
col1, col2 = st.columns(2)

if not tabla_viva.empty:
    df_filtrado = tabla_viva.copy()
    ultima = df_filtrado.iloc[0] # El movimiento más nuevo arriba de todo
    monto_ult = f"${ultima['Monto Recibido ($)']:,.2f}"
    det_ult = f"{ultima['Hora']} - {ultima['Origen / Tipo']}"
    total_acumulado = df_filtrado["Monto Recibido ($)"].sum()
else:
    monto_ult = "$0.00"
    det_ult = "Esperando transferencia por Alias..."
    total_acumulado = 0.0

with col1:
    st.metric(label="🚨 ÚLTIMA TRANSFERENCIA DETECTADA", value=monto_ult, delta=det_ult)
with col2:
    st.metric(label="💰 TOTAL RECIBIDO RECIENTE", value=f"${total_acumulado:,.2f}")

st.markdown("---")
st.subheader("📋 Registro de Transferencias Recientes")

if not tabla_viva.empty:
    st.dataframe(tabla_viva, use_container_width=True, height=400)
else:
    st.info("No se registran ingresos recientes en el historial. El monitor está activo esperando transferencias por Alias...")

# Bucle automático de ráfaga de 2 segundos
time.sleep(2)
st.rerun()
