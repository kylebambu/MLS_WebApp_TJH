import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
from utils import *

import folium
from folium.plugins import MarkerCluster

st.set_page_config(layout="wide")

st.header("MLS thing")
st.subheader("Sup Dylan")

uploaded_file = st.file_uploader("Upload MLS file")


if uploaded_file is not None:

    viable_properties_list = inital_setup(uploaded_file)

    all_properties = []

    for entry in viable_properties_list:
        active_property = entry['active_property']
        comparables = entry['comparables']
        
        all_properties.append(active_property)
        all_properties.extend(comparables.to_dict(orient='records'))

    center_lat = sum(property['Geo Lat'] for property in all_properties) / len(all_properties)
    center_lon = sum(property['Geo Lon'] for property in all_properties) / len(all_properties)

    # Create a map centered at the calculated location
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Create a MarkerCluster for the properties
    marker_cluster = MarkerCluster().add_to(m)

    list_numbers = {}
    # Iterate through viable properties and add markers to the map
    for entry in viable_properties_list:
        active_property = entry['active_property']
        comparables = entry['comparables']
        

        # Add a marker for the active property
        active_property_info = f"Active Property: {active_property['List Number']}<br>Price: ${active_property['List Price']}<br>Lot Size: {active_property['Approx Lot SqFt']} sqft"
        folium.Marker(
            location=[active_property['Geo Lat'], active_property['Geo Lon']],
            popup=active_property_info,
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(marker_cluster)
        
        # Add markers for comparables
        for _, comp in comparables.iterrows():
            comp_info = f"Comparable: {comp['List Number']}<br>Price: ${comp['Sold Price']}<br>Lot Size: {comp['Approx Lot SqFt']} sqft"
            folium.Marker(
                location=[comp['Geo Lat'], comp['Geo Lon']],
                popup=comp_info,
                icon=folium.Icon(color='red', icon='home')
            ).add_to(marker_cluster)

    # Save the map to an HTML file (optional)
    #m.save('property_map.html')

    st_folium(m, width=800,height=600)
    
    property_choices = [entry['active_property']['Address'] for entry in viable_properties_list]

    dropdown_choice = st.selectbox("dropdown", property_choices)

    result =  [index for index, item in enumerate(viable_properties_list) if item['active_property']['Address'] == dropdown_choice]

    selected_columns = viable_properties_list[result[0]]['comparables'][["Address", "Listing Agent", "Close of Escrow Date", "Sold Price", "Price/SqFt", "Approx SQFT", "Year Built", "# Bedrooms", "# Bathrooms", "Pool", "Approx Lot Acres", "Days on Market"]]

    st.dataframe(selected_columns, hide_index=True)

    st.header(result)