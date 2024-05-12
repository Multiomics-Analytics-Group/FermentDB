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

# from pyArango.connection import *

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
        st.write(f"Connected to database '{st.session_state.db.name}' as {st.session_state.db.username}.")

    return st.session_state.db

def get_aql():
    return connect_to_db().aql


## 4. Streamlit UI
st.set_page_config(
    page_title="FermentDB",
    page_icon="👋" # Favicon 
)

aql = get_aql()

st.title('FermentDB')
st.subheader('A Database for High-cell Density Fermentations')



# cursor = aql.execute( '''
#      FOR doc IN Country
#     RETURN doc.name
#                       ''')

# result = []
# for item in cursor:
#    if item == "DK":
#     result.append(item)


# st.write(result)

if st.button("View Node Collections"):
   nodes = connect_to_db().graph('fermentdb').vertex_collections()
   st.write(nodes)
          
if st.button("View Edge Collections"):
   edges = connect_to_db().graph('fermentdb').edge_definitions()
   st.write(edges)

# st.title('FermentDB')
# st.header('FermentDB')
# st.subheader('A Database for...')

## 5. Query data from ArangoDB

# result = collection.fetchAll()
# for doc in result:
#     st.write(doc)

# How it worked before for database connection
# st.cache_resource

# st.write("text")
# st.markdown(
#     """
#     Text
#     """
# )


# # st.plotly_chart(figure_or_data, use_container_width=False, sharing="streamlit", theme="None", **kwargs)


# # Add histogram data
# x1 = np.random.randn(200) - 2
# x2 = np.random.randn(200)
# x3 = np.random.randn(200) + 2

# # Group data together
# hist_data = [x1, x2, x3]

# group_labels = ['Group 1', 'Group 2', 'Group 3']

# # Create distplot with custom bin_size
# fig = ff.create_distplot(
#         hist_data, group_labels, bin_size=[.1, .25, .5])

# # Plot!
# st.plotly_chart(fig, use_container_width=True)


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

# tab1, tab2 = st.tabs(["Streamlit theme (default)", "Plotly native theme"])
# with tab1:
#     # Use the Streamlit theme.
#     # This is the default. So you can also omit the theme argument.
#     st.plotly_chart(fig, theme="streamlit", use_container_width=True)
# with tab2:
#     # Use the native Plotly theme.
#     st.plotly_chart(fig, theme=None, use_container_width=True)






# # if st.checkbox('Show dataframe'):
# #     chart_data = pd.DataFrame(
# #        np.random.randn(20, 3),
# #        columns=['a', 'b', 'c'])

# #     chart_data

# # df = pd.DataFrame({
# #     'first column': [1, 2, 3, 4],
# #     'second column': [10, 20, 30, 40]
# #     })

# # option = st.selectbox(
# #     'Which number do you like best?',
# #      df['first column'])

# # 'You selected: ', option
# # Add a selectbox to the sidebar:
# add_selectbox = st.sidebar.selectbox(
#     'How would you like to be contacted?',
#     ('Email', 'Home phone', 'Mobile phone')
# )

# # Add a slider to the sidebar:
# add_slider = st.sidebar.slider(
#     'Select a range of values',
#     0.0, 100.0, (25.0, 75.0)
# )

# left_column, right_column = st.columns(2)
# # You can use a column just like st.sidebar:
# left_column.button('Press me!')

# # Or even better, call Streamlit functions inside a "with" block:
# with right_column:
#     chosen = st.radio(
#         'Sorting hat',
#         ("Gryffindor", "Ravenclaw", "Hufflepuff", "Slytherin"))
#     st.write(f"You are in {chosen} house!")


# # @st.cache_data
# # def data_loading_function(param1, param2):
# #     return …


# if "strain" not in st.session_state:
#     st.session_state.strain = 0

# st.write(f"Selected options: strain = {st.session_state.strain}.")
