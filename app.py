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
from datetime import datetime
import hashlib
from collections import Counter

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

if 'clicked' not in st.session_state:
    st.session_state.clicked = False

def click_GO():
    st.session_state.clicked = True

# ------- Statistical Section ----------- #

st.header('FermentDB', divider='grey')

st.markdown("<h1 style='text-align: center; font-size: 30px;'>Welcome to <span style= 'font-size: 40px;'>FermentDB</span></h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center;'>A Database for High-cell Density Fermentations</h5>", unsafe_allow_html=True)
st.write("")
st.write("")
st.write("")

left_column, middle_column, right_column = st.columns(3)

strains_sum = len(get_doc('Strain'))
runs_sum = len(get_doc('Run'))
pcond_sum = len(get_doc('Process_condition'))

with left_column:

    df = pd.DataFrame(query_sum_strains_from_db()) 
    fig = px.pie(df, values='count', names='strain', color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(showlegend=False,
                      width=175,
                      height=175,
                      margin=dict(l=1,r=1,b=1,t=1))

    fig.update_traces(marker=dict(line=dict(color='#000000', width=2)))
    
    st.plotly_chart(fig, theme='streamlit', use_container_width=False)
    st.markdown(f"<p style='text-align: left; padding-left: 60px'> {strains_sum} Strains <p>", unsafe_allow_html=True)

with middle_column:
    df = pd.DataFrame(query_sum_runs_from_db()) 
    fig = px.pie(df, values='count', names='run', color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(showlegend=False,
                      width=175,
                      height=175,
                      margin=dict(l=1,r=1,b=1,t=1))
    fig.update_traces(marker=dict(line=dict(color='#000000', width=2)),
                      textposition='none') # or inside
    
    st.plotly_chart(fig, theme='streamlit', use_container_width=False)
    st.markdown(f"<p style='text-align: left; padding-left: 60px'> {runs_sum} Runs <p>", unsafe_allow_html=True)

with right_column:
    df = pd.DataFrame(query_sum_pconditions_from_db()) 
    fig = px.pie(df, values='count', names='process_condition', color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(showlegend=False,
                    #   width=400,
                    #   height=400,
                      width=175,
                      height=175,
                      margin=dict(l=1,r=1,b=1,t=1))
    fig.update_traces(marker=dict(line=dict(color='#000000', width=2)),
                      textposition='none') # or inside
    
    st.plotly_chart(fig, theme='streamlit', use_container_width=False)
    st.markdown(f"<p style='text-align: left; padding-left: 30px'> {pcond_sum} Process Conditions <p>", unsafe_allow_html=True)
    st.write("")
    st.markdown("<p style='text-align: right;font-size: 12px'> Version 1.0 released on June 18th, 2024<p>", unsafe_allow_html=True)





st.divider()

# ------- Explore Section ----------- #

# Define variables 
if "strain" not in st.session_state:
    st.session_state.strain = ""
if "ferm_type" not in st.session_state:
    st.session_state.ferm_type = ""
if "pcondition" not in st.session_state:
    st.session_state.pcondition = ""



st.markdown("<h3 style='text-align: center;'>Explore Fermentations</h3>", unsafe_allow_html=True)

st.markdown("<p style='text-align: center;'>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. </p>", unsafe_allow_html=True)
st.write("")
st.write("")
st.write("")

left_column, middle_column, right_column = st.columns(3)

with left_column:
    st.session_state.strain = st.selectbox(
        'Strain:',
        get_doc('Strain'),
        placeholder="Choose a strain")

    'Strain: ', st.session_state.strain
with right_column:
    st.session_state.pcondition = st.selectbox(
        'Process condition:',
        get_doc('Process_condition'),
        placeholder='Choose a condition')

    'Process condition: ', st.session_state.pcondition

with middle_column:
    st.selectbox(
        'Fermenter Type:',
        get_doc('Fermenter'),
        placeholder='Choose a fermenter')

    'Fermenter Type: ', st.session_state.ferm_type
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
        st.button('GO!', on_click=click_GO)


if st.session_state.clicked:
    st.divider()
    st.markdown("<h3>Data Visualization</h3>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Line Graph", "Bar Graph", "Table"])
    with tab1:
        plot_condition(strain="HMP3427-012", pcondition=["D-glucose"], fermenter="AMBR 250")


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

st.divider()



















