import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import requests
import json
import time

apikey = '77fb35caa2msh8d7338a11a6579ep12bd27jsnf71d495a0d50'
apihost = 'zillow-com1.p.rapidapi.com'

def convert_df(df):
    return df.to_csv()

# In this block of code the user is asked to specify some search criteria like the city, state and
# How many result pages the API should look through
header = st.container()
inputform = st.container()
evaluation = st.container()

propdetails = pd.read_csv('0801_propdetail_clean_losangeles.csv')
df_prop_details = pd.DataFrame(propdetails)
df_neighborhoods = df_prop_details.groupby(['address.city']).agg({'zpid':'count'}).sort_values(by='zpid', ascending=False)

with header:
    st.title("Property Analyzer")
with inputform:
    st.header('Tell me about your real estate')

    inp_col, map_col = st.columns(2)
    city = inp_col.text_input('Which city is it located in?', placeholder = 'New York City')
    state = inp_col.text_input('In which state?', placeholder = 'NY')
    pages = inp_col.number_input('How many Zillow pages do you want to use for comparison?', min_value = 1, value = 1)
    buildingtypes = inp_col.multiselect(
     'What type of buildings do you want to use for comparison?',['Houses', 'Townhomes'])
    search_button = inp_col.button('Search')

    if search_button == True:
        #create empty list to collect first x pages of search results. (Number of pages is defined by user input before)
        #Each API response contains info from one page of zillow search results. Each response is transformed into a
        #dataframe and collected in the list below
        search_results_dataframes = []

        pages_list = list(range(1,pages+1))
        search_str = city + '' + state

        for page in pages_list:

            #basically sample code copied from RapidAPI. Only modification is that the querystring
            #refers to variables to react to user input
            url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"

            querystring = {"location":search_str,'page': page, "home_type":"Houses"}

            headers = {
             "X-RapidAPI-Key": apikey,
             "X-RapidAPI-Host": apihost
            }

            #execute the API request & transform to json directly
            z_for_sale_resp = requests.request("GET", url, headers=headers, params=querystring)
            z_search_results_resp_json = z_for_sale_resp.json()

            #transform json to dataframe:
            df_search_results_page_x = pd.json_normalize(data = z_search_results_resp_json['props'])
            search_results_dataframes.append(df_search_results_page_x)

            #wait 0.5 sec based on RapidAPI limit of 2 requests per second
            time.sleep(0.5)

            #concatenate list of dataframes into one big dataframe called df_total_search_results
            df_total_search_results = pd.concat(search_results_dataframes)

        # to be able to extract zpid's for later search requests, but still get zpid as the index,
        # we create a new column 'zpid_index' and then set 'zpid_index' as the dataframe index
        df_total_search_results['zpid_index'] = df_total_search_results['zpid']
        df_results_zpid = df_total_search_results.set_index('zpid_index')

        #map_col.dataframe(df_results_zpid)
        df_sr_map = df_results_zpid[{'latitude', 'longitude'}]
        df_sr_map.dropna(axis = 0, how = 'any', inplace = True)
        #map_col.dataframe(df_sr_map)
        map_col.map(df_sr_map)

        #df_prop_map = df_prop_details[{'latitude', 'longitude'}]
        #map_col.dataframe(df_prop_map)
        with evaluation:
            st.header('Here is what I found about similar properties in your area')
            st.write('Your property is located in', city, ",", state)
            st.caption('This table shows you some details about other properties in your area. You can compare prices, living area etc.')

            column_names = ['address', 'price', 'livingArea', 'bedrooms','bathrooms']
            column_names_geo = ['address', 'price', 'livingArea', 'bedrooms','bathrooms','latitude', 'longitude']

            df_prop_details = pd.DataFrame(pd.read_csv('0804_searchresults_oc.csv'))
            df_prop_details.dropna(axis = 0, how = 'any', subset=['livingArea', 'bedrooms', 'bathrooms'], inplace = True)
            df_prop_details.astype({'livingArea':'int', 'bedrooms':'int', 'bathrooms':'int'})

            df_prop_map = df_prop_details[column_names_geo].reindex(columns = column_names_geo)

            #df_neighborhoods = df_prop_details.groupby(['address.city']).agg({'zpid':'count'}).sort_values(by='zpid', ascending=False)
            #st.bar_chart(df_neighborhoods)

            df_similarhomes = df_prop_details[{'address', 'price', 'livingArea', 'bedrooms','bathrooms','latitude', 'longitude'}]
            df_similarhomes.astype({'livingArea':'int', 'bedrooms':'int', 'bathrooms':'int'})


            csv = convert_df(df_prop_details)
            st.download_button('Download this list',csv )
            st.dataframe(df_prop_details)


            st.caption('This map shows properties with similar features to yours')

            df_prop_map.dropna(axis = 0, how = 'any', inplace = True)
            st.map(df_prop_map)

            st.dataframe(df_similarhomes.reindex(columns = ['address', 'price', 'livingArea', 'bedrooms','bathrooms']))
            #st.dataframe(df_prop_details[list(column_names)])
            #st.write(df_prop_details['livingArea'].dtypes)



            #df6 = (df.groupby(['A', 'B'], as_index=False)
                # .agg({'C':'sum','D':'mean'})
            #df_prop_pricechart = df_prop_details[{'price', 'yearBuilt'}]
            #c = alt.Chart(df_prop_pricechart).mark_circle().encode(
                # x='yearBuilt',
                # y='price', tooltip=['yearBuilt', 'price'])

            #c = alt.Chart(df_prop_pricechart).mark_circle().encode(
            #alt.X('yearBuilt', scale=alt.Scale(domain=(1900,2022))),
            #alt.Y('price', scale=alt.Scale(domain=(500000,8000000))),
            #tooltip=['yearBuilt', 'price'])

            #st.altair_chart(c, use_container_width=True)
