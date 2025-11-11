# stock_zero_mvp_centered.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import warnings
import os
from supabase import create_client, Client

# ============================================
# 1. SUPABASE CLIENT & SECRETS
# ============================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["anon_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================
# 2. SESSION STATE INIT
# ============================================
if "user" not in st.session_state:
    st.session_state.user = None
if "show_login" not in st.session_state:
    st.session_state.show_login = True
if "show_upload_modal" not in st.session_state:
    st.session_state.show_upload_modal = False
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "Dashboard Inteligente"

# ============================================
# 3. AUTH DIALOG (LOGIN / SIGNUP)
# ============================================
@st.experimental_dialog("Acceso a StockZero", width="small")
def auth_dialog():
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])

    with tab1:  # LOGIN
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Contraseña", type="password", key="login_pwd")
        if st.button("Entrar", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                st.session_state.user = res.user
                st.session_state.show_login = False
                st.rerun()
            except Exception as e:
                st.error("Credenciales inválidas")

    with tab2:  # SIGNUP
        name = st.text_input("Nombre de Empresa", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        pwd = st.text_input("Contraseña (6+)", type="password", key="signup_pwd")
        if st.button("Crear Cuenta", type="primary"):
            if len(pwd) < 6:
                st.error("Mínimo 6 caracteres")
            else:
                try:
                    res = supabase.auth.sign_up({"email": email, "password": pwd})
                    # Guardar cliente
                    supabase.table("clients").insert({
                        "id": res.user.id,
                        "name": name,
                        "plan": "free"
                    }).execute()
                    st.success("Cuenta creada. Verifica tu email.")
                except Exception as e:
                    st.error(str(e))

# Mostrar login si no hay usuario
if st.session_state.show_login:
    auth_dialog()
    st.stop()

# ============================================
# 4. SIDEBAR: LOGOUT + USER INFO
# ============================================
with st.sidebar:
    st.markdown(f"**Empresa:** {st.session_state.user.user_metadata.get('name', 'N/A')}")
    if st.button("Cerrar Sesión"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.show_login = True
        st.rerun()

# ============================================
# 5. CONFIG & HEADER
# ============================================
st.set_page_config(page_title="Stock Zero", page_icon="📦", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 5rem; color: #4361EE; margin-bottom: 0.5rem;'>StockZero</h1>
        <p style='font-size: 1.2rem; color: #666;'>Gestión Inteligente de Inventario</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Botón subir archivos (esquina derecha)
col_left, col_right = st.columns([8, 2])
with col_right:
    if st.button("Subir Archivos", type="primary"):
        st.session_state.show_upload_modal = True

# ============================================
# 6. MODAL SUBIDA
# ============================================
@st.dialog("Subir Archivos de Datos", width="large")
def upload_modal():
    st.markdown("### Guía de Formatos")

    with st.expander("Ejemplos", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Ventas (Largo)")
            ejemplo_largo = pd.DataFrame({
                'fecha': ['2025-01-01', '2025-01-01'],
                'producto': ['Café (Kg)', 'Leche (L)'],
                'cantidad_vendida': [7, 14]
            })
            st.dataframe(ejemplo_largo, hide_index=True)
            st.download_button("Descargar Largo", ejemplo_largo.to_csv(index=False), "ventas_largo.csv", "text/csv")

            st.markdown("#### Ventas (Ancho)")
            ejemplo_ancho = pd.DataFrame({
                'fecha': ['2025-01-01'], 'Café (Kg)': [7], 'Leche (L)': [14]
            })
            st.dataframe(ejemplo_ancho, hide_index=True)
            st.download_button("Descargar Ancho", ejemplo_ancho.to_csv(index=False), "ventas_ancho.csv", "text/csv")

        with col2:
            st.markdown("#### Entradas Stock")
            ejemplo_stock = pd.DataFrame({
                'fecha': ['2024-12-31'], 'producto': ['Café (Kg)'], 'cantidad_recibida': [120]
            })
            st.dataframe(ejemplo_stock, hide_index=True)
            st.download_button("Descargar Stock", ejemplo_stock.to_csv(index=False), "stock.csv", "text/csv")

    st.markdown("---")
    uploaded_ventas = st.file_uploader("Ventas (CSV)", type="csv", key="u_ventas")
    uploaded_stock = st.file_uploader("Stock (Opcional)", type="csv", key="u_stock")

    if st.button("Cerrar", type="secondary"):
        st.session_state.show_upload_modal = False
        st.rerun()

    user_id = st.session_state.user.id

    # === VENTAS ===
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
            df_ventas['user_id'] = user_id

            st.session_state.df_ventas_trazabilidad = df_ventas
            st.success("Ventas cargadas.")

            # Guardar en Supabase
            data = df_ventas[['user_id', 'fecha', 'producto', 'cantidad_vendida']].to_dict('records')
            supabase.table("ventas").insert(data).execute()
            st.info("Guardado en Supabase.")

        except Exception as e:
            st.error(f"Error ventas: {e}")

    # === STOCK ===
    if uploaded_stock:
        try:
            df_stock = pd.read_csv(uploaded_stock)
            df_stock['fecha'] = pd.to_datetime(df_stock['fecha'], errors='coerce')
            df_stock = df_stock.dropna(subset=['fecha'])
            df_stock['cantidad_recibida'] = pd.to_numeric(df_stock['cantidad_recibida'], errors='coerce').fillna(0)
            df_stock['user_id'] = user_id

            st.session_state.df_stock_trazabilidad = df_stock
            st.success("Stock cargado.")

            data = df_stock[['user_id', 'fecha', 'producto', 'cantidad_recibida']].to_dict('records')
            supabase.table("stock").insert(data).execute()

        except Exception as e:
            st.error(f"Error stock: {e}")

    if uploaded_ventas or uploaded_stock:
        if st.button("Listo - Cerrar", type="primary"):
            st.session_state.show_upload_modal = False
            st.rerun()

if st.session_state.show_upload_modal:
    upload_modal()

# ============================================
# 7. MÓDULOS (IMPORTS CONDICIONALES)
# ============================================
try:
    from modules.core_analysis import procesar_multiple_productos
    from modules.trazability import calcular_trazabilidad_inventario
    from modules.components import (
        inventario_basico_app, crear_grafico_comparativo,
        crear_grafico_trazabilidad_total, generar_inventario_base
    )
    from modules.recipes import recetas_app
    RECIPES_AVAILABLE = True
except ImportError as e:
    st.warning("Módulos no disponibles. Usa ejemplo.")
    RECIPES_AVAILABLE = False
    def recetas_app(): st.error("Módulo recetas no disponible.")

# Inicializar datos si no existen
if 'df_ventas_trazabilidad' not in st.session_state:
    st.session_state.df_ventas_trazabilidad = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_vendida', 'user_id'])
if 'df_stock_trazabilidad' not in st.session_state:
    st.session_state.df_stock_trazabilidad = pd.DataFrame(columns=['fecha', 'producto', 'cantidad_recibida', 'user_id'])
if 'inventario_df' not in st.session_state:
    st.session_state.inventario_df = generar_inventario_base(use_example_data=True)

# ============================================
# 8. NAVEGACIÓN
# ============================================
st.markdown("---")
st.markdown("## Secciones")
cols = st.columns(5)
with cols[1]:
    if st.button("Dashboard", type="primary"): st.session_state.pagina_actual = "Dashboard Inteligente"
with cols[2]:
    if st.button("Optimización"): st.session_state.pagina_actual = "Optimización de Inventario"
with cols[3]:
    if st.button("Control Inventario"): st.session_state.pagina_actual = "Control de Inventario Básico"

st.markdown("---")
pagina = st.session_state.pagina_actual

# ============================================
# 9. PÁGINAS
# ============================================
if pagina == "Dashboard Inteligente":
    try:
        from pages._0_Dashboard_Enhanced import dashboard_enhanced_app
        dashboard_enhanced_app()
    except Exception as e:
        st.error(f"Error Dashboard: {e}")

elif pagina == "Optimización de Inventario":
    st.header("Optimización de Inventario")
    if not st.session_state.df_ventas_trazabilidad.empty:
        st.success("Datos listos. ¡Calcula!")
        # Aquí irá tu IA
    else:
        st.info("Sube archivos desde el botón superior.")

elif pagina == "Control de Inventario Básico":
    inventario_basico_app()

# ============================================
# 10. FOOTER
# ============================================
st.markdown("---")
st.caption(f"© 2025 StockZero | Usuario: {st.session_state.user.email}")
