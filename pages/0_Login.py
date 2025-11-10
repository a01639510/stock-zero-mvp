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
                data, error = response

                if error:
                    st.error(f"Error: {str(error)}")
                elif data and data.user:
                    # ¡ÉXITO!
                    st.session_state.user = data.user
                    st.session_state.user_id = data.user.id
                    st.session_state.access_token = data.access_token
                    st.success("¡Login exitoso!")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except Exception as e:
                st.error(f"Error: {str(e)}")

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
                    data, error = response

                    if error:
                        st.error(f"Error: {str(error)}")
                    else:
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# === LOGOUT ===
if "user" in st.session_state:
    st.sidebar.success(f"Bienvenido, {st.session_state.user.email}")
    if st.sidebar.button("Cerrar Sesión"):
        try:
            supabase.auth.sign_out()
        except:
            pass
        st.session_state.clear()
        st.rerun()
