# stock_zero_mvp_centered.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import warnings
import os

# --- SUPABASE ---
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

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
        st.error("El módulo de recetas no está disponible.")

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Stock Zero",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="collapsed"
)

lead_time = 7
stock_seguridad = 3
frecuencia = 7

# ============================================
# TÍTULO Y BOTÓN DE SUBIR (SIEMPRE VISIBLE)
# ============================================
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; color: #4361EE; margin-bottom: 0.5rem;'>
              StockZero
        </h1>
        <p style='font-size: 1.2rem; color: #666; margin-top: 0;'>
            Sistema de Gestión de Inventario
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Botón en esquina superior derecha
col_left, col_right = st.columns([8, 2])
with col_right:
    # Botón de subir archivos
    if st.button("Subir Archivos", type="primary", use_container_width=True):
        st.session_state.show_upload_modal = True  # Siempre True al hacer clic

# ============================================
# MODAL DE SUBIDA CON st.dialog
# ============================================
@st.dialog("Subir Archivos de Datos", width="large")
def upload_modal():
    st.markdown("### Guía de Formatos y Ejemplos")

    with st.expander("Formatos Aceptados", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Ventas (Requerido)")
            st.markdown("**Formato Largo (Recomendado)**")
            ejemplo_largo = pd.DataFrame({
                'fecha': ['2025-01-01', '2025-01-01'],
                'producto': ['Café en Grano (Kg)', 'Leche Entera (Litros)'],
                'cantidad_vendida': [7, 14]
            })
            st.dataframe(ejemplo_largo, use_container_width=True, hide_index=True)
            st.download_button(
                "Descargar Ejemplo Largo",
                ejemplo_largo.to_csv(index=False),
                "ejemplo_ventas_largo.csv",
                "text/csv"
            )

            st.markdown("**Formato Ancho**")
            ejemplo_ancho = pd.DataFrame({
                'fecha': ['2025-01-01'],
                'Café en Grano (Kg)': [7],
                'Leche Entera (Litros)': [14]
            })
            st.dataframe(ejemplo_ancho, use_container_width=True, hide_index=True)
            st.download_button(
                "Descargar Ejemplo Ancho",
                ejemplo_ancho.to_csv(index=False),
                "ejemplo_ventas_ancho.csv",
                "text/csv"
            )

        with col2:
            st.markdown("#### Entradas de Stock (Opcional)")
            ejemplo_stock = pd.DataFrame({
                'fecha': ['2024-12-31'],
                'producto': ['Café en Grano (Kg)'],
                'cantidad_recibida': [120]
            })
            st.dataframe(ejemplo_stock, use_container_width=True, hide_index=True)
            st.download_button(
                "Descargar Ejemplo Stock",
                ejemplo_stock.to_csv(index=False),
                "ejemplo_stock.csv",
                "text/csv"
            )

    st.markdown("---")
    st.markdown("### Subir Archivos")

    uploaded_ventas = st.file_uploader("Ventas (CSV)", type="csv", key="modal_ventas")
    uploaded_stock = st.file_uploader("Stock (Opcional, CSV)", type="csv", key="modal_stock")

    if st.button("Cerrar", type="secondary"):
        st.session_state.show_upload_modal = False
        st.rerun()

    # Procesar Ventas
    if uploaded_ventas:
        try:
            df_raw = pd.read_csv(uploaded_ventas)
            if 'producto' not in df_raw.columns and len(df_raw.columns) > 2:
                df_ventas = df_raw.melt(id_vars='fecha', var_name='producto', value_name='cantidad_vendida')
            else:
                df_ventas = df_raw[['fecha', 'producto', 'cantidad_vendida']].copy()

            df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
            df_ventas = df_ventas.dropna(subset=['fecha'])
            df_ventas['cantidad_vendida'] = pd.to_numeric(df_ventas['cantidad_vendida'], errors='coerce').fillna(0)

            st.session_state.df_ventas_trazabilidad = df_ventas
            st.success("Ventas cargadas correctamente.")

            # Supabase
            if SUPABASE_AVAILABLE and os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
                supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
                supabase.table("ventas").insert(df_ventas.to_dict('records')).execute()
                st.info("Guardado en Supabase.")

        except Exception as e:
            st.error(f"Error: {e}")

    # Procesar Stock
    if uploaded_stock:
        try:
            df_stock = pd.read_csv(uploaded_stock)
            df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce')
            df_stock = df_stock.dropna(subset=['fecha'])
            df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'], errors='coerce').fillna(0)
            st.session_state.df_stock_trazabilidad = df_stock
            st.success("Stock cargado.")

            if SUPABASE_AVAILABLE and os.getenv("SUPABASE_URL"):
                supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
                supabase.table("stock").insert(df_stock.to_dict('records')).execute()

        except Exception as e:
            st.error(f"Error: {e}")

    if uploaded_ventas or uploaded_stock:
        if st.button("Listo - Cerrar", type="primary"):
            st.session_state.show_upload_modal = False
            st.rerun()

# Mostrar modal si está activo
if st.session_state.get("show_upload_modal", False):
    upload_modal()

# ============================================
# NAVEGACIÓN
# ============================================
st.markdown("---")
st.markdown("## Secciones")

cols = st.columns(5)
with cols[1]:
    if st.button("Dashboard", use_container_width=True, type="primary"):
        st.session_state.pagina_actual = "Dashboard Inteligente"
with cols[2]:
    if st.button("Optimización", use_container_width=True):
        st.session_state.pagina_actual = "Optimización de Inventario"
with cols[3]:
    if st.button("Control Inventario", use_container_width=True):
        st.session_state.pagina_actual = "Control de Inventario Básico"

# ============================================
# INICIALIZAR SESSION STATE
# ============================================
if 'df_ventas_trazabilidad' not in st.session_state:
    st.session_state.df_ventas_trazabilidad = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_vendida'])
if 'df_stock_trazabilidad' not in st.session_state:
    st.session_state.df_stock_trazabilidad = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida'])
if 'inventario_df' not in st.session_state:
    st.session_state.inventario_df = generar_inventario_base(use_example_data=True)

# ============================================
# PÁGINAS
# ============================================
st.markdown("---")
pagina = st.session_state.get("pagina_actual", "Dashboard Inteligente")

if pagina == "Dashboard Inteligente":
    try:
        from pages._0_Dashboard_Enhanced import dashboard_enhanced_app
        dashboard_enhanced_app()
    except Exception as e:
        st.error(f"Error: {e}")

elif pagina == "Optimización de Inventario":
    st.header("Optimización de Inventario")
    if not st.session_state.df_ventas_trazabilidad.empty:
        st.success("Datos listos. ¡Calcula!")
        # Aquí va tu código de optimización...
        # Usa: st.session_state.df_ventas_trazabilidad
    else:
        st.info("Sube archivos desde el botón superior.")

elif pagina == "Control de Inventario Básico":
    inventario_basico_app()
