#!/usr/bin/env python
# coding: utf-8

# In[11]:


import sys


# In[26]:


import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# 1. Configuración de la conexión a Supabase (¡Cambia esto con tus datos!)
SUPABASE_URL = "https://ylgnfodvizlncqbqjskd.supabase.co"
SUPABASE_KEY = "sb_secret_Z5p7zKkppBbcxeagfZOuXQ_9MQCEm_O"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# Configuración de la página
st.set_page_config(page_title="Gastos Compartidos", page_icon="💰", layout="centered")
st.title("💰 Nuestro Control de Gastos")

# 2. Formulario para agregar un gasto
st.subheader("📝 Registrar nuevo gasto")
with st.form("formulario_gasto", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        monto = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f")
        categoria = st.selectbox("Categoría", ["Comida/Súper", "Renta/Servicios", "Salidas/Ocio", "Transporte", "Otros"])
    with col2:
        descripcion = st.text_input("¿En qué gastamos?", placeholder="Ej. Mandado semanal")
        pagado_por = st.radio("¿Quién lo pagó?", ["Persona A", "Persona B"], horizontal=True) # Cambia por sus nombres
    
    fecha = st.date_input("Fecha", datetime.date.today())
    botón_guardar = st.form_submit_button("Guardar Gasto")

# Acción al presionar el botón
if botón_guardar:
    if monto > 0 and descripcion:
        # Estructura del dato a enviar a la nube
        nuevo_gasto = {
            "fecha": str(fecha),
            "descripcion": descripcion,
            "monto": monto,
            "categoria": categoria,
            "pagado_por": pagado_por
        }
        # Insertar en la base de datos
        supabase.table("gastos").insert(nuevo_gasto).execute()
        st.success("¡Gasto guardado correctamente!")
        st.rerun()
    else:
        st.error("Por favor, introduce un monto válido y una descripción.")

st.divider()

# 3. Visualización y cuentas del mes
st.subheader("📊 Historial y Resumen")

# Creamos una función específica para traer los datos y evitar el conflicto de hilos
@st.cache_data(ttl=5) # El ttl=5 hace que refresque los datos de la nube cada 5 segundos si hay cambios
def obtener_gastos():
    try:
        respuesta = supabase.table("gastos").select("*").order("fecha", desc=True).execute()
        return respuesta.data
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return []

# Llamamos a la función
datos = obtener_gastos()

if datos:
    df = pd.DataFrame(datos)
    
    # Mostrar tabla limpia (eliminando columnas técnicas internas)
    df_mostrar = df[["fecha", "descripcion", "monto", "categoria", "pagado_por"]]
    st.dataframe(df_mostrar, use_container_width=True)
    
    # Cálculos matemáticos
    total_gastado = df["monto"].sum()
    gastos_persona_a = df[df["pagado_por"] == "Persona A"]["monto"].sum()
    gastos_persona_b = df[df["pagado_por"] == "Persona B"]["monto"].sum()
    
    # Suponiendo división 50/50
    mitad = total_gastado / 2
    
    # Mostrar métricas visuales
    st.metric(label="Total Gastado Colectivo", value=f"${total_gastado:,.2f}")
    
    c1, c2 = st.columns(2)
    c1.metric(label="Pagado por Persona A", value=f"${gastos_persona_a:,.2f}")
    c2.metric(label="Pagado por Persona B", value=f"${gastos_persona_b:,.2f}")
    
    # Lógica de quién le debe a quién
    st.subheader("⚖️ Balance de Cuentas")
    if gastos_persona_a > mitad:
        debe = gastos_persona_a - mitad
        st.info(f"💡 **Persona B** le debe a **Persona A**: `${debe:,.2f}` para quedar 50/50.")
    elif gastos_persona_b > mitad:
        debe = gastos_persona_b - mitad
        st.info(f"💡 **Persona A** le debe a **Persona B**: `${debe:,.2f}` para quedar 50/50.")
    else:
        st.success("🎉 ¡Están perfectamente a mano!")
else:
    st.info("Aún no hay gastos registrados. ¡Empiecen anotando el primero arriba!")


# In[ ]:





# In[ ]:




