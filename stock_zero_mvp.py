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
        st.error("El módulo de recetas no está disponible. Crea `modules/recipes.py`")

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN DE LA APP
# ============================================

st.set_page_config(
    page_title="Stock Zero",
    page_icon="Box",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SESSION STATE (PERSISTENCIA)
# ============================================

for key in [
    'uploaded_ventas_bytes', 'uploaded_stock_bytes',
    'df_ventas', 'df_stock',
    'df_ventas_trazabilidad', 'df_stock_trazabilidad',
    'df_resultados', 'inventario_df'
]:
    if key not in st.session_state:
        st.session_state[key] = None

if st.session_state.df_ventas_trazabilidad is None:
    st.session_state.df_ventas_trazabilidad = pd.DataFrame(columns=['fecha','producto','cantidad_vendida'])
if st.session_state.df_stock_trazabilidad is None:
    st.session_state.df_stock_trazabilidad = pd.DataFrame(columns=['fecha','producto','cantidad_recibida'])
if st.session_state.inventario_df is None:
    st.session_state.inventario_df = generar_inventario_base(None, use_example_data=True)

# ============================================
# EJEMPLOS DE DATOS
# ============================================

def generar_ejemplo_ventas():
    fechas = pd.date_range('2024-01-01','2024-01-31')
    datos = []
    prods = ['Café en Grano (Kg)','Leche Entera (Litros)','Pan Hamburguesa (Uni)']
    for f in fechas:
        for p in prods:
            datos.append({'fecha':f.strftime('%Y-%m-%d'),'producto':p,'cantidad_vendida':10+(hash(str(f)+p)%20)})
    return pd.DataFrame(datos)

def generar_ejemplo_stock():
    return pd.DataFrame([
        {'fecha':'2024-01-05','producto':'Café en Grano (Kg)','cantidad_recibida':50},
        {'fecha':'2024-01-12','producto':'Leche Entera (Litros)','cantidad_recibida':100},
        {'fecha':'2024-01-18','producto':'Pan Hamburguesa (Uni)','cantidad_recibida':200},
        {'fecha':'2024-01-25','producto':'Café en Grano (Kg)','cantidad_recibida':50},
    ])

def generar_ejemplo_ventas_ancho():
    fechas = pd.date_range('2024-01-01','2024-01-31')
    datos = []
    for f in fechas:
        fila = {'fecha':f.strftime('%Y-%m-%d')}
        fila['Café en Grano (Kg)'] = 10 + (hash(str(f)+'cafe')%15)
        fila['Leche Entera (Litros)'] = 15 + (hash(str(f)+'leche')%20)
        fila['Pan Hamburguesa (Uni)'] = 20 + (hash(str(f)+'pan')%25)
        datos.append(fila)
    return pd.DataFrame(datos)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.title("Stock Zero")
    st.markdown("### Sistema de Gestión de Inventario")
    st.markdown("---")

    opciones = ["Optimización de Inventario","Control de Inventario Básico"]
    if RECIPES_AVAILABLE:
        opciones.append("Recetas y Productos")
    pagina = st.radio("Navegación", opciones, label_visibility="collapsed")
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
    st.markdown("### Información")
    st.caption(datetime.now().strftime('%d/%m/%Y'))
    st.caption("Usuario: Demo")

    st.markdown("---")
    st.markdown("### Datos Cargados")
    if st.session_state.df_ventas is not None:
        st.success(f"Ventas: {len(st.session_state.df_ventas)} registros")
    else:
        st.warning("Ventas: No cargadas")
    if st.session_state.df_stock is not None:
        st.info(f"Stock: {len(st.session_state.df_stock)} entradas")
    else:
        st.info("Stock: No cargado")

    st.markdown("---")
    st.markdown("### Reset")
    if st.button("Borrar todos los datos", type="secondary"):
        for k in list(st.session_state.keys()):
            if k.startswith('uploaded_') or k.startswith('df_'):
                del st.session_state[k]
        st.success("Datos borrados")
        st.rerun()

# ============================================
# PÁGINA: OPTIMIZACIÓN
# ============================================

if pagina == "Optimización de Inventario":
    st.header("Optimización de Inventario")
    st.markdown("---")

    # --- GUÍA ---
    with st.expander("Guía de Formatos", expanded=False):
        st.markdown("### Formatos")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Ventas (Largo)")
            st.dataframe(generar_ejemplo_ventas().head(5), use_container_width=True, hide_index=True)
            st.download_button("Ejemplo Largo", generar_ejemplo_ventas().to_csv(index=False),
                               "ejemplo_ventas_largo.csv","text/csv",key="dl_largo")
            st.markdown("---")
            st.markdown("#### Ventas (Ancho)")
            st.dataframe(generar_ejemplo_ventas_ancho().head(5), use_container_width=True, hide_index=True)
            st.download_button("Ejemplo Ancho", generar_ejemplo_ventas_ancho().to_csv(index=False),
                               "ejemplo_ventas_ancho.csv","text/csv",key="dl_ancho")
        with c2:
            st.markdown("#### Entradas de Stock")
            st.dataframe(generar_ejemplo_stock(), use_container_width=True, hide_index=True)
            st.download_button("Ejemplo Stock", generar_ejemplo_stock().to_csv(index=False),
                               "ejemplo_stock.csv","text/csv",key="dl_stock")
        st.markdown("### Requisitos")
        st.markdown("- Fechas `YYYY-MM-DD`\n- Números positivos\n- UTF-8, separador `,`")

    # --- CARGA ---
    st.markdown("### 1. Sube archivos")
    cv, cs = st.columns(2)
    up_ventas = cv.file_uploader("Ventas (CSV)", type="csv", key="up_ventas")
    up_stock  = cs.file_uploader("Stock (CSV)", type="csv", key="up_stock")

    # VENTAS
    if up_ventas:
        st.session_state.uploaded_ventas_bytes = up_ventas.getvalue()
        try:
            raw = pd.read_csv(up_ventas)
            if 'producto' not in raw.columns and len(raw.columns)>2:
                df_ventas = raw.melt(id_vars='fecha',var_name='producto',value_name='cantidad_vendida')
            else:
                df_ventas = raw[['fecha','producto','cantidad_vendida']].copy()
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'],errors='coerce')
            df_ventas = df_ventas.dropna(subset='fecha')
            df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'],errors='coerce').fillna(0)
            st.session_state.df_ventas = df_ventas
            st.session_state.df_ventas_trazabilidad = df_ventas.copy()
            st.success("Ventas cargadas")
        except Exception as e:
            st.error(f"Error: {e}")
    elif st.session_state.uploaded_ventas_bytes:
        try:
            df_ventas = pd.read_csv(io.BytesIO(st.session_state.uploaded_ventas_bytes))
            if 'producto' not in df_ventas.columns and len(df_ventas.columns)>2:
                df_ventas = df_ventas.melt(id_vars='fecha',var_name='producto',value_name='cantidad_vendida')
            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'],errors='coerce')
            df_ventas = df_ventas.dropna(subset='fecha')
            df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'],errors='coerce').fillna(0)
            st.session_state.df_ventas = df_ventas
            st.session_state.df_ventas_trazabilidad = df_ventas.copy()
        except:
            pass

    # STOCK
    if up_stock:
        st.session_state.uploaded_stock_bytes = up_stock.getvalue()
        try:
            raw = pd.read_csv(up_stock)
            cols = {c.strip().lower():c for c in raw.columns}
            req = ['fecha','producto','cantidad_recibida']
            if all(r in cols for r in req):
                df_stock = raw.rename(columns={cols[r]:r for r in req})[req].copy()
                df_stock['fecha'] = pd.to_datetime(df_stock['fecha'],errors='coerce')
                df_stock = df_stock.dropna(subset='fecha')
                df_stock['fecha'] = df_stock['fecha'].dt.normalize()
                df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'],errors='coerce').fillna(0)
                st.session_state.df_stock = df_stock
                st.session_state.df_stock_trazabilidad = df_stock.copy()
                st.success("Stock cargado")
            else:
                st.warning("Columnas no válidas")
        except Exception as e:
            st.error(f"Error: {e}")
    elif st.session_state.uploaded_stock_bytes:
        try:
            df_stock = pd.read_csv(io.BytesIO(st.session_state.uploaded_stock_bytes))
            cols = {c.strip().lower():c for c in df_stock.columns}
            req = ['fecha','producto','cantidad_recibida']
            if all(r in cols for r in req):
                df_stock = df_stock.rename(columns={cols[r]:r for r in req})[req].copy()
                df_stock['fecha'] = pd.to_datetime(df_stock['fecha'],errors='coerce')
                df_stock = df_stock.dropna(subset='fecha')
                df_stock['fecha'] = df_stock['fecha'].dt.normalize()
                df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'],errors='coerce').fillna(0)
                st.session_state.df_stock = df_stock
                st.session_state.df_stock_trazabilidad = df_stock.copy()
        except:
            pass

    # --- PROCESO ---
    if st.session_state.df_ventas is not None:
        df_ventas = st.session_state.df_ventas

        # Reiniciar inventario si es necesario
        if st.session_state.inventario_df is not None:
            example_prods = {'Café en Grano (Kg)','Leche Entera (Litros)','Pan Hamburguesa (Uni)'}
            if example_prods.issubset(set(st.session_state.inventario_df['Producto'])):
                st.session_state.inventario_df = generar_inventario_base(df_ventas, use_example_data=False)
        else:
            st.session_state.inventario_df = generar_inventario_base(df_ventas)

        st.markdown("### 2. Resumen")
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Productos", df_ventas['producto'].nunique())
        with c2: st.metric("Registros", len(df_ventas))
        with c3: st.metric("Días", (df_ventas['fecha'].max()-df_ventas['fecha'].min()).days+1)
        with c4: st.metric("Formato", "Ancho" if up_ventas and 'producto' not in pd.read_csv(up_ventas).columns else "Largo")
        st.markdown(f"**Productos:** {', '.join(sorted(df_ventas['producto'].unique()))}")

        if len(df_ventas) < 30:
            st.warning("Menos de 30 registros → pronóstico menos fiable")

        st.markdown("### 3. Calcular")
        if st.button("Calcular para TODOS", type="primary", use_container_width=True):
            with st.spinner("Analizando..."):
                res = procesar_multiple_productos(df_ventas, lead_time, stock_seguridad, frecuencia)
            st.session_state.df_resultados = res
            st.rerun()

        if st.session_state.df_resultados is not None:
            df_res = st.session_state.df_resultados
            ok = df_res[df_res['error'].isnull()].sort_values('cantidad_a_ordenar', ascending=False)

            st.markdown("---")
            st.markdown("## Resultados")
            if not ok.empty:
                st.success(f"{len(ok)} productos OK")
                c1,c2 = st.columns(2)
                with c1: st.metric("PR total", f"{ok['punto_reorden'].sum():.0f}")
                with c2: st.metric("Ordenar total", f"{ok['cantidad_a_ordenar'].sum():.0f}")

                # Export Excel
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                    ok[['producto','clasificacion_abc','punto_reorden','cantidad_a_ordenar']].to_excel(writer, sheet_name='Recomendaciones', index=False)
                    ok.to_excel(writer, sheet_name='Completo', index=False)
                buf.seek(0)
                st.download_button(
                    "Descargar Excel",
                    buf,
                    f"stock_zero_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_excel"
                )

                st.markdown("### ABC")
                disp = ok[['producto','clasificacion_abc','punto_reorden','cantidad_a_ordenar']].copy()
                disp.columns = ['Producto','ABC','PR','Ordenar']
                disp['PR'] = disp['PR'].apply(lambda x:f"{x:.0f}")
                disp['Ordenar'] = disp['Ordenar'].apply(lambda x:f"{x:.0f}")
                st.dataframe(disp, use_container_width=True, hide_index=True)

                st.markdown("### Trazabilidad")
                prod = st.selectbox("Producto", ok['producto'].tolist(), key="sel_traz")
                if prod:
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
                        fig = crear_grafico_trazabilidad_total(traz, r, lead_time)
                        st.pyplot(fig)

                st.markdown("### Tendencias")
                fig = crear_grafico_comparativo(df_res.to_dict('records'))
                st.pyplot(fig)
            else:
                st.info("Sin datos suficientes")
        else:
            st.info("Pulsa Calcular")
    else:
        st.info("Sube ventas para empezar")

# ============================================
# OTRAS PÁGINAS
# ============================================

elif pagina == "Control de Inventario Básico":
    inventario_basico_app()  # <-- este módulo debe guardar `st.session_state.inventario_df = df_editado`

elif pagina == "Recetas y Productos":
    if RECIPES_AVAILABLE:
        recetas_app()
    else:
        st.error("Módulo recetas no encontrado")
