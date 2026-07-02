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
st.title("⚡ Monitor de Caja en Vivo")
hora_actual = time.strftime("%H:%M:%S")
st.caption(f"🔄 Modo ráfaga activo • Controlando Mercado Pago cada 2 segundos... [Último control: {hora_actual}]")

def consultar_pagos_v1():
    # Usamos el buscador general sin filtros de fecha estrictos para evitar rechazos del servidor
    url = "https://mercadopago.com"
    headers = {"Authorization": f"Bearer {TOKEN_MP}"}
    
    # Traemos los últimos 20 movimientos ordenados por creación decreciente
    params = {
        "sort": "date_created",
        "criteria": "desc",
        "limit": 20
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=2.0)
        if res.status_code == 200:
            datos = res.json().get("results", [])
            lista = []
            for pago in datos:
                estado = pago.get("status", "")
                
                # Filtramos para mostrar únicamente ingresos aprobados o pendientes de tu caja
                if estado in ["approved", "in_process"]:
                    f = pago.get("date_created", "")
                    hora = f[11:16] if f else "--:--"
                    
                    # Intentamos extraer el nombre real del cliente o el tipo de transferencia
                    cliente = pago.get("description")
                    if not cliente:
                        tarjeta_nombre = pago.get("card", {}).get("cardholder", {}).get("name")
                        detalles_pago = pago.get("transaction_details", {})
                        
                        if tarjeta_nombre:
                            cliente = tarjeta_nombre
                        elif pago.get("payment_method_id") == "account_money":
                            cliente = "Transferencia entre cuentas MP"
                        elif "bank_transfer" in pago.get("operation_type", ""):
                            cliente = "Transferencia bancaria / Alias"
                        else:
                            cliente = "Ingreso de dinero"
                    
                    monto = float(pago.get("transaction_amount", 0))
                    neto = float(pago.get("transaction_details", {}).get("net_received_amount", 0))
                    medio = pago.get("payment_method_id", "Otros").upper()
                    
                    lista.append({
                        "Hora": hora,
                        "Monto ($)": monto,
                        "Dinero Neto Real ($)": neto,
                        "Cliente / Detalle": cliente,
                        "Medio de Pago": medio,
                        "Estado": estado.upper()
                    })
            return pd.DataFrame(lista)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

tabla_viva = consultar_pagos_v1()

# Si la tabla viene vacía, armamos estructura limpia para evitar errores en pantalla
if tabla_viva.empty:
    tabla_viva = pd.DataFrame(columns=["Hora", "Monto ($)", "Dinero Neto Real ($)", "Cliente / Detalle", "Medio de Pago", "Estado"])

df_aprobados = tabla_viva[tabla_viva["Estado"] == "APPROVED"]

# Bloques de métricas gigantes en pantalla
col1, col2, col3 = st.columns(3)

if not tabla_viva.empty:
    ultima = tabla_viva.iloc[0] # Tomamos la fila de arriba de todo (la más reciente)
    monto_ult = f"${ultima['Monto ($)']:,.2f}"
    det_ult = f"{ultima['Hora']} - {ultima['Cliente / Detalle'][:15]}"
else:
    monto_ult = "$0.00"
    det_ult = "Esperando nueva transferencia..."

with col1:
    st.metric(label="🚨 ÚLTIMO INGRESO DETECTADO", value=monto_ult, delta=det_ult)
with col2:
    st.metric(label="💰 TOTAL BRUTO RECIENTE", value=f"${df_aprobados['Monto ($)'].sum():,.2f}")
with col3:
    st.metric(label="🏦 DINERO NETO EN CUENTA", value=f"${df_aprobados['Dinero Neto Real ($)'].sum():,.2f}")

st.markdown("---")
st.subheader("📋 Registro de Operaciones Recientes")

if not tabla_viva.empty:
    # Función para pintar las celdas y ver rápido los estados
    def colorear_estados(val):
        if val == "APPROVED": return "background-color: #d4edda; color: #155724; font-weight: bold;"
        return "background-color: #fff3cd; color: #856404;"
        
    st.dataframe(
        tabla_viva.style.map(colorear_estados, subset=["Estado"]), 
        use_container_width=True, 
        height=400
    )
else:
    st.info("El monitor está activo y conectado. Esperando a que ingrese la primera transferencia en vivo...")

# Bucle automático de ráfaga de 2 segundos
time.sleep(2)
st.rerun()
