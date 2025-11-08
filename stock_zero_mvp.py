# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import warnings

# --- MÓDULOS ---
from modules.core_analysis import procesar_multiple_productos
from modules.trazability import calcular_trazabilidad_inventario
from modules.components import (
    inventario_basico_app,
    crear_grafico_comparativo,
    crear_grafico_trazabilidad_total,
    generar_inventario_base
)

# --- Recetas (opcional) ---
try:
    from modules.recipes import recetas_app
    RECIPES_AVAILABLE = True
except ImportError:
    RECIPES_AVAILABLE = False
    def recetas_app():
        st.error("Módulo `recipes.py` no encontrado")

# --- Analytics (NUEVO) ---
try:
    from modules.analytics import analytics_app
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    def analytics_app():
        st.error("Módulo `analytics.py` no encontrado")

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN GLOBAL
# ============================================
st.set_page_config(
    page_title="Stock Zero MVP",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': '# Stock Zero MVP\nGestión inteligente de inventario.'
    }
)

# ============================================
# SESSION STATE (PERSISTENTE)
# ============================================
DEFAULTS = {
    'uploaded_ventas_bytes': None,
    'uploaded_stock_bytes': None,
    'df_ventas': None,
    'df_stock': None,
    'df_ventas_trazabilidad': pd.DataFrame(columns=['fecha','producto','cantidad_vendida']),
    'df_stock_trazabilidad': pd.DataFrame(columns=['fecha','producto','cantidad_recibida']),
    'df_resultados': None,
    'inventario_df': None
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================
# EJEMPLOS (solo para guía)
# ============================================
@st.cache_data
def ejemplo_ventas_largo():
    fechas = pd.date_range('2024-01-01','2024-01-31')
    prods = ['Café en Grano (Kg)','Leche Entera (Litros)','Pan Hamburguesa (Uni)']
    data = [{'fecha':f.strftime('%Y-%m-%d'),'producto':p,'cantidad_vendida':10+(hash(str(f)+p)%20)}
            for f in fechas for p in prods]
    return pd.DataFrame(data)

@st.cache_data
def ejemplo_stock():
    return pd.DataFrame([
        {'fecha':'2024-01-05','producto':'Café en Grano (Kg)','cantidad_recibida':50},
        {'fecha':'2024-01-12','producto':'Leche Entera (Litros)','cantidad_recibida':100},
        {'fecha':'2024-01-18','producto':'Pan Hamburguesa (Uni)','cantidad_recibida':200},
        {'fecha':'2024-01-25','producto':'Café en Grano (Kg)','cantidad_recibida':50},
    ])

@st.cache_data
def ejemplo_ventas_ancho():
    fechas = pd.date_range('2024-01-01','2024-01-31')
    data = []
    for f in fechas:
        r = {'fecha':f.strftime('%Y-%m-%d')}
        r['Café en Grano (Kg)'] = 10 + (hash(str(f)+'cafe')%15)
        r['Leche Entera (Litros)'] = 15 + (hash(str(f)+'leche')%20)
        r['Pan Hamburguesa (Uni)'] = 20 + (hash(str(f)+'pan')%25)
        data.append(r)
    return pd.DataFrame(data)

# ============================================
# PROCESAR CSV
# ============================================
def procesar_csv(bytes_data, tipo):
    df = pd.read_csv(io.BytesIO(bytes_data))
    if tipo == 'ventas':
        if 'producto' not in df.columns and len(df.columns) > 2:
            df = df.melt(id_vars='fecha', var_name='producto', value_name='cantidad_vendida')
        else:
            df = df[['fecha','producto','cantidad_vendida']].copy()
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset='fecha').copy()
        df['fecha'] = df['fecha'].dt.normalize()
        df['cantidad_vendida'] = pd.to_numeric(df['cantidad_vendida'], errors='coerce').fillna(0)
        return df
    else:
        cols = {c.strip().lower():c for c in df.columns}
        req = ['fecha','producto','cantidad_recibida']
        # ← AQUÍ ESTÁ LA CORRECCIÓN: "all" en minúscula, sin caracteres raros
        if not all(r in cols for r in req):
            return None
        df = df.rename(columns={cols[r]:r for r in req})[req].copy()
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset='fecha').copy()
        df['fecha'] = df['fecha'].dt.normalize()
        df['cantidad_recibida'] = pd.to_numeric(df['cantidad_recibida'], errors='coerce').fillna(0)
        return df

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.title("📦 Stock Zero")
    st.markdown("### Gestión de Inventario")
    st.markdown("---")
    opciones = ["🚀 Optimización de Inventario", "🛒 Control de Inventario Básico", "📊 Análisis"]
    if RECIPES_AVAILABLE:
        opciones.append("👨‍🍳 Recetas y Productos")
    pagina = st.radio("Navegar", opciones, label_visibility="collapsed")
    st.markdown("---")
    
    # Configuración solo visible en Optimización
    if pagina == "🚀 Optimización de Inventario":
        st.markdown("### ⚙️ Configuración")
        lead_time = st.slider("Lead Time (días)", 1, 30, 7)
        stock_seguridad = st.slider("Stock de Seguridad (días)", 1, 10, 3)
        frecuencia = st.selectbox(
            "Estacionalidad", [7, 14, 30], index=0,
            format_func=lambda x: f"{x} días ({'Semanal' if x==7 else 'Quincenal' if x==14 else 'Mensual'})"
        )
    else:
        lead_time, stock_seguridad, frecuencia = 7, 3, 7  # Valores por defecto si no se usan

    st.markdown("---")
    st.markdown("### ℹ️ Estado")
    st.caption(datetime.now().strftime('%d/%m/%Y'))
    st.caption("Usuario: Demo")
    st.markdown("### 📊 Datos")
    if st.session_state.df_ventas is not None:
        st.success(f"Ventas: {len(st.session_state.df_ventas)} registros")
    else:
        st.warning("Ventas: No cargadas")
    if st.session_state.df_stock is not None:
        st.info(f"Stock: {len(st.session_state.df_stock)} entradas")
    else:
        st.info("Stock: No cargado")
    st.markdown("---")
    if st.button("🔄 Resetear todo", type="secondary"):
        for k in list(st.session_state.keys()):
            if k.startswith('uploaded_') or k.startswith('df_'):
                del st.session_state[k]
        st.success("✅ Datos eliminados")
        st.rerun()

