import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# 1. Configuración de la conexión a Supabase leyendo los Secretos protegidos
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
    nueva_cat = st.text_input("Nombre de la categoría (Ej. Mascotas, Salud)", placeholder="Ej. Mascotas").strip()
    if st.button("➕ Agregar Categoría"):
        if nueva_cat:
            try:
                supabase.table("categorias").insert({"nombre": nueva_cat}).execute()
                st.success(f"¡Categoría '{nueva_cat}' añadida!")
                st.cache_data.clear()
                st.slots.clear() if hasattr(st, 'slots') else None
                st.rerun()
            except:
                st.error("Esta categoría ya existe o hubo un error.")
        else:
            st.error("Escribe un nombre válido.")

# 3. Formulario para agregar un gasto
st.subheader("📝 Registrar nuevo gasto")
with st.form("formulario_gasto", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        monto = st.number_input("Monto (\$)", min_value=0.0, step=10.0, format="%.2f")
        categoria = st.selectbox("Categoría", lista_categorias) # Lista dinámica
    with col2:
        descripcion = st.text_input("¿En qué gastamos?", placeholder="Ej. Mandado semanal")
        pagado_por = st.radio("¿Quién lo pagó?", ["Roberto", "Sandy"], horizontal=True)
    
    fecha = st.date_input("Fecha", datetime.date.today())
    botón_guardar = st.form_submit_button("Guardar Gasto")

if botón_guardar:
    if monto > 0 and descripcion:
        nuevo_gasto = {
            "fecha": str(fecha),
            "descripcion": descripcion,
            "monto": monto,
            "categoria": categoria,
            "pagado_por": pagado_por
        }
        supabase.table("gastos").insert(nuevo_gasto).execute()
        st.success("¡Gasto guardado correctamente!")
        st.cache_data.clear() 
        st.rerun()
    else:
        st.error("Por favor, introduce un monto válido y una descripción.")

st.divider()

# 4. Visualización e Historial
st.subheader("📊 Historial y Resumen")

datos = obtener_gastos()

if datos:
    df = pd.DataFrame(datos)
    df["fecha"] = pd.to_datetime(df["fecha"])
    
    # 📆 FILTRO DE FECHAS (Selector de Mes y Año)
    st.markdown("### 🔍 Filtrar por período")
    df['Mes_Año'] = df['fecha'].dt.strftime('%B %Y') # Ej: September 2026
    opciones_meses = ["Ver todo"] + list(df['Mes_Año'].unique())
    mes_seleccionado = st.selectbox("Selecciona un mes para analizar:", opciones_meses)
    
    # Aplicar filtro si no es "Ver todo"
    if mes_seleccionado != "Ver todo":
        df_filtrado = df[df['Mes_Año'] == mes_seleccionado].copy()
    else:
        df_filtrado = df.copy()
        
    # Mostrar tabla limpia filtrada
    df_mostrar = df_filtrado[["fecha", "descripcion", "monto", "categoria", "pagado_por"]].copy()
    df_mostrar["fecha"] = df_mostrar["fecha"].dt.strftime('%Y-%m-%d')
    st.dataframe(df_mostrar, use_container_width=True)
    
    # Cálculos matemáticos basados en el filtro
    total_gastado = df_filtrado["monto"].sum()
    gastos_roberto = df_filtrado[df_filtrado["pagado_por"] == "Roberto"]["monto"].sum()
    gastos_sandy = df_filtrado[df_filtrado["pagado_por"] == "Sandy"]["monto"].sum()
    
    # Métricas dinámicas
    st.metric(label=f"Total Gastado ({mes_seleccionado})", value=f"\${total_gastado:,.2f}")
    c1, c2 = st.columns(2)
    c1.metric(label="Aportado por Roberto", value=f"\${gastos_roberto:,.2f}")
    c2.metric(label="Aportado por Sandy", value=f"\${gastos_sandy:,.2f}")
        
    st.divider()
    
    # 📈 SECCIÓN DE GRÁFICAS DEL PERÍODO FILTRADO
    st.subheader("📈 Análisis de Tendencias Visuales")
    
    pestana_pastel, pestana_diaria, pestana_semanal, pestana_mensual = st.tabs([
        "🍕 Distribución", "🗓️ Diario", "📆 Semanal", "📅 Mensual"
    ])
    
    with pestana_pastel:
        st.markdown(f"**Porcentaje de gastos por categoría en {mes_seleccionado}:**")
        df_categoria = df_filtrado.groupby("categoria")["monto"].sum().reset_index()
        # Generamos la gráfica de dona interactiva nativa de Streamlit
        st.logo(image="", icon="🍕")
        
    with pestana_diaria:
        st.markdown("**Gasto acumulado por día:**")
        df_diario = df_filtrado.groupby("fecha")["monto"].sum().reset_index()
        st.line_chart(data=df_diario, x="fecha", y="monto", use_container_width=True)
        
    with pestana_semanal:
        st.markdown("**Gasto total por semana:**")
        df_semanal = df_filtrado.groupby(df_filtrado["fecha"].dt.to_period("W"))["monto"].sum().reset_index()
        df_semanal["fecha"] = df_semanal["fecha"].astype(str)
        st.bar_chart(data=df_semanal, x="fecha", y="monto", use_container_width=True)
        
    with pestana_mensual:
        st.markdown("**Gasto total por mes:**")
        df_mensual = df.groupby(df["fecha"].dt.to_period("M"))["monto"].sum().reset_index()
        df_mensual["fecha"] = df_mensual["fecha"].astype(str)
        st.bar_chart(data=df_mensual, x="fecha", y="monto", use_container_width=True)

else:
    st.info("Aún no hay gastos registrados. ¡Empiecen anotando el primero arriba!")
