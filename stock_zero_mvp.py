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

try:
    from modules.recipes import recetas_app
    RECIPES_AVAILABLE = True
except ImportError:
    RECIPES_AVAILABLE = False
    def recetas_app():
        st.error("Módulo `recipes.py` no encontrado")

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN
# ============================================

st.set_page_config(page_title="Stock Zero", page_icon="Box", layout="wide", initial_sidebar_state="expanded")

# ============================================
# SESSION STATE (GLOBAL, PERSISTENTE)
# ============================================

DEFAULTS = {
    'uploaded_ventas_bytes': None,
    'uploaded_stock_bytes': None,
    'df_ventas': None,
    'df_stock': None,
    'df_ventas_trazabilidad': pd.DataFrame(columns=['fecha','producto','cantidad_vendida']),
    'df_stock_trazabilidad': pd.DataFrame(columns=['fecha','producto','cantidad_recibida']),
    'df_resultados': None,
    'inventario_df': generar_inventario_base(None, use_example_data=True)
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================
# EJEMPLOS
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
# FUNCIÓN REUTILIZABLE: PROCESAR CSV
# ============================================

def procesar_csv(bytes_data, tipo):
    """tipo: 'ventas' o 'stock'"""
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
    else:  # stock
        cols = {c.strip().lower():c for c in df.columns}
        req = ['fecha','producto','cantidad_recibida']
        if not all(r in cols for r in req):
            return None
        df = df.rename(columns={cols[r]:r for r in req})[req].copy()
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset='fecha').copy()
        df['fecha'] = df['fecha'].dt.normalize()
        df['cantidad_recibida'] = pd.to_numeric(df['cantidad_recibida'], errors='coerce').fillna(0)
        return df

# ============================================
# SIDEBAR (UNA VEZ)
# ============================================

with st.sidebar:
    st.title("Stock Zero")
    st.markdown("### Gestión de Inventario")
    st.markdown("---")

    opciones = ["Optimización de Inventario","Control de Inventario Básico"]
    if RECIPES_AVAILABLE:
        opciones.append("Recetas y Productos")
    pagina = st.radio("Navegar", opciones, label_visibility="collapsed")

    st.markdown("---")
    if pagina == "Optimización de Inventario":
        st.markdown("### Configuración")
        lead_time = st.slider("Lead Time (días)",1,30,7)
        stock_seguridad = st.slider("Stock de Seguridad (días)",1,10,3)
        frecuencia = st.selectbox("Estacionalidad",[7,14,30],index=0,
                                 format_func=lambda x:f"{x} días ({'Semanal' if x==7 else 'Mensual' if x==30 else 'Quincenal'})")
    else:
        lead_time, stock_seguridad, frecuencia = 7, 3, 7

    st.markdown("---")
    st.markdown("### Estado")
    st.caption(datetime.now().strftime('%d/%m/%Y'))
    st.caption("Usuario: Demo")

    st.markdown("### Datos")
    if st.session_state.df_ventas is not None:
        st.success(f"Ventas: {len(st.session_state.df_ventas)}")
    else:
        st.warning("Ventas: No")
    if st.session_state.df_stock is not None:
        st.info(f"Stock: {len(st.session_state.df_stock)}")
    else:
        st.info("Stock: No")

    st.markdown("---")
    if st.button("Resetear todo", type="secondary"):
        for k in list(st.session_state.keys()):
            if k.startswith('uploaded_') or k.startswith('df_'):
                del st.session_state[k]
        st.success("Datos eliminados")
        st.rerun()

# ============================================
# CARGA DE ARCHIVOS (UNA VEZ, GLOBAL)
# ============================================

