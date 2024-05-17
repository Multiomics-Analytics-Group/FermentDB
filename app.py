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
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import hashlib
from collections import Counter

from arango import ArangoClient
from streamlit_arango.config import Config
from streamlit import session_state as ss


with open('style.css') as f:
    css = f.read()


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
    if 'aql' not in st.session_state:
        st.session_state.aql = connect_to_db().aql
    return st.session_state.aql


## 4. Streamlit UI

# Page confing
page_icon = "./assets/images/page_icon.png"

st.set_page_config(
    page_title="FermentDB",
    page_icon=page_icon # Favicon 
)


# 4.1 Query data from ArangoDB

def get_doc(collection):
    '''
    Retrieve docuents for a given collection
    
    parameters:
        collection (dict): dictionary structure 

    return:
        result: list of documents in the choosen collection. 
    '''

    cursor = get_aql().execute( f'''
        FOR doc IN {collection}
        RETURN doc.name
    ''')

    result = set()
    for item in cursor:
        result.add(item)
    
    return list(result)

def get_strain_batch():
    cursor = get_aql().execute('''
                               
        FOR doc IN Run
            RETURN doc.strain_batch                           
    ''')
    
    result = set()
    for item in cursor:
        result.add(item)
    return result

def get_container_type():
    cursor = get_aql().execute('''
                               
        FOR doc IN Run
            RETURN doc.container_type                           
    ''')
    
    result = set()
    for item in cursor:
        result.add(item)
    return result

def query_sum_strains_from_db():
    cursor = get_aql().execute('''
                               
        FOR doc IN Run
            FOR v, e IN 1..1 OUTBOUND doc cultures_strain
                COLLECT strain = e.strain_batch WITH COUNT INTO counter 
                RETURN { strain: strain, count: counter}                          
    ''')
    
    result = []
    for item in cursor:
        result.append(item)
    print(result)
    return result

def query_sum_runs_from_db():
    cursor = get_aql().execute('''
                               
        FOR doc IN Run
            COLLECT run = doc.name WITH COUNT INTO counter 
                RETURN { run: run, count: counter}                          
    ''')
    
    result = []
    for item in cursor:
        result.append(item)
    print(result)
    return result

def get_hash(key, prefix=""):
    hkey = str(int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
    hkey = f"{prefix}{hkey}"
    
    return hkey

def query_sum_pconditions_from_db():
    cursor = get_aql().execute('''
        FOR doc IN Run
            FOR v, e IN 1..1 OUTBOUND doc has_condition
                LET pcondition = SPLIT(e._to, '/')[1] //Extract part after "/"
                COLLECT pcondition_hash = e._to WITH COUNT INTO counter 
                RETURN { process_condition: pcondition_hash, count: counter}                          
    ''')
    
    result = []
    for item in cursor:
        pcondition_hash = item['process_condition']
        pcondition_name = get_hash(pcondition_hash, "C")
        item['process_condition'] = pcondition_name
        result.append(item)
    return result

def get_condition_data(strain, condition, fermenter):
    condition = [f"Process_condition/{get_hash(c, prefix='C')}" for c in condition]
    
    query = '''FOR doc IN Run
      FILTER doc.strain_batch == @val AND doc.container_type == @fermenter
      FOR v, e IN 1..1 OUTBOUND doc has_condition
        FILTER e._to IN @condition
        RETURN { source: doc, target: v, edge: e }
    '''
                   
    cursor = get_aql().execute(query,bind_vars={'val': strain,
                              'condition': condition, 'fermenter': fermenter})

    
    result = [doc for doc in cursor]

    print(result)

    return result

def plot_condition(strain, pcondition, fermenter ):
    result = get_condition_data(strain, pcondition, fermenter)
    rows = []
    for r in result:
        source = r['source']['_key']
        target = r['target']['name']
        data = r['edge']['data']
        timestamps = r['edge']['timestamps']
        rows.append(pd.DataFrame({'run': source, 'data':data, 'time': timestamps, 'condition': target}))
    
    df = pd.concat(rows)
    df['time'] = df['time'].apply(lambda t: datetime.fromtimestamp(t))
    df = df.sort_values(by="time")
    fig = px.line(df, x="time", y="data", color='run', line_dash='condition')
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


if 'go_clicked' not in st.session_state:
    st.session_state.go_clicked = False

def click_go():
    st.session_state.go_clicked = True

if 'clear' not in st.session_state:
    st.session_state.clear_clicked = False



def plot_condition_table(strain, pcondition, fermenter ):
    result = get_condition_data(strain, pcondition, fermenter)
    rows = []
    for r in result:
        source = r['source']['_key']
        strain = r['source']['strain_batch']
        fermenter = r['source']['container_type']
        target = r['target']['name']
        data = r['edge']['data']
        timestamps = r['edge']['timestamps']
        rows.append(pd.DataFrame({'run': source,'strain': strain, 'fermenter': fermenter, 'condition': target, 'data': data, 'time': timestamps}))
    
    df = pd.concat(rows, ignore_index=True)
    df['time'] = df['time'].apply(lambda t: datetime.fromtimestamp(t))
    df = df.sort_values(by="time")

    # df = df.drop_duplicates(subset=['run', 'strain', 'fermenter', 'condition']) # unique values
    
    table_data = df[['run', 'strain', 'fermenter', 'condition', 'data', 'time']] # Prepare data for table


    fig = go.Figure(data=[go.Table(
        header=dict(values=list(table_data.columns),
                    fill_color='grey',
                    align='center'),
        cells=dict(values=[table_data['run'], table_data['strain'], table_data['fermenter'], table_data['condition'], table_data['data'], table_data['time'] ],
                   align='center'))
    ])
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


# Icicle Chart:

# def get_icicle_data():
                   
@st.cache_data
def get_icicle_chart():
    # Fermenter, Species, Strain, Condition type
    query = '''FOR doc IN Run
      FILTER doc.strain_batch == @val AND doc.container_type == @fermenter
      FOR v, e IN 1..1 OUTBOUND doc has_condition
        FILTER e._to IN @condition
        RETURN { source: doc, target: v, edge: e }
    '''
        
    cursor = get_aql().execute(query)

    
    result = [doc for doc in cursor]

        
    # result = get_icicle_data()
    # rows = []
    # for r in result:
    #     node_ids = r['source']['_key']
    #     node_name = r['target']['name']
    #     parent_node = r['edge']['data']
    #     rows.append(pd.DataFrame({'ids': node_ids, 'labels':node_name, 'parents': parent_node}))
    
    # df = pd.concat(rows)

    df = px.data.gapminder().query("year == 2007")

    fig = px.icicle(df, path=[px.Constant("species"), 'strains', 'runs'], values='pop',
                   color='lifeExp', hover_data=['iso_alpha'],
                      color_continuous_scale='RdBu',
                      color_continuous_midpoint=np.average(df['lifeExp'], weights=df['pop']))


    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, theme="streamlit")




