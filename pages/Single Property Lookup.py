import streamlit as st
from utils import *
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="Single Property Lookup", layout="wide")

st.header("Single Property Lookup")


input_property = {}
input_property["Address"] = st.text_input("Property Address:")

if input_property:
    sold_properties = init_setup_func()

    zillow_request_url = "https://api.bridgedataoutput.com/api/v2/zestimates_v2/zestimates"

    params = {
        "access_token": st.secrets["zillow_API"],
        "limit": 1,
        "address": input_property["Address"]
    }

    output = make_http_request(zillow_request_url, params=params)

    input_lat, input_lon = output["bundle"][0]["Latitude"], output["bundle"][0]["Longitude"]

    #st.text(input_lat)
    #st.text(input_lon)
    
    #st.text("hey")
    row1 = {}

    row1["col1"], row1["col2"], row1["col3"], row1["col4"] = st.columns(4)

    # with row1["col1"]:
    #     select = row1["col1"].selectbox("dropbox", ["% Purchase Discount", "Purchase Price"])

    # with row1["col2"]:
    #     if select == "% Purchase Discount":
    #         pct_disct = st.number_input(select, min_value=0, max_value=100, value=10)
    #     else:
    #         purchase_price = st.number_input(select, min_value=0)
    #     #search_radius = st.text_input("Search Radius (mi)")


    purchase_price = row1["col1"].number_input("Purchase Price", min_value=0)
    input_radius = row1["col2"].number_input("Search Radius", min_value=0.25,max_value=5.0, value=1.0)
    input_lot_sqft = row1["col3"].number_input("Lot Sqft", min_value=0)
    input_lot_var = row1["col4"].selectbox("% Lot Sqft Variance", ["Any", "25", "50", "100"], index=2)

    if input_lot_var == "Any":
        input_lot_var = 1000
    else:
        input_lot_var = int(input_lot_var)/100

    if (purchase_price != 0 and input_lot_var != 0):
        input_property['Approx Lot SqFt'] = input_lot_sqft
        input_property['Geo Lat'] = input_lat
        input_property['Geo Lon'] = input_lon
        input_property['List Price'] = purchase_price

        a = filter_properties2(input_property, sold_properties, 1-input_lot_var, 1+input_lot_var, input_radius)

        viable_properties_list = calculate_viability(a, 0)
        #st.text(b)

        # all_properties = []

        # for entry in viable_properties_list:
        #     active_property = entry['active_property']
        #     comparables = entry['comparables']
            
        #     all_properties.append(active_property)
        #     all_properties.extend(comparables.to_dict(orient='records'))

        # center_lat = sum(property['Geo Lat'] for property in all_properties) / len(all_properties)
        # center_lon = sum(property['Geo Lon'] for property in all_properties) / len(all_properties)

        # # Create a map centered at the calculated location
        # m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # # Create a MarkerCluster for the properties
        # marker_cluster = MarkerCluster().add_to(m)

        # list_numbers = {}
        # # Iterate through viable properties and add markers to the map
        # for entry in viable_properties_list:
        #     active_property = entry['active_property']
        #     comparables = entry['comparables']
            

        #     # Add a marker for the active property
        #     active_property_info = "a"#f"Active Property: {active_property['List Number']}<br>Price: ${active_property['List Price']}<br>Lot Size: {active_property['Approx Lot SqFt']} sqft"
        #     folium.Marker(
        #         location=[active_property['Geo Lat'], active_property['Geo Lon']],
        #         popup=active_property_info,
        #         icon=folium.Icon(color='blue', icon='home')
        #     ).add_to(marker_cluster)
            
        #     # Add markers for comparables
        #     for _, comp in comparables.iterrows():
        #         comp_info = f"Comparable: {comp['Address']}<br>List Number: {comp['List Number']}<br>Price: ${comp['Sold Price']}<br>Lot Size: {comp['Approx Lot SqFt']} sqft"
        #         folium.Marker(
        #             location=[comp['Geo Lat'], comp['Geo Lon']],
        #             popup=comp_info,
        #             icon=folium.Icon(color='red', icon='home')
        #         ).add_to(marker_cluster)

        # Save the map to an HTML file (optional)
        #m.save('property_map.html')

        viable_properties_list[0]['comparables']["Zillow Link"] = (viable_properties_list[0]['comparables']).apply(get_zillow_link, axis=1)
        # viable_properties_list[0]['comparables']["Street View Link"] = (viable_properties_list[0]['comparables']).apply(get_google_street_link, axis=1)
        m = make_map(viable_properties_list)

        st_folium(m, width=800,height=600)

        #viable_properties_list[0]['comparables']["Zillow Link"] = get_zillow_link(viable_properties_list)
        selected_columns = viable_properties_list[0]['comparables'][["Address", "Listing Agent", "Close of Escrow Date", "Sold Price", "Price/SqFt", "Approx SQFT", "Year Built", "# Bedrooms", "# Bathrooms", "Pool", "Approx Lot Acres", "Days on Market", "Zillow Link"]]

        st.dataframe(selected_columns, hide_index=True)