if pagina == "Optimización de Inventario":  # Solo se muestra aquí, pero se guarda global
    with st.expander("Guía de Formatos", expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("#### Ventas (Largo)")
            st.dataframe(ejemplo_ventas_largo().head(5), use_container_width=True, hide_index=True)
            st.download_button("Ej. Largo", ejemplo_ventas_largo().to_csv(index=False), "ventas_largo.csv", "text/csv")
            st.markdown("---")
            st.markdown("#### Ventas (Ancho)")
            st.dataframe(ejemplo_ventas_ancho().head(5), use_container_width=True, hide_index=True)
            st.download_button("Ej. Ancho", ejemplo_ventas_ancho().to_csv(index=False), "ventas_ancho.csv", "text/csv")
        with c2:
            st.markdown("#### Stock")
            st.dataframe(ejemplo_stock(), use_container_width=True, hide_index=True)
            st.download_button("Ej. Stock", ejemplo_stock().to_csv(index=False), "stock.csv", "text/csv")
        st.markdown("### Requisitos: YYYY-MM-DD, UTF-8, coma")

    st.markdown("### 1. Carga de archivos (persistente)")
    cv, cs = st.columns(2)
    up_ventas = cv.file_uploader("Ventas CSV", type="csv", key="upv")
    up_stock = cs.file_uploader("Stock CSV", type="csv", key="ups")

    # VENTAS
    if up_ventas:
        st.session_state.uploaded_ventas_bytes = up_ventas.getvalue()
        df = procesar_csv(st.session_state.uploaded_ventas_bytes, 'ventas')
        if df is not None:
            st.session_state.df_ventas = df
            st.session_state.df_ventas_trazabilidad = df.copy()
            st.success("Ventas OK")
        else:
            st.error("Formato ventas inválido")
    elif st.session_state.uploaded_ventas_bytes:
        df = procesar_csv(st.session_state.uploaded_ventas_bytes, 'ventas')
        if df is not None:
            st.session_state.df_ventas = df
            st.session_state.df_ventas_trazabilidad = df.copy()

    # STOCK
    if up_stock:
        st.session_state.uploaded_stock_bytes = up_stock.getvalue()
        df = procesar_csv(st.session_state.uploaded_stock_bytes, 'stock')
        if df is not None:
            st.session_state.df_stock = df
            st.session_state.df_stock_trazabilidad = df.copy()
            st.success("Stock OK")
        else:
            st.warning("Columnas stock faltan")
    elif st.session_state.uploaded_stock_bytes:
        df = procesar_csv(st.session_state.uploaded_stock_bytes, 'stock')
        if df is not None:
            st.session_state.df_stock = df
            st.session_state.df_stock_trazabilidad = df.copy()

# ============================================
# PÁGINAS
# ============================================

if pagina == "Optimización de Inventario":
    if st.session_state.df_ventas is None:
        st.info("Sube ventas para continuar")
        st.stop()

    df_ventas = st.session_state.df_ventas

    # Actualizar inventario base
    if st.session_state.inventario_df is not None:
        example = {'Café en Grano (Kg)','Leche Entera (Litros)','Pan Hamburguesa (Uni)'}
        if example.issubset(set(st.session_state.inventario_df['Producto'])):
            st.session_state.inventario_df = generar_inventario_base(df_ventas, use_example_data=False)
    else:
        st.session_state.inventario_df = generar_inventario_base(df_ventas)

    st.markdown("### 2. Resumen")
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Productos", df_ventas['producto'].nunique())
    with c2: st.metric("Registros", len(df_ventas))
    with c3: st.metric("Días", (df_ventas['fecha'].max()-df_ventas['fecha'].min()).days+1)
    if len(df_ventas) < 30:
        st.warning("Menos de 30 días → pronóstico débil")

    st.markdown("### 3. Calcular")
    if st.button("Calcular todo", type="primary", use_container_width=True):
        with st.spinner("Procesando..."):
            res = procesar_multiple_productos(df_ventas, lead_time, stock_seguridad, frecuencia)
        st.session_state.df_resultados = res
        st.rerun()

    if st.session_state.df_resultados is not None:
        ok = st.session_state.df_resultados[st.session_state.df_resultados['error'].isnull()]
        ok = ok.sort_values('cantidad_a_ordenar', ascending=False)

        st.markdown("---")
        st.markdown("## Resultados")
        if not ok.empty:
            st.success(f"{len(ok)} productos")
            c1,c2 = st.columns(2)
            with c1: st.metric("PR total", f"{ok['punto_reorden'].sum():.0f}")
            with c2: st.metric("Ordenar", f"{ok['cantidad_a_ordenar'].sum():.0f}")

            # Excel
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                ok[['producto','clasificacion_abc','punto_reorden','cantidad_a_ordenar']].to_excel(w, 'Recomendaciones', index=False)
                ok.to_excel(w, 'Completo', index=False)
            buf.seek(0)
            st.download_button("Descargar Excel", buf, f"stock_zero_{datetime.now():%Y%m%d}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            st.markdown("### ABC")
            disp = ok[['producto','clasificacion_abc','punto_reorden','cantidad_a_ordenar']].copy()
            disp.columns = ['Producto','ABC','PR','Ordenar']
            st.dataframe(disp, use_container_width=True, hide_index=True)

            st.markdown("### Trazabilidad")
            prod = st.selectbox("Producto", ok['producto'].tolist())
            r = ok[ok['producto']==prod].iloc[0].to_dict()
            stock_act = 0.0
            if st.session_state.inventario_df is not None:
                row = st.session_state.inventario_df[st.session_state.inventario_df['Producto']==prod]
                if not row.empty:
                    stock_act = float(row['Stock Actual'].iloc[0])
            st.info(f"Stock actual: **{stock_act:.2f}**")

            traz = calcular_trazabilidad_inventario(
                st.session_state.df_ventas_trazabilidad,
                st.session_state.df_stock_trazabilidad,
                prod, stock_act, r['punto_reorden'],
                r['cantidad_a_ordenar'], r['pronostico_diario_promedio'], lead_time
            )
            if traz is not None and not traz.empty:
                st.pyplot(crear_grafico_trazabilidad_total(traz, r, lead_time))

            st.markdown("### Tendencias")
            st.pyplot(crear_grafico_comparativo(ok.to_dict('records')))
        else:
            st.info("Sin resultados válidos")

elif pagina == "Control de Inventario Básico":
    inventario_basico_app()  # debe hacer: st.session_state.inventario_df = df_editado

elif pagina == "Recetas y Productos":
    if RECIPES_AVAILABLE:
        recetas_app()
    else:
        st.error("Módulo recetas no disponible")
