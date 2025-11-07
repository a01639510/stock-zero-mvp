    # --- Sección de Ejemplos y Formatos ---
    with st.expander("📘 Guía de Formatos y Ejemplos de Archivos", expanded=False):
        st.markdown("### 📊 Formatos Aceptados")
        
        col_guia1, col_guia2 = st.columns(2)
        
        with col_guia1:
            st.markdown("#### 📈 Archivo de Ventas (Requerido)")
            
            # Ejemplo Formato Largo
            st.markdown("**Formato 1: Largo (Recomendado)**")
            ejemplo_ventas_largo = generar_ejemplo_ventas().head(5)  # Mostrar solo 5 filas
            st.dataframe(
                ejemplo_ventas_largo,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "fecha": st.column_config.DateColumn("Fecha"),
                    "producto": st.column_config.TextColumn("Producto"),
                    "cantidad_vendida": st.column_config.NumberColumn("Cantidad Vendida", format="%d")
                }
            )
            st.caption("↓ Descarga el archivo completo de ejemplo")
            csv_ventas = generar_ejemplo_ventas().to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Ejemplo (Formato Largo)",
                data=csv_ventas,
                file_name="ejemplo_ventas_largo.csv",
                mime="text/csv",
                key="download_ventas_largo"
            )
            
            st.markdown("---")
            
            # Ejemplo Formato Ancho
            st.markdown("**Formato 2: Ancho**")
            ejemplo_ventas_ancho = generar_ejemplo_ventas_ancho().head(5)
            st.dataframe(
                ejemplo_ventas_ancho,
                use_container_width=True,
                hide_index=True
            )
            st.caption("↓ Descarga el archivo completo de ejemplo")
            csv_ventas_ancho = ejemplo_ventas_ancho.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Ejemplo (Formato Ancho)",
                data=csv_ventas_ancho,
                file_name="ejemplo_ventas_ancho.csv",
                mime="text/csv",
                key="download_ventas_ancho"
            )
        
        with col_guia2:
            st.markdown("#### 📦 Archivo de Entradas de Stock (Opcional)")
            st.markdown("**Formato: Largo**")
            
            ejemplo_stock = generar_ejemplo_stock()
            st.dataframe(
                ejemplo_stock,
                use_container_width=True,
                hide_index=True
            )
            st.info("💡 **Nota:** Este archivo es opcional pero mejora la precisión del análisis de trazabilidad.")
            
            csv_stock = ejemplo_stock.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Ejemplo de Stock",
                data=csv_stock,
                file_name="ejemplo_stock.csv",
                mime="text/csv",
                key="download_stock"
            )
        
        st.markdown("---")
        st.markdown("### ✅ Requisitos Importantes")
        st.markdown("""
        - **Fechas:** Formato `YYYY-MM-DD` (ejemplo: 2024-01-15)
        - **Columnas:** No usar espacios adicionales ni caracteres especiales
        - **Cantidades:** Solo números positivos
        - **Codificación:** UTF-8 (estándar para CSV)
        - **Separador:** Coma (`,`)
        """)
