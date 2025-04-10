
# (Script content placeholder - already provided above)

if 'df_show' in locals() and not df_show.empty and "SourceFile" in df_show.columns:
    st.subheader("📊 Radar Plot Comparison")
    selected_waxes = st.multiselect("Select up to 3 waxes to compare:", df_show["SourceFile"].unique(), max_selections=3)

    radar_columns = ["DropMeltingPoint", "Viscosity135C", "Penetration25C", "Density23C", "AcidValue", "OilContent"]
    if selected_waxes and all(col in df_show.columns for col in radar_columns):
        df_plot = df_show[df_show["SourceFile"].isin(selected_waxes)]
        radar_df = df_plot.set_index("SourceFile")[radar_columns]
        fig = px.line_polar(
            radar_df.reset_index(),
            r=radar_df.values.flatten(),
            theta=radar_df.columns.tolist() * len(radar_df),
            line_close=True,
            color=radar_df.reset_index()["SourceFile"].repeat(len(radar_df.columns)).values
        )
        st.plotly_chart(fig, use_container_width=True)
    elif selected_waxes:
        st.warning("⚠️ Radar plot not available: some required properties are missing.")
