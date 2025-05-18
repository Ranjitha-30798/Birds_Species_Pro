import streamlit as st
import pandas as pd
import plotly.express as px

# Load Data
forest_raw = pd.read_csv(r"C:\Users\Ranjitha\OneDrive\Documents\cleaned_bird_forest_data.csv", parse_dates=['Date'])
grassland_raw = pd.read_csv(r"C:\Users\Ranjitha\OneDrive\Documents\cleaned_bird_grass_data.csv", parse_dates=['Date'])

# Clean Process

def clean_bird_data(df):
   
    # 1. Drop duplicates
    df = df.drop_duplicates()

    # 2. Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # 3. Fill or drop missing values in critical columns (example)
    df = df.dropna(subset=['Date', 'Location_Type', 'Plot_Name'])

    # 4. Add Month, Year, Season columns
    df['Month'] = df['Date'].dt.month
    df['Year'] = df['Date'].dt.year
    df['Season'] = df['Month'].apply(lambda x: 'Spring' if x in [3,4,5] else (
                                               'Summer' if x in [6,7,8] else (
                                               'Fall' if x in [9,10,11] else 'Winter')))
    # 5. Convert Observer to string if exists
    if 'Observer' in df.columns:
        df['Observer'] = df['Observer'].astype(str)

    return df

forest_clean = clean_bird_data(forest_raw)
grassland_clean = clean_bird_data(grassland_raw)

# csv
forest_clean.to_csv(r"C:\Users\Ranjitha\OneDrive\Documents\cleaned_bird_forest_data.csv", index=False)
grassland_clean.to_csv(r"C:\Users\Ranjitha\OneDrive\Documents\cleaned_bird_grass_data.csv", index=False)

# concat cleaned data
common_cols = list(set(forest_clean.columns) & set(grassland_clean.columns))
df = pd.concat([forest_clean[common_cols], grassland_clean[common_cols]], ignore_index=True)

# Sreamlit

# Sidebar Filters with "All"
years = ['All'] + sorted(df['Year'].dropna().unique().tolist())
locations = ['All'] + df['Location_Type'].dropna().unique().tolist()
seasons = ['All'] + df['Season'].unique().tolist()

st.sidebar.header("🔍 Filters")
selected_year = st.sidebar.selectbox("Select Year", years)
selected_location = st.sidebar.selectbox("Select Location Type", locations)
selected_season = st.sidebar.selectbox("Select Season", seasons)

filtered_df = df.copy()
if selected_year != 'All':
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]
if selected_location != 'All':
    filtered_df = filtered_df[filtered_df['Location_Type'] == selected_location]
if selected_season != 'All':
    filtered_df = filtered_df[filtered_df['Season'] == selected_season]

st.title("🕊️ Bird Monitoring Dashboard")
st.markdown(f"**Showing data for `{selected_location}` habitat in `{selected_season}` `{selected_year}`**")

st.dataframe(filtered_df)

# Map if coordinates exist
if {'Latitude', 'Longitude'}.issubset(filtered_df.columns) and not filtered_df.empty:
    st.subheader("📍 Bird Observation Map")
    fig_map = px.scatter_mapbox(filtered_df,
                                lat='Latitude', lon='Longitude',
                                hover_name='Plot_Name',
                                hover_data=['Date', 'Temperature', 'Humidity'] if {'Temperature', 'Humidity'}.issubset(filtered_df.columns) else None,
                                color='Location_Type',
                                zoom=4, height=400)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map)

# Observation counts by Plot
if 'Plot_Name' in filtered_df.columns and not filtered_df.empty:
    st.subheader("📊 Observation Count per Plot")
    plot_counts = filtered_df['Plot_Name'].value_counts().reset_index()
    plot_counts.columns = ['Plot_Name', 'Observations']
    fig_bar = px.bar(plot_counts, x='Plot_Name', y='Observations',
                     title="Observations by Plot")
    fig_bar.update_layout(xaxis_title="Plot Name", yaxis_title="Observation Count")
    st.plotly_chart(fig_bar)

# Temporal Heatmap (Year vs Month)
st.subheader("📅 Temporal Heatmap (Year vs Month)")
heatmap_data = df.groupby(['Year', 'Month']).size().reset_index(name='Count')
fig_heatmap = px.density_heatmap(heatmap_data, x='Month', y='Year', z='Count',
                                 color_continuous_scale='Viridis',
                                 title="Monthly Observation Density")
st.plotly_chart(fig_heatmap)

# Temperature vs Humidity scatter
if {'Temperature', 'Humidity'}.issubset(filtered_df.columns) and not filtered_df.empty:
    st.subheader("🌡️ Temperature vs Humidity by Plot")
    fig_env = px.scatter(filtered_df, x='Temperature', y='Humidity',
                         color='Plot_Name',
                         hover_data=['Date', 'Observer'] if 'Observer' in filtered_df.columns else None,
                         title="Environmental Conditions")
    st.plotly_chart(fig_env)

# Conservation Insights if available
if 'PIF_Watchlist_Status' in filtered_df.columns and not filtered_df.empty:
    st.subheader("🛡️ Conservation Priority (PIF Watchlist)")
    pif_status = filtered_df['PIF_Watchlist_Status'].value_counts().reset_index()
    pif_status.columns = ['PIF_Watchlist_Status', 'Count']
    fig_pif = px.pie(pif_status, values='Count', names='PIF_Watchlist_Status',
                     title="PIF Watchlist Species Observations")
    st.plotly_chart(fig_pif)

# High-Activity Zones by Season and Habitat
st.subheader("📍 High Activity Zones")
activity = df.groupby(['Location_Type', 'Season']).size().reset_index(name='Observations')
fig_activity = px.bar(activity, x='Location_Type', y='Observations', color='Season',
                      title="Seasonal Observation Distribution by Habitat")
st.plotly_chart(fig_activity)

