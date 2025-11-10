# stock_zero_mvp.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client

st.set_page_config(page_title="Stock Zero", layout="wide")

# === CONEXIÓN SUPABASE ===
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase = create_client(supabase_url, supabase_key)

# === ESTADO DE SESIÓN ===
if "user" not in st.session_state:
    st.session_state.user = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# === FUNCIÓN DE LOGIN ===
def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        data, error = response
        if error:
            st.error(f"Error: {str(error)}")
            return False
        if data and data.user:
            st.session_state.user = data.user
            st.session_state.user_id = data.user.id
            st.session_state.access_token = data.access_token
            return True
        else:
            st.error("Credenciales incorrectas")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

# === FUNCIÓN DE REGISTRO ===
def signup(email, password, confirm_password):
    if password != confirm_password:
        st.error("Las contraseñas no coinciden")
        return False
    if len(password) < 6:
        st.error("Mínimo 6 caracteres")
        return False
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        data, error = response
        if error:
            st.error(f"Error: {str(error)}")
            return False
        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
        return True
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

# === FUNCIÓN DE LOGOUT ===
def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.clear()
    st.rerun()

# ========================================
# === SI NO ESTÁ LOGUEADO → MOSTRAR LOGIN ===
# ========================================
if not st.session_state.user:
    st.title("Stock Zero")

    tab1, tab2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
    # === LOGIN ===
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Login"):
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    data, error = response
    
                    if error:
                        st.error(f"Error: {str(error)}")
                    elif data and data.user:
                        st.session_state.user = data.user
                        st.session_state.user_id = data.user.id
                        st.success("¡Login exitoso!")
                        st.rerun()  # ← ESTO ES LA CLAVE
                    else:
                        st.error("Credenciales incorrectas")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Contraseña", type="password", key="signup_pass1")
            confirm_password = st.text_input("Confirmar Contraseña", type="password", key="signup_pass2")
            if st.form_submit_button("Crear Cuenta"):
                signup(email, password, confirm_password)

    st.stop()  # ← Detiene ejecución si no está logueado

# ========================================
# === SI ESTÁ LOGUEADO → MOSTRAR DASHBOARD ===
# ========================================

# === SIDEBAR ===
with st.sidebar:
    st.image("https://via.placeholder.com/100", caption="Stock Zero", width=100)
    st.success(f"Usuario: {st.session_state.user.email}")
    st.markdown("### Navegación")
    st.markdown("- [Home](stock_zero_mvp.py)")
    st.markdown("- [Archivos](pages/1_Archivos.py)")
    st.markdown("- [Inventario](pages/2_Inventario.py)")
    st.markdown("- [Análisis](pages/3_Analisis.py)")
    st.markdown("- [Productos](pages/4_Productos.py)")
    if st.button("Cerrar Sesión"):
        logout()

# === CARGAR DATOS DEL USUARIO ===
@st.cache_data(ttl=60)
def load_data():
    try:
        ventas = supabase.table("ventas").select("*").eq("user_id", st.session_state.user_id).execute()
        stock = supabase.table("stock").select("*").eq("user_id", st.session_state.user_id).execute()
        return pd.DataFrame(ventas.data), pd.DataFrame(stock.data)
    except:
        return pd.DataFrame(), pd.DataFrame()

df_ventas, df_stock = load_data()
st.session_state.df_ventas = df_ventas
st.session_state.df_stock = df_stock

# === DASHBOARD ===
st.title("Stock Zero")
st.header("Main Dashboard")

if df_ventas.empty:
    st.info("Sube datos en **Archivos** para ver el dashboard.")
else:
    df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
    ventas_hist = df_ventas.groupby('fecha')['cantidad_vendida'].sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=ventas_hist.index, y=ventas_hist.values, name="Ventas"))
    if not df_stock.empty:
        fig.add_hline(y=df_stock['cantidad_recibida'].sum(), line_dash="dash", line_color="green")
    fig.add_hline(y=100, line_dash="dot", line_color="red", annotation_text="PR")
    fig.update_layout(title="Flujo de Inventario", height=500)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Ventas Hoy", f"{ventas_hist.iloc[-1] if len(ventas_hist) > 0 else 0:.0f}")
    with col2: st.metric("Stock Total", f"{df_stock['cantidad_recibida'].sum() if not df_stock.empty else 0:.0f}")
    with col3: st.metric("Críticos", len(df_stock[df_stock['cantidad_recibida'] < 10]) if not df_stock.empty else 0)
    with col4: st.metric("Valor", f"${(df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum():,.0f}" if not df_stock.empty else "$0")

st.success("Dashboard activo.")
