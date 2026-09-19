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
            "metodo_pago": metodo_pago
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

# 4. NUEVA SECCIÓN: GRÁFICAS Y ESTADÍSTICAS TEMPORALES
st.markdown("---")
st.subheader("📊 Análisis de Gastos")

datos_gastos = obtener_gastos()

if datos_gastos:
    # Convertir a DataFrame y procesar fechas
    df_analisis = pd.DataFrame(datos_gastos)
    df_analisis['fecha'] = pd.to_datetime(df_analisis['fecha']).dt.date
    
    # Obtener fechas de referencia (Hoy, inicio de semana e inicio de mes)
    hoy = datetime.date.today()
    inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())  # Lunes de esta semana
    inicio_mes = hoy.replace(day=1)                              # Día 1 de este mes
    
    # Filtrar datos por periodos
    df_hoy = df_analisis[df_analisis['fecha'] == hoy]
    df_semana = df_analisis[(df_analisis['fecha'] >= inicio_semana) & (df_analisis['fecha'] <= hoy)]
    df_mes = df_analisis[(df_analisis['fecha'] >= inicio_mes) & (df_analisis['fecha'] <= hoy)]
    
    # Calcular totales numéricos
    total_hoy = df_hoy['monto'].sum()
    total_semana = df_semana['monto'].sum()
    total_mes = df_mes['monto'].sum()
    
    # Mostrar tarjetas de métricas en tres columnas
    col1, col2, col3 = st.columns(3)
    col1.metric("Gastado Hoy", f"${total_hoy:,.2f}")
    col2.metric("Esta Semana", f"${total_semana:,.2f}")
    col3.metric("Este Mes", f"${total_mes:,.2f}")
    
    # Pestañas interactivas para cambiar de gráfica
    tab_dia, tab_semana, tab_mes = st.tabs(["📅 Gastos de Hoy", "📆 Esta Semana", "🗓️ Este Mes"])
    
    with tab_dia:
        if not df_hoy.empty:
            st.markdown("**Desglose por Categoría (Hoy)**")
            gastos_hoy_cat = df_hoy.groupby('categoria')['monto'].sum()
            st.bar_chart(gastos_hoy_cat)
        else:
            st.info("No se han registrado gastos el día de hoy.")
            
    with tab_semana:
        if not df_semana.empty:
            st.markdown("**Evolución de gastos día a día (Esta semana)**")
            # Agrupar por fecha para ver la evolución diaria
            gastos_semana_dias = df_semana.groupby('fecha')['monto'].sum()
            st.line_chart(gastos_semana_dias)
        else:
            st.info("No hay gastos registrados en esta semana calendario.")
            
    with tab_mes:
        if not df_mes.empty:
            st.markdown("**Distribución por Categoría (Este mes)**")
            gastos_mes_cat = df_mes.groupby('categoria')['monto'].sum()
            st.bar_chart(gastos_mes_cat)
        else:
            st.info("No hay gastos registrados en este mes.")

# 5. HISTORIAL Y VISUALIZACIÓN DE GASTOS
st.markdown("---")
st.subheader("📋 Historial Completo")

if datos_gastos:
    df_tabla = pd.DataFrame(datos_gastos)
    df_tabla['fecha'] = pd.to_datetime(df_tabla['fecha']).dt.date
    
    columnas_mostrar = [c for c in ['fecha', 'descripcion', 'categoria', 'monto', 'pagado_por', 'metodo_pago'] if c in df_tabla.columns]
    st.dataframe(df_tabla[columnas_mostrar], use_container_width=True)
else:
    st.info("Aún no hay gastos registrados.")