###############################################
### --------- Statistical Section --------- ###
###############################################
st.header('FermentDB', divider='grey')

st.markdown("<h1 style='text-align: center; font-size: 30px;'>Welcome to <span style= 'font-size: 40px;'>FermentDB</span></h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; margin-bottom: 50px'>A Database for High-cell Density Fermentations</h5>", unsafe_allow_html=True)

ss

@st.cache_data
def get_chart_79899895():
    import plotly.express as px
    import numpy as np
    df = px.data.gapminder().query("year == 2007")
    fig = px.icicle(df, path=[px.Constant("world"), 'continent', 'country'], values='pop',
                      color='lifeExp', hover_data=['iso_alpha'],
                      color_continuous_scale='RdBu',
                      color_continuous_midpoint=np.average(df['lifeExp'], weights=df['pop']))
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

    st.plotly_chart(fig, theme="streamlit")

get_chart_79899895()



# left_column, right_column = st.columns(2)

# strains_sum = len(get_doc('Strain'))
# runs_sum = len(get_doc('Run'))
# pcond_sum = len(get_doc('Process_condition'))

# with left_column:

#     df = pd.DataFrame(query_sum_strains_from_db()) 
#     fig = px.pie(df, values='count', names='strain', color_discrete_sequence=px.colors.sequential.RdBu)
#     fig.update_layout(showlegend=False,
#                       width=175,
#                       height=175,
#                       margin=dict(l=1,r=1,b=1,t=1))

#     fig.update_traces(marker=dict(line=dict(color='#000000', width=2)))
    
#     st.plotly_chart(fig, theme='streamlit', use_container_width=True)

#     st.markdown(f"<p style='text-align: center;'> {strains_sum} Strains <p>", unsafe_allow_html=True)

# with right_column:
#     df = pd.DataFrame(query_sum_runs_from_db()) 
#     fig = px.pie(df, values='count', names='run', color_discrete_sequence=px.colors.sequential.RdBu)
#     fig.update_layout(showlegend=False,
#                       width=175,
#                       height=175,
#                       margin=dict(l=1,r=1,b=1,t=1))
#     fig.update_traces(marker=dict(line=dict(color='#000000', width=2)),
#                       textposition='none') # or inside
    
#     st.plotly_chart(fig, theme='streamlit', use_container_width=True)
#     st.markdown(f"<p style='text-align: center;'> {runs_sum} Runs <p>", unsafe_allow_html=True)

# with right_column:
#     df = pd.DataFrame(query_sum_pconditions_from_db()) 
#     fig = px.pie(df, values='count', names='process_condition', color_discrete_sequence=px.colors.sequential.RdBu)
#     fig.update_layout(showlegend=False,
#                     #   width=400,
#                     #   height=400,
#                       width=175,
#                       height=175,
#                       margin=dict(l=1,r=1,b=1,t=1))
#     fig.update_traces(marker=dict(line=dict(color='#000000', width=2)),
#                       textposition='none') # or inside
    
#     st.plotly_chart(fig, theme='streamlit', use_container_width=False)
st.markdown(f"<p style='text-align: left; padding-left: 30px'> Strains, Runs and Process Conditions <p>", unsafe_allow_html=True)
#     st.write("")
st.markdown("<p style='text-align: right;font-size: 12px'> Version 1.0 released on June 18th, 2024<p>", unsafe_allow_html=True)





