import streamlit as st
from geopy.distance import geodesic
import pandas as pd
import requests
import folium
from folium.plugins import MarkerCluster

def filter_properties(actively_listed, sold_properties, lot_size_lower_bound=0.5, lot_size_upper_bound=1.5, radius_miles=1.0):
    filtered_properties = []
    for _, active_property in actively_listed.iterrows():
        if active_property['Dwelling Type'] == 'Single Family - Detached':
            # Calculate the lot size thresholds
            lot_size_lower = active_property['Approx Lot SqFt'] * lot_size_lower_bound
            lot_size_upper = active_property['Approx Lot SqFt'] * lot_size_upper_bound
            
            # Find sold properties within the radius
            nearby_sold_properties = sold_properties[
                (sold_properties['Dwelling Type'] == 'Single Family - Detached') &  # Filter sold properties by Dwelling Type
                sold_properties.apply(
                    lambda sold_property: geodesic(
                        (active_property['Geo Lat'], active_property['Geo Lon']),
                        (sold_property['Geo Lat'], sold_property['Geo Lon'])
                    ).miles <= radius_miles,
                    axis=1
                )
            ]
            
            # Find comparables based on lot size
            comparables = nearby_sold_properties[
                (nearby_sold_properties['Approx Lot SqFt'] >= lot_size_lower) &
                (nearby_sold_properties['Approx Lot SqFt'] <= lot_size_upper)
            ]
            
            # Store filtered data
            filtered_properties.append({
                'active_property': active_property,
                'comparables': comparables
            })
        # break
    
    return filtered_properties

def calculate_viability(filtered_properties, min_sold_count=3):
    viable_properties = []
    for data in filtered_properties:
        active_property = data['active_property']
        comparables = data['comparables']
        
        # Calculate the threshold price
        threshold_price = active_property['List Price'] * 3  # Change 'original_price' to 'List Price'
        
        # Check if there are at least min_sold_count comparables that sold for more
        qualified_comparables = comparables[comparables['Sold Price'] > threshold_price]  # Change 'sale_price' to 'Sale Price'
        
        if len(qualified_comparables) >= min_sold_count:
            viable_properties.append({
                'active_property': active_property,
                'comparables': qualified_comparables
            })
    
    return viable_properties

def create_address(row):
    # Define the columns to include in the address
    address_columns = ['House Number', 'Building Number', 'Compass', 'Street Name', 'Unit #', 'St Dir Sfx', 'St Suffix', 'City/Town Code', 'State/Province']

    # Filter the columns and remove 'nan' values
    address_parts = [str(row[col]) for col in address_columns if row[col] and str(row[col]) != 'nan']

    # Remove empty strings and join the address parts with a comma between city and state
    formatted_address = ' '.join(address_parts)
    if 'City/Town Code' in row and 'State/Province' in row:
        city_state = f"{row['City/Town Code']}, {row['State/Province']}"
        formatted_address = formatted_address.replace(city_state, city_state, 1)

    return formatted_address

@st.cache_data
def inital_setup(uploaded_file):
    actively_listed_properties = pd.read_csv(uploaded_file, encoding='latin1')


    # Step 1: Load Data with updated file locations and column names
    sold_properties = pd.read_csv("sold_10323.csv", encoding='latin1')
    #actively_listed_properties = pd.read_csv(r"C:\Users\kyleb\Downloads\textexport.csv", encoding='latin1')

    # Step 2: Discount Active Listings
    actively_listed_properties['discounted_price'] = actively_listed_properties['List Price'] * 0.9  # Change 'original_price' to 'List Price'
    actively_listed_properties['Address'] = actively_listed_properties.apply(create_address, axis=1)
    sold_properties['Address'] = sold_properties.apply(create_address, axis=1)

    # Step 3: Filter by Lot Size and Distance
    filtered_data = filter_properties(actively_listed_properties, sold_properties)

    # Step 4: Calculate Viability
    min_sold_count = 3  # You can adjust this value as needed
    viable_properties_list = calculate_viability(filtered_data, min_sold_count)

    # Print the list of viable properties and their comparables
    # for entry in viable_properties_list:
    #    active_property = entry['active_property']
    #    comparables = entry['comparables']
        
        # print("Active Property:")
        # print(active_property)
        
        # print("Comparables:")
        # print(comparables)
        
        # print("=" * 30)  # Separator between properties

    # Calculate the map center by averaging Geo Lat and Geo Lon values from properties and comparables

    return viable_properties_list

