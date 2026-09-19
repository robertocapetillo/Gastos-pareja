import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# 1. Configuración de la conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# Configuración de la página
st.set_page_config(page_title="Gastos Roberto y Sandy", page_icon="💰", layout="centered")
st.title("💰 Nuestro Control de Gastos")

# --- FUNCIONES PARA TRAER DATOS ---
@st.cache_data(ttl=5)
def obtener_categorias():
    try:
        res = supabase.table("categorias").select("*").order("nombre").execute()
        return [item["nombre"] for item in res.data]
    except:
        return ["Comida/Súper", "Renta/Servicios", "Salidas/Ocio", "Transporte", "Otros"]

@st.cache_data(ttl=5)
def obtener_gastos():
    try:
        respuesta = supabase.table("gastos").select("*").order("fecha", desc=True).execute()
        return respuesta.data
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return []

# Cargar categorías dinámicas
lista_categorias = obtener_categorias()

# 2. SECCIÓN DE CONFIGURACIÓN (Administrar Categorías)
with st.expander("🛠️ Administrar Categorías de Gastos"):
    st.markdown("**Agregar nueva categoría:**")
    nueva_cat = st.text_input("Nombre de la categoría", placeholder="Ej. Mascotas").strip()
    if st.button("➕ Agregar Categoría"):
        if nueva_cat:
            try:
                supabase.table("categorias").insert({"nombre": nueva_cat}).execute()
                st.success(f"¡Categoría '{nueva_cat}' añadida!")
                st.cache_data.clear()
                st.rerun()
            except:
                st.error("Esta categoría ya existe o hubo un error.")
        else:
            st.warning("Por favor, escribe un nombre para la categoría.")

# 3. FORMULARIO DE REGISTRO DE GASTOS
st.subheader("📝 Registrar Nuevo Gasto")
with st.form("formulario_gastos", clear_on_submit=True):
    fecha = st.date_input("Fecha", datetime.date.today())
    descripcion = st.text_input("Descripción / Concepto", placeholder="Ej. Súper semanal, Gasolina...")
    monto = st.number_input("Monto ($)", min_value=0.0, step=0.01, format="%.2f")
    categoria = st.selectbox("Categoría", lista_categorias)
    pagado_por = st.selectbox("¿Quién lo pagó?", ["Roberto", "Sandy", "Ambos (50/50)"])
    
    # 🆕 NUEVO CAMPO: Método de pago
    metodo_pago = st.selectbox("Método de Pago", ["Tarjeta", "Efectivo", "Transferencia"])
    
    boton_guardar = st.form_submit_button("💾 Guardar Gasto")

if boton_guardar:
    if monto > 0 and descripcion:
        nuevo_gasto = {
            "fecha": str(fecha),
            "descripcion": descripcion,
            "monto": monto,
            "categoria": categoria,
            "pagado_por": pagado_por,
            "metodo_pago": metodo_pago  # 🆕 Se envía a Supabase
        }
        try:
            supabase.table("gastos").insert(nuevo_gasto).execute()
            st.success("¡Gasto registrado exitosamente!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar el gasto: {e}")
    else:
        st.error("Por favor, introduce una descripción y un monto mayor a 0.")

# 4. HISTORIAL Y VISUALIZACIÓN DE GASTOS
st.subheader("📊 Historial de Gastos")
datos_gastos = obtener_gastos()

if datos_gastos:
    df = pd.DataFrame(datos_gastos)
    df['fecha'] = pd.to_datetime(df['fecha']).dt.date
    
    # Métricas rápidas
    total_gastado = df['monto'].sum()
    st.metric(label="Total Gastado", value=f"${total_gastado:,.2f}")
    
    # Mostrar tabla limpia incluyendo la nueva columna si existe en la base de datos
    columnas_mostrar = [c for c in ['fecha', 'descripcion', 'categoria', 'monto', 'pagado_por', 'metodo_pago'] if c in df.columns]
    st.dataframe(df[columnas_mostrar], use_container_width=True)
else:
    st.info("Aún no hay gastos registrados.")
