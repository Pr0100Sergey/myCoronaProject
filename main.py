import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from celluloid import Camera
import folium as fo
from streamlit_folium import folium_static
import datetime
import random as rnd

with st.echo(code_location='below'):
    st.title("MyCoronaApp")

    df = pd.read_csv("owid-covid-data.csv")
    df['date'] = pd.to_datetime(df['date']).dt.date
    countries = sorted(list(set(df['location'])))
    columns = ['total_cases', 'total_deaths', 'new_cases', 'new_cases_smoothed', 'new_deaths', 'new_deaths_smoothed', 'total_cases_per_million', 'total_deaths_per_million', 'new_cases_per_million', 'new_cases_smoothed_per_million', 'new_deaths_per_million', 'new_deaths_smoothed_per_million']

    mode = st.radio("Pick the mode (Animation may take some time)", ('Comparing mode', 'Animation mode', 'Map mode'))

    if mode == 'Comparing mode' or mode == 'Animation mode':
        country = st.multiselect('Select some countries to compare', countries, default=['Russia', 'United States'])
        if not country:
            st.error('Error: Please pick at least one country')

        params = st.multiselect('Select some parameters to compare', columns, default=['new_cases_smoothed', 'new_deaths_smoothed'])
        if not params:
            st.error('Error: Please pick at least one parameter')

        p = params.copy()
        p.extend(['location', 'date'])
        dfs = df[p]

        a = []
        for i in dfs['location']:
            a.append(i in country)
        dfs = dfs[a]


        st_date = dfs.sort_values('date')['date'].iloc()[0]
        start_date = st.date_input('Start date', st_date)
        end_date = st.date_input('End date', datetime.date.today())
        if start_date >= end_date:
            st.error('Error: End date must fall after start date. Please pick other dates')
        dfs = dfs[(dfs['date'] >= start_date) & (dfs['date'] <= end_date)]
        dfs = dfs.set_index('date')

    if mode == 'Comparing mode':
        dfs = dfs.melt('location', var_name='parameters', value_name='values', ignore_index=False)
        g = sns.relplot(x=dfs.index.values, y="values", hue='location', style='parameters', kind='line', data=dfs)
        g.fig.autofmt_xdate()
        st.pyplot(g)

    if mode == 'Animation mode':
        st.markdown("""
        You can see the legend in comparing mode
        """)
        fig = plt.figure()
        camera = Camera(fig)
        colors = []
        for a in country:
            colors.append((rnd.random(), rnd.random(), rnd.random()))
        for t in pd.date_range(start_date, end_date):
            dfs_anim = dfs[dfs.index.values <= t]
            for i, c in enumerate(country):
                dfs_anim_c = dfs_anim[dfs_anim['location'] == c]
                for par in params:
                    plt.plot(dfs_anim_c.index.values, dfs_anim_c[par], c=colors[i])
            camera.snap()
        animation = camera.animate()
        components.html(animation.to_jshtml(), height=1000)

    if mode == 'Map mode':
        par = st.selectbox("Choose the parameter to compare", columns, index=0)
        st.markdown("""
            This is current situation
            """)
        dfs_map = df[df['date'] == df['date'].iloc()[-1]][['location', par]]
        dfs_map.replace('United States', "United States of America", inplace=True)
        dfs_map.replace('Czechia', "Czech Republic", inplace=True)
        dfs_map.replace('Tanzania', "United Republic of Tanzania", inplace=True)
        dfs_map.replace('Democratic Republic of Congo', "Democratic Republic of the Congo", inplace=True)
        dfs_map.replace('Congo', "Republic of the Congo", inplace=True)
        dfs_map.replace('Serbia', "Republic of Serbia", inplace=True)

        m = fo.Map()
        country_shapes = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json'
        bins = list(dfs_map[par].quantile([0, 0.1, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1]))
        fo.Choropleth(
            geo_data=country_shapes,
            name='choropleth COVID-19',
            data=dfs_map,
            columns=['location', par],
            key_on='feature.properties.name',
            fill_color='PuRd',
            nan_fill_color='white',
            bins=bins
        ).add_to(m)
        folium_static(m)
