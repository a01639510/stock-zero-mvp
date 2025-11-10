# pages/0_Login.py
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Login - Stock Zero")

# === CONEXIÓN ===
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase = create_client(supabase_url, supabase_key)

st.title("Stock Zero - Login")

col1, col2 = st.columns(2)

# === LOGIN ===
with col1:
    st.subheader("Iniciar Sesión")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Login"):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                # Supabase devuelve el objeto directamente (no una tupla)
                if hasattr(response, 'user') and response.user:
                    st.session_state.user = response.user
                    st.session_state.user_id = response.user.id
                    
                    # Session viene dentro del objeto response
                    if hasattr(response, 'session') and response.session:
                        st.session_state.access_token = response.session.access_token
                        st.session_state.refresh_token = response.session.refresh_token
                    
                    st.success("¡Login exitoso!")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except Exception as e:
                st.error(f"Error de autenticación: {str(e)}")

# === REGISTRO ===
with col2:
    st.subheader("Crear Cuenta")
    with st.form("signup"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Contraseña", type="password", key="signup_pass1")
        confirm_password = st.text_input("Confirmar Contraseña", type="password", key="signup_pass2")
        
        if st.form_submit_button("Crear Cuenta"):
            if password != confirm_password:
                st.error("Las contraseñas no coinciden")
            elif len(password) < 6:
                st.error("Mínimo 6 caracteres")
            else:
                try:
                    response = supabase.auth.sign_up({
                        "email": email,
                        "password": password
                    })
                    
                    if response.user:
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                    else:
                        st.error("No se pudo crear la cuenta")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# === LOGOUT EN SIDEBAR ===
if "user" in st.session_state and st.session_state.user:
    st.sidebar.success(f"Bienvenido, {st.session_state.user.email}")
    if st.sidebar.button("Cerrar Sesión"):
        try:
            supabase.auth.sign_out()
        except:
            pass
        st.session_state.clear()
        st.rerun()
