'''
FermentDB Streamlit App
'''

## 1.Install dependencies
#! pip install streamlit
#! pip install plotly
# streamlit run your_script.py or URL


## 2.Import modules
import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import plotly.express as px

from arango import ArangoClient
from streamlit_arango.config import Config

## 3. Connect to ArangoDB
# Initialize the ArangoDB client. 
client = ArangoClient(hosts=Config.ArangoDB.host)


# Initialize connection to database: "fermentdb" as root user
def connect_to_db():
    if 'db' not in st.session_state:
        st.session_state.db = client.db(
            name = Config.ArangoDB.database,
            username = Config.ArangoDB.username,
            password = Config.ArangoDB.password
        )
        #st.write(f"Connected to database '{st.session_state.db.name}' as {st.session_state.db.username}.")

    return st.session_state.db

def get_aql():
    return connect_to_db().aql


## 4. Streamlit UI
# Page confing
page_icon = "./assets/images/page_icon.png"

st.set_page_config(
    page_title="FermentDB",
    page_icon=page_icon # Favicon 
)


# 4.1 Query data from ArangoDB


# ------- Statistical Section ----------- #

st.header('FermentDB', divider='grey')

st.markdown("<h1 style='text-align: center; font-size: 30px;'>Welcome to <span style= 'font-size: 40px;'>FermentDB</span></h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center;'>A Database for High-cell Density Fermentations</h5>", unsafe_allow_html=True)

left_column, middle_column, right_column = st.columns(3)

with left_column:
    st.write(" X Strains")

with middle_column:
    st.write("Runs")

with right_column:
    st.write("Bioprocess Conditions")
    st.write("")
    st.markdown("<p style='text-align: right;font-size: 12px'> Version 1.0 released on June 18th, 2024<p>", unsafe_allow_html=True)




# if "strain" not in st.session_state:
#     st.session_state.strain = 0

#st.write(f"Selected options: {st.session_state.strain}.")

st.divider()
# ------- Explore Section ----------- #

st.markdown("<h3 style='text-align: center;'>Explore Fermentations</h3>", unsafe_allow_html=True)

st.markdown("<p style='text-align: center;'>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. </p>", unsafe_allow_html=True)
st.write("")
st.write("")
st.write("")

# Retrieve documents for a given collection
def get_doc(collection):
    '''
    Retrieve docuents for a given collection
    
    parameters:
        data_dict (dict): dictionary structure 
        map_list (list): list of nested keys

    return:
        nested_value: nested value given the provided list of keys

    example:
        >>> data_dict = {'a': {'b': {'c': 5}}}
        >>> value = get_from_nested_dict(data_dict=data_dict, map_list=['a', 'b', 'c'])
        >>> print(value)
        5
    '''
    aql = get_aql()
    cursor = aql.execute( f'''
        FOR doc IN {collection}
        RETURN doc.name
    ''')

    result = set()
    for item in cursor:
        result.add(item)
    
    return list(result)



left_column, middle_column, right_column = st.columns(3)

with left_column:
    option = st.selectbox(
        'Strain:',
        get_doc('Strain'))

    'Strain: ', option

with right_column:
    option = st.selectbox(
        'Process condition:',
        get_doc('Process_condition'))

    'Process condition: ', option

with middle_column:
    option = st.selectbox(
        'Fermenter Type:',
        get_doc('Fermenter'))

    'Fermenter Type: ', option
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown(
        "<style>div.stButton > button { width: 100%; text-align: center; }</style>", 
        unsafe_allow_html=True
        )
        st.button('Clear')
    with right_column:
        st.markdown(
        "<style>div.stButton > button { width: 100%; text-align: center; }</style>", 
        unsafe_allow_html=True
        )
        st.button('GO!')


st.divider()
st.markdown("<h3>Data Visualization</h3>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["Line Graph", "Bar Graph", "Table"])

st.divider()














# Add histogram data
x1 = np.random.randn(200) - 2
x2 = np.random.randn(200)
x3 = np.random.randn(200) + 2

# Group data together
hist_data = [x1, x2, x3]

group_labels = ['Group 1', 'Group 2', 'Group 3']

# Create distplot with custom bin_size
fig = ff.create_distplot(
        hist_data, group_labels, bin_size=[.1, .25, .5])

# Plot!
st.plotly_chart(fig, use_container_width=True)


df = px.data.gapminder()

fig = px.scatter(
    df.query("year==2007"),
    x="gdpPercap",
    y="lifeExp",
    size="pop",
    color="continent",
    hover_name="country",
    log_x=True,
    size_max=60,
)

tab1, tab2, tab3 = st.tabs(["Line Graph", "Bar Graph", "Table"])
with tab1:
    # Line graph.
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
with tab2:
    # Bar graph or table in another tab.
    st.plotly_chart(fig, theme=None, use_container_width=True)
with tab3:
    # Bar graph or table in another tab.
    st.plotly_chart(fig, theme=None, use_container_width=True)



#------ Example with line graph, more grpahs as tabs
# df = px.data.gapminder()

# fig = px.scatter(
#     df.query("year==2007"),
#     x="gdpPercap",
#     y="lifeExp",
#     size="pop",
#     color="continent",
#     hover_name="country",
#     log_x=True,
#     size_max=60,
# )

# tab1, tab2 = st.tabs(["Line Graph", "Plotly native theme"])
# with tab1:
#     # Line graph.
#     st.plotly_chart(fig, theme="streamlit", use_container_width=True)
# with tab2:
#     # Use the native Plotly theme.
#     st.plotly_chart(fig, theme=None, use_container_width=True)






# if st.checkbox('Show dataframe'):
#     chart_data = pd.DataFrame(
#        np.random.randn(20, 3),
#        columns=['a', 'b', 'c'])

#     chart_data









# #Add a selectbox to the sidebar:
# add_selectbox = st.sidebar.selectbox(
#     'How would you like to be contacted?',
#     ('Email', 'Home phone', 'Mobile phone')
# )