# ============================================
# CARGA DE ARCHIVOS (GLOBAL)
# ============================================
if pagina in ["🚀 Optimización de Inventario", "📊 Análisis"]:
    with st.expander("📘 Guía de Formatos", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📈 Ventas (Largo)")
            st.dataframe(ejemplo_ventas_largo().head(5), use_container_width=True, hide_index=True)
            st.download_button("⬇️ Ej. Largo", ejemplo_ventas_largo().to_csv(index=False), "ventas_largo.csv", "text/csv")
            st.markdown("#### 📊 Ventas (Ancho)")
            st.dataframe(ejemplo_ventas_ancho().head(5), use_container_width=True, hide_index=True)
            st.download_button("⬇️ Ej. Ancho", ejemplo_ventas_ancho().to_csv(index=False), "ventas_ancho.csv", "text/csv")
        with c2:
            st.markdown("#### 📦 Stock")
            st.dataframe(ejemplo_stock(), use_container_width=True, hide_index=True)
            st.download_button("⬇️ Ej. Stock", ejemplo_stock().to_csv(index=False), "stock.csv", "text/csv")
        st.markdown("### ✅ Formato: YYYY-MM-DD, UTF-8, coma")

    st.markdown("### 1️⃣ Carga de archivos")
    cv, cs = st.columns(2)
    up_ventas = cv.file_uploader("📈 Ventas CSV", type="csv", key="upv")
    up_stock = cs.file_uploader("📦 Stock CSV", type="csv", key="ups")

    # --- VENTAS ---
    if up_ventas:
        st.session_state.uploaded_ventas_bytes = up_ventas.getvalue()
        df = procesar_csv(st.session_state.uploaded_ventas_bytes, 'ventas')
        if df is not None:
            st.session_state.df_ventas = df
            st.session_state.df_ventas_trazabilidad = df.copy()
            st.success("✅ Ventas cargadas correctamente")
        else:
            st.error("❌ Formato de ventas inválido")
    elif st.session_state.uploaded_ventas_bytes:
        df = procesar_csv(st.session_state.uploaded_ventas_bytes, 'ventas')
        if df is not None:
            st.session_state.df_ventas = df
            st.session_state.df_ventas_trazabilidad = df.copy()

    # --- STOCK ---
    if up_stock:
        st.session_state.uploaded_stock_bytes = up_stock.getvalue()
        df = procesar_csv(st.session_state.uploaded_stock_bytes, 'stock')
        if df is not None:
            st.session_state.df_stock = df
            st.session_state.df_stock_trazabilidad = df.copy()
            st.success("✅ Stock cargado correctamente")
        else:
            st.warning("⚠️ Faltan columnas en stock")
    elif st.session_state.uploaded_stock_bytes:
        df = procesar_csv(st.session_state.uploaded_stock_bytes, 'stock')
        if df is not None:
            st.session_state.df_stock = df
            st.session_state.df_stock_trazabilidad = df.copy()

# ============================================
# PÁGINAS
# ============================================

# === OPTIMIZACIÓN DE INVENTARIO ===
if pagina == "🚀 Optimización de Inventario":
    if st.session_state.df_ventas is None:
        st.info("👆 Sube tus datos de ventas para continuar")
        st.stop()
    df_ventas = st.session_state.df_ventas

    # === REGENERAR INVENTARIO CON DATOS REALES ===
    st.session_state.inventario_df = generar_inventario_base(df_ventas, use_example_data=False)

    st.markdown("### 2️⃣ Resumen de Datos")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📦 Productos", df_ventas['producto'].nunique())
    with c2: st.metric("📊 Registros", len(df_ventas))
    with c3: st.metric("📅 Días", (df_ventas['fecha'].max() - df_ventas['fecha'].min()).days + 1)
    if len(df_ventas) < 30:
        st.warning("⚠️ Menos de 30 días → pronóstico menos preciso")

    st.markdown("### 3️⃣ Calcular Inventario Óptimo")
    if st.button("🚀 Calcular para TODOS los productos", type="primary", use_container_width=True):
        with st.spinner("Analizando productos..."):
            res = procesar_multiple_productos(df_ventas, lead_time, stock_seguridad, frecuencia)
        st.session_state.df_resultados = res
        st.rerun()

    # === RESULTADOS CON CONFIGURACIÓN MOSTRADA ===
    if st.session_state.df_resultados is not None:
        ok = st.session_state.df_resultados[st.session_state.df_resultados['error'].isnull()]
        ok = ok.sort_values('cantidad_a_ordenar', ascending=False)
        st.markdown("---")
        st.markdown("## 📊 Resultados del Análisis")

        # ← AQUÍ ESTÁ EL CAPTION CON PARÁMETROS (como pediste)
        st.caption(
            f"⚙️ Configuración aplicada: "
            f"**Lead Time** = {lead_time} días | "
            f"**Stock de Seguridad** = {stock_seguridad} días | "
            f"**Estacionalidad** = {frecuencia} días"
        )

        if not ok.empty:
            st.success(f"✅ Se analizaron exitosamente {len(ok)} productos")
            c1, c2 = st.columns(2)
            with c1: st.metric("🎯 Total Punto de Reorden", f"{ok['punto_reorden'].sum():.0f} unidades")
            with c2: st.metric("📦 Total a Ordenar", f"{ok['cantidad_a_ordenar'].sum():.0f} unidades")

            # Descarga Excel
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                ok[['producto','clasificacion_abc','punto_reorden','cantidad_a_ordenar']].to_excel(w, 'Recomendaciones', index=False)
                ok.to_excel(w, 'Completo', index=False)
            buf.seek(0)
            st.download_button(
                "⬇️ Descargar Excel", buf,
                f"stock_zero_{datetime.now():%Y%m%d}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.markdown("### 📋 Recomendaciones y Clasificación ABC")
            disp = ok[['producto','clasificacion_abc','punto_reorden','cantidad_a_ordenar']].copy()
            disp.columns = ['Producto','ABC','Punto de Reorden','Cantidad a Ordenar']
            st.dataframe(disp, use_container_width=True, hide_index=True)

            st.markdown("### 📈 Trazabilidad de Inventario")
            prod = st.selectbox("Selecciona un producto:", ok['producto'].tolist())
            r = ok[ok['producto']==prod].iloc[0].to_dict()
            stock_act = 0.0
            if st.session_state.inventario_df is not None:
                row = st.session_state.inventario_df[st.session_state.inventario_df['Producto']==prod]
                if not row.empty:
                    stock_act = float(row['Stock Actual'].iloc[0])
            st.info(f"💡 Stock actual: **{stock_act:.2f}** unidades (de Control Básico)")

            traz = calcular_trazabilidad_inventario(
                st.session_state.df_ventas_trazabilidad,
                st.session_state.df_stock_trazabilidad,
                prod, stock_act, r['punto_reorden'],
                r['cantidad_a_ordenar'], r['pronostico_diario_promedio'], lead_time
            )
            if traz is not None and not traz.empty:
                st.pyplot(crear_grafico_trazabilidad_total(traz, r, lead_time))

            st.markdown("### 📊 Tendencias de Ventas")
            st.pyplot(crear_grafico_comparativo(ok.to_dict('records')))
        else:
            st.info("ℹ️ No se pudo calcular para ningún producto. Verifica los datos.")

# === CONTROL DE INVENTARIO BÁSICO ===
elif pagina == "🛒 Control de Inventario Básico":
    inventario_basico_app()

# === ANÁLISIS ===
elif pagina == "📊 Análisis":
    if ANALYTICS_AVAILABLE:
        analytics_app()
    else:
        st.error("Módulo `analytics.py` no encontrado")

# === RECETAS ===
elif pagina == "👨‍🍳 Recetas y Productos":
    if RECIPES_AVAILABLE:
        recetas_app()
    else:
        st.error("Módulo recetas no disponible")