@st.cache_data
def make_http_request(url, params=None, headers=None):
    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()  # If the response is in JSON format
        else:
            print(f"Request failed with status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed with error: {e}")
        return None
    
@st.cache_data
def filter_properties2(actively_listed, sold_properties, lot_size_lower_bound, lot_size_upper_bound, radius_miles):
    filtered_properties = []
    lot_size_lower = actively_listed['Approx Lot SqFt'] * lot_size_lower_bound
    lot_size_upper = actively_listed['Approx Lot SqFt'] * lot_size_upper_bound
    
    # Find sold properties within the radius
    nearby_sold_properties = sold_properties[
        (sold_properties['Dwelling Type'] == 'Single Family - Detached') &  # Filter sold properties by Dwelling Type
        sold_properties.apply(
            lambda sold_property: geodesic(
                (actively_listed['Geo Lat'], actively_listed['Geo Lon']),
                (sold_property['Geo Lat'], sold_property['Geo Lon'])
            ).miles <= radius_miles,
            axis=1
        )
    ]
    
    # Find comparables based on lot size
    comparables = nearby_sold_properties[
        (nearby_sold_properties['Approx Lot SqFt'] >= lot_size_lower) &
        (nearby_sold_properties['Approx Lot SqFt'] <= lot_size_upper)
    ]
    
    # Store filtered data
    filtered_properties.append({
        'active_property': actively_listed,
        'comparables': comparables
    })
    # break
    
    return filtered_properties

def make_map(viable_properties_list):
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
        active_property_info = "a"#f"Active Property: {active_property['List Number']}<br>Price: ${active_property['List Price']}<br>Lot Size: {active_property['Approx Lot SqFt']} sqft"
        folium.Marker(
            location=[active_property['Geo Lat'], active_property['Geo Lon']],
            popup=active_property_info,
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(marker_cluster)
        
        # Add markers for comparables
        for _, comp in comparables.iterrows():
            comp_info = f"Comparable: {comp['Address']}<br>List Number: {comp['List Number']}<br>Price: ${comp['Sold Price']}<br>Lot Size: {comp['Approx Lot SqFt']} sqft<br><a href='{comp['Zillow Link']}' target='_blank'>Zillow Link</a>"
            folium.Marker(
                location=[comp['Geo Lat'], comp['Geo Lon']],
                popup=comp_info,
                icon=folium.Icon(color='red', icon='home')
            ).add_to(marker_cluster)


    return m

@st.cache_data
def init_setup_func():
    sold_properties = pd.read_csv("sold_10323.csv", encoding='latin1')
    sold_properties['Address'] = sold_properties.apply(create_address, axis=1)
    
    return sold_properties

@st.cache_data
def get_zillow_link(row):
    print(row)
    input_property = row["Address"]
    zillow_request_url = "https://api.bridgedataoutput.com/api/v2/zestimates_v2/zestimates"

    params = {
        "access_token": st.secrets["zillow_API"],
        "limit": 1,
        "address": input_property
    }

    output = make_http_request(zillow_request_url, params=params)

    zillow_link = output["bundle"][0]["zillowUrl"]

    return zillow_link

# def get_google_street_link(row):
#     address = row["Address"]
#     base_url = "https://www.google.com/maps/place/"
#     address = address.replace(" ", "+")  # Replace spaces with "+" for the URL

#     street_view_url = f"{base_url}{address}&layer=c"  # Append the address and set the "layer" to "c" for Street View
    
#     return street_view_url

