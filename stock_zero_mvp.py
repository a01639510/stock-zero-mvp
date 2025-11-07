# stock_zero_mvp.py (Solo se muestra la sección de Trazabilidad modificada)

# ... (Código anterior hasta la selección del producto) ...

                    # Gráfico de Trazabilidad
                    st.markdown("---")
                    st.markdown("### 📈 Trazabilidad de Inventario (Simulación de PR)")
                    
                    producto_seleccionado_inv = st.selectbox(
                        "Selecciona un producto para ver la simulación de stock y órdenes:",
                        options=df_exitosos['producto'].tolist(),
                        key="selector_inventario_proyectado" 
                    )
                    
                    if producto_seleccionado_inv:
                        resultado_prod = df_exitosos[df_exitosos['producto'] == producto_seleccionado_inv].iloc[0].to_dict()
                        
                        # Obtener Stock Actual
                        df_inv_basico = st.session_state.get('inventario_df', pd.DataFrame())
                        stock_actual = 0.0
                        mensaje_stock = "⚠️ **Stock Inicial/Actual no cargado.** Usando Stock = 0. ¡Actualiza el Stock Actual en la pestaña de Control de Inventario Básico!"
                        
                        # ... (Lógica robusta para obtener stock actual) ...
                        if not df_inv_basico.empty and 'Producto' in df_inv_basico.columns:
                            stock_row = df_inv_basico[df_inv_basico['Producto'] == producto_seleccionado_inv]
                            if not stock_row.empty:
                                try:
                                    stock_actual = float(stock_row['Stock Actual'].iloc[0])
                                    mensaje_stock = f"Stock Inicial/Actual: **{stock_actual:.2f}** (tomado de Control de Inventario Básico)."
                                except:
                                    stock_actual = 0.0
                        
                        st.warning(mensaje_stock)

                        # LLAMADA AL MÓDULO TRAZABILITY (NUEVOS PARÁMETROS)
                        try:
                            df_trazabilidad = calcular_trazabilidad_inventario(
                                st.session_state['df_ventas_trazabilidad'],
                                st.session_state['df_stock_trazabilidad'],
                                producto_seleccionado_inv,
                                stock_actual,
                                resultado_prod['punto_reorden'],           # <--- NUEVO
                                resultado_prod['cantidad_a_ordenar'],      # <--- NUEVO
                                resultado_prod['pronostico_diario_promedio'],
                                lead_time
                            )

                            if df_trazabilidad is not None and not df_trazabilidad.empty:
                                # LLAMADA AL MÓDULO COMPONENTS (Gráfico)
                                fig_trazabilidad = crear_grafico_trazabilidad_total(
                                    df_trazabilidad,
                                    resultado_prod,
                                    lead_time
                                )
                                st.pyplot(fig_trazabilidad)
                            else:
                                st.error(f"❌ La función de trazabilidad no devolvió datos válidos para {producto_seleccionado_inv}.")
                        
                        except Exception as e:
                            st.error(f"❌ Error crítico al generar la trazabilidad. Detalle: {e}")

                    # ... (Código restante) ...