###############################################
### ----------- Explore Section ----------- ###
###############################################
st.divider()

# Initialize variables
ss.strain_disabled = True
ss.ferm_disabled = True
ss.cultivation_disabled = True
ss.pcond_disabled = True


    
st.markdown("<h3 style='text-align: center;'>Explore Fermentations</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Dive into the depths of FermentDB's comprehensive data to cross-reference multiple fermentation experiments at once </p>", unsafe_allow_html=True)

st.write("")
st.write("")
st.markdown("<p style='text-align: left;'>Select organism of interest: </p>", unsafe_allow_html=True)

left_column, right_column = st.columns(2)
with left_column:
    st.selectbox(
        'Species: ',
        get_doc('Species'),
        key = "sb_species",
        index=None,
        placeholder="Choose species",
        help = "Select the type of microorganism you wish to study")

if ss. sb_species is not None:
    ss.strain_disabled = False


with right_column:
    st.selectbox(
        'Strain:',
        get_strain_batch(),
        key = "sb_strain",
        index=None,
        placeholder="Choose strain",
        disabled = ss.strain_disabled,
        help = "Select a specific strain of your chosen organism. Each strain has unique characteristics and applications")

if ss.sb_strain is not None:
    ss.ferm_disabled = False

st.write("")
st.write("")
st.markdown("<p style='text-align: left;'>Select Fermenter: </p>", unsafe_allow_html=True)

left_column, right_column = st.columns(2)
with left_column:
    st.selectbox(
        'Fermenter type:',
        get_container_type(),
        key = 'sb_fermenter_type',
        index=None,
        placeholder='Choose fermenter',
        disabled = ss.ferm_disabled,
        help = "Select a specific fermenter type.")

if ss.sb_fermenter_type is not None:
    ss.cultivation_disabled = False

with right_column:
    st.selectbox(
        'Cultivation Type:',
        ("Fed-Batch",),
        key = 'sb_cultivationtype',
        index=None,
        placeholder="Choose cultivation type",
        disabled = ss.cultivation_disabled,
        help = "Select a specific cultivation type of your fermenter")

if ss.sb_cultivationtype is not None:
    ss.pcond_disabled = False

st.write("")
st.write("")
st.markdown("<p style='text-align: left;'> Select Condition of Interest: </p>", unsafe_allow_html=True)

left_column, right_column = st.columns(2)
with left_column:
    st.selectbox(
        'Bioprocess Condition:',
        get_doc('Process_condition'),
        key = 'sb_pcondition',
        index=None,
        placeholder='Choose condition',
        disabled = ss.pcond_disabled,
        help = "Select the specific process condition")
    
left_column, middle_column, right_column = st.columns(3)
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
# st.markdown(
#     """
#     <style>
#     .stButton {
#         display: flex;
#         justify-content: center;
#         margin-top: 50px;
#     }
#     .stButton > button {
#         padding: 10px 40px; /* Adjust padding as needed */
#     }
#     </style>
#     """, 
#     unsafe_allow_html=True
# )


with middle_column:    
    st.button('GO!', on_click=click_go)

if ss.go_clicked:
    st.divider()
    st.markdown("<h5>Fermentation Data Visualization</h5>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Line Graph", "Table"])
    with tab1:
        plot_condition(strain=ss.sb_strain, pcondition=[ss.sb_pcondition], fermenter= ss.sb_fermenter_type)


    # # Store the original key in the dictionary using the hash as the key
    # hash_to_key={}
    # hash_to_key[hkey] = key
    

def get_condition_data(strain, condition):
    condition = [f"Process_condition/{get_hash(c, prefix='C')}" for c in condition]
    
    query = '''FOR doc IN Run
      FILTER doc.strain_batch == @val AND doc.container_type == "AMBR 250"
      FOR v, e IN 1..1 OUTBOUND doc has_condition
        FILTER e._to == @condition
        RETURN { source: doc, target: v, edge: e }
    '''
                   
    cursor = get_aql().execute(query,bind_vars={'val': strain,
                              'condition':condition})

    
    result = [doc for doc in cursor]

    print(result)

    return result

get_condition_data(strain="Strain1", condition=["D-glucose"])


tab1, tab2, tab3 = st.tabs(["Line Graph", "Bar Graph", "Table"])
with tab1:
    plot_condition(strain="Strain1", pcondition=["D-glucose"], fermenter="AMBR 250")
# with tab2:
#     # Bar graph or table in another tab.
#     st.plotly_chart(fig, theme=None, use_container_width=True)
# with tab3:
#     # Bar graph or table in another tab.
#     st.plotly_chart(fig, theme=None, use_container_width=True)
    with tab2:
        plot_condition_table(strain= ss.sb_strain, pcondition=[ss.sb_pcondition], fermenter= ss.sb_fermenter_type)


###############################################
### ------ iModulon Explore Section ------- ###
###############################################
st.divider()

st.markdown("<h3 style='text-align: center;'> Explore iModulons </h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'> Dive deep into the science of iModulons and high-cell density fermentations </p>", unsafe_allow_html=True)


ss
















