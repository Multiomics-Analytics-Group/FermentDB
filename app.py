''' FermentDB Streamlit App '''

# - - - - - - - - - - - IMPORT MODULES - - - - - - - - - - - - - - - - - 

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as pxl
from datetime import datetime
import hashlib
import time

from arango import ArangoClient
from streamlit_arango.config import Config
from streamlit import session_state as ss
from streamlit_d3graph import d3graph
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb
from streamlit_navigation_bar import st_navbar
import pages as pg




st.set_page_config(page_title="FermentDB",page_icon="./assets/images/fermenter_graph_logo.jpg", initial_sidebar_state="collapsed")
# - - - - - - - - - - - - - - - CSS CODE FOR CUSTOMIZATION - - - - - - - - - - - - -

with open('style.css', "r") as file:
    style_css = file.read()

st.markdown(f'<style>{style_css}</style>', unsafe_allow_html=True)

# - - - - - - - - - - - - - - - CONNECT TO ARANGODB - - - - - - - - - - - - - 

# Initialize the ArangoDB client. 
client = ArangoClient(hosts=Config.ArangoDB.host)

# Initialize connection to database: "fermentdb" as root user
@st.cache_resource
def get_database_session():
    if 'db' not in ss:
        ss.db = client.db(
            name = Config.ArangoDB.database,
            username = Config.ArangoDB.username,
            password = Config.ArangoDB.password
    )
    return ss.db

@st.cache_resource
def get_aql():
    if 'aql' not in ss:
        ss.aql = get_database_session().aql
    return ss.aql


# - - - - - - - - - - - - - - - - - - QUERY DATA FROM ARANGODB - - - - - - - - - - - - 

#### ------ STATISTICS SECTION -------- ####

@st.cache_data(show_spinner=False)
def get_num_node_documents():
    vertex_collections = get_database_session().graph('fermentdb').vertex_collections()
    total_nodes = 0

    for collection_name in vertex_collections:
        collection = get_database_session().collection(collection_name)
        total_nodes += collection.count()

    return total_nodes

@st.cache_data(show_spinner=False)
def get_num_edge_documents():
    edge_definitions = get_database_session().graph('fermentdb').edge_definitions()
    total_edges = 0

    for edge_def in edge_definitions:
        collection_name = edge_def['edge_collection']
        collection = get_database_session().collection(collection_name)
        total_edges += collection.count()
    
    return total_edges

@st.cache_data(show_spinner=False)
def get_icicle_chart():
    # time.sleep(4)
    #filter im_v with major im_e values
    query = """
        LET im_counts = (
            FOR doc IN Run
                FOR im_v, im_e IN 1..1 OUTBOUND doc has_measured_imodulon
                    COLLECT im = im_v.name WITH COUNT INTO num_im
                    RETURN { im, num_im }
        )
        FOR doc IN Run
            FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
                FOR species_v, species_e IN 1..1 OUTBOUND strain_v belongs_to
                    FOR im_v, im_e IN 1..1 OUTBOUND doc has_measured_imodulon
                        LET major_im = (
                            FOR item IN im_counts
                                FILTER item.num_im >= 7  
                                RETURN item.im
                        )
                        FILTER im_v.name IN major_im
                        COLLECT species = species_v.name, strains = strain_v.name, im = im_v.name
                        AGGREGATE im_value = COUNT(im_e)
                        RETURN { species: species, strains: strains, im: im, im_edges: im_value }
    """
    cursor = get_aql().execute(query)
    result = [doc for doc in cursor] 
    # print(f"Result icicle: {result}")  
    df = pd.DataFrame(result)


    fig = pxl.icicle(df, path=[pxl.Constant("AMBR 250"), 'species', 'strains' ], values='im_edges',
                   color='im_edges', hover_data=['im_edges'],
                    color_continuous_scale='RdBu',
                    range_color=[5, 5.3],
                    color_continuous_midpoint=np.average(df['im_edges'], weights=df['im_edges']))
    fig.update_layout(margin = dict(t=50, l=75, r=40, b=50),
                      autosize=True,
                      title={
                        'text': "Summary of Strains with Major iModulon Activities",
                        'y': 0.08,
                        'x': 0.42,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    })

    st.plotly_chart(fig, theme="streamlit")
# Made with pcond+iModulon
# def get_icicle_chart():
#     # time.sleep(4)
#     #filter pcond_v with major pcond_e values
#     query = """
#         LET pcond_counts = (
#             FOR doc IN Run
#                 FOR pcond_v, pcond_e IN 1..1 OUTBOUND doc has_condition
#                     COLLECT pcond = pcond_v.name WITH COUNT INTO num_pcond
#                     RETURN { pcond, num_pcond }
#         )
#         FOR doc IN Run
#             FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
#                 FOR species_v, species_e IN 1..1 OUTBOUND strain_v belongs_to
#                     FOR pcond_v, pcond_e IN 1..1 OUTBOUND doc has_condition
#                         LET major_pcond = (
#                             FOR item IN pcond_counts
#                                 FILTER item.num_pcond >= 10  
#                                 RETURN item.pcond
#                         )
#                         FILTER pcond_v.name IN major_pcond
#                         COLLECT species = species_v.name, strains = strain_v.name, pcond = pcond_v.name
#                         AGGREGATE pcond_value = COUNT(pcond_e)
#                         RETURN { species: species, strains: strains, pcond: pcond, pcondition_edges: pcond_value }
#     """
#     cursor = get_aql().execute(query)
#     result = [doc for doc in cursor] 
#     # print(f"Result icicle: {result}")  
#     df = pd.DataFrame(result)


#     fig = px.icicle(df, path=[px.Constant("AMBR 250"), 'species', 'strains' ], values='pcondition_edges',
#                    color='pcondition_edges', hover_data=['pcondition_edges'],
#                     color_continuous_scale='RdBu',
#                     range_color=[5, 5.3],
#                     color_continuous_midpoint=np.average(df['pcondition_edges'], weights=df['pcondition_edges']))
#     fig.update_layout(margin = dict(t=50, l=75, r=40, b=50),
#                       autosize=True,
#                       title={
#                         'text': "Summary of Strains with Major Process Condition Interactions",
#                         'y': 0.08,
#                         'x': 0.42,
#                         'xanchor': 'center',
#                         'yanchor': 'top'
#                     })

#     st.plotly_chart(fig, theme="streamlit")

# @st.cache_data(show_spinner=False)
# def get_icicle_chart():
#     # time.sleep(4)
#     query = """
#         FOR doc IN Run
#                 FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
#                     FOR species_v, species_e IN 1..1 OUTBOUND strain_v belongs_to
#                         FOR pcond_v, pcond_e IN 1..1 OUTBOUND doc has_condition
#                         COLLECT species = species_v.name, strains = strain_v.name, pcond = pcond_v.name
#                         AGGREGATE pcond_value = COUNT(pcond_e)
#                         RETURN { species: species, strains: strains, pcond: pcond, pcondition_edges: pcond_value  }  
#     """
#     cursor = get_aql().execute(query)
#     result = [doc for doc in cursor] 
#     print(f"Result icicle: {result}")  
#     df = pd.DataFrame(result)


#     fig = px.icicle(df, path=[px.Constant("AMBR 250"), 'species', 'strains'], values='pcondition_edges',
#                    color='pcondition_edges', hover_data=['pcondition_edges'],
#                     color_continuous_scale='RdBu',
#                     range_color=[5, 5.3],
#                     color_continuous_midpoint=np.average(df['pcondition_edges'], weights=df['pcondition_edges']))
#     fig.update_layout(margin = dict(t=50, l=75, r=50, b=50),
#                       autosize=True,
#                       title={
#                         'text': "Summary of Process Conditions per Strain",
#                         'y': 0.08,
#                         'x': 0.33,
#                         'xanchor': 'center',
#                         'yanchor': 'top'
#                     })

#     st.plotly_chart(fig, theme="streamlit")

@st.cache_data
def get_doc_count(collection):
    cursor = get_aql().execute( f'''
        FOR doc IN {collection}
        RETURN doc.name
    ''')
    result = []
    for item in cursor:
        result.append(item)
    return len(result)

@st.cache_data(show_spinner=False)
def graph_statistics():
    time.sleep(1)
    st.write('Database Statistics:' )
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown(f"<p class='statistic'> {get_num_node_documents()} nodes <p>", unsafe_allow_html=True)
    col2.markdown(f"<p class='statistic'> {get_num_edge_documents()} edges <p>", unsafe_allow_html=True)
    col3.markdown(f"<p class='statistic'> {get_doc_count('Run')} Runs <p>", unsafe_allow_html=True)
    col4.markdown(f"<p class='statistic'> {get_doc_count('Process_condition')} process condition <p>", unsafe_allow_html=True)
    col5.markdown(f"<p class='statistic'> {get_doc_count('Initial_condition')} initial conditions <p>", unsafe_allow_html=True)
        
    st.markdown("<p style='text-align: right;font-size: 12px'> Version 1.0 released on June 18th, 2024 <p>", unsafe_allow_html=True)

def load_statistics_data():
    with st.spinner('Loading data...'):
        get_num_node_documents()
        get_num_edge_documents()
        with st.container():
            st.markdown('<div class="icicle_centered">', unsafe_allow_html=True)
            get_icicle_chart()
            st.markdown('</div>', unsafe_allow_html=True)
        graph_statistics()

#### ------ BIOPROCESS CONDITION EXPLORE SECTION -------- ####

def get_doc_name(collection):

    cursor = get_aql().execute( f'''
        FOR doc IN {collection}
        RETURN doc.name
    ''')

    result = []
    for item in cursor:
        result.append(item)
    return result

def get_hash(key, prefix=""):
    hkey = ""
    if key is not None:
        hkey = str(int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
        hkey = f"{prefix}{hkey}"
    return hkey

def get_strains(species):
    # species = [f"Species/{get_hash(s, prefix='SP')}" for s in species]
    species = [f"Species/{get_hash(species, prefix='SP')}"]
    
    query= """
        FOR doc IN Strain
            FOR v, e IN 1..1 OUTBOUND doc belongs_to
                FILTER e._to IN @species
                RETURN doc.name
    """

    cursor = get_aql().execute(query, bind_vars={'species': species})
    
    result = [doc for doc in cursor]
    return result

def get_fermenter_type(strains):
    # strains = [f"Strain/{get_hash(s, prefix='ST')}" for s in strains]
    strains = [f"Strain/{get_hash(strains, prefix='ST')}"]

    query = """
        FOR doc IN Run
            FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
                FILTER strain_e._to IN @strains
                    FOR fermenter_v, fermenter_e IN 1..1 OUTBOUND doc uses_fermenter
                    RETURN fermenter_v.name
    """

    cursor = get_aql().execute(query, bind_vars={'strains': strains})

    # result = [doc for doc in cursor]
    result = set()
    for item in cursor:
        result.add(item)
    return result

def get_pconditions(strains, fermenters):
    strains = [f"Strain/{get_hash(strains, prefix='ST')}"]
    fermenters = [f"Fermenter/{get_hash(fermenters, prefix='F')}"]
    # strains = [f"Strain/{get_hash(s, prefix='ST')}" for s in strains]
    # fermenters = [f"Fermenter/{get_hash(f, prefix='F')}" for f in fermenters]

    query = """
        FOR doc IN Run
            FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
                FILTER strain_e._to IN @strains
                FOR fermenter_v, fermenter_e IN 1..1 OUTBOUND doc uses_fermenter
                    FILTER fermenter_e._to IN @fermenters
                    FOR v, e IN 1..1 OUTBOUND doc has_condition
                        RETURN v.name
    """

    cursor = get_aql().execute(query, bind_vars={'strains': strains,
                                                 'fermenters': fermenters})
    
    result = [doc for doc in cursor]
    # result = set()
    # for item in cursor:
    #     result.add(item)
    return result


def get_pcondition_data(strains, conditions, fermenters):
    conditions = [f"Process_condition/{get_hash(conditions, prefix='C')}"]
    strains = [f"Strain/{get_hash(strains, prefix='ST')}"]
    fermenters = [f"Fermenter/{get_hash(fermenters, prefix='F')}"]
    # conditions = [f"Process_condition/{get_hash(c, prefix='C')}" for c in conditions]
    # strains = [f"Strain/{get_hash(s, prefix='S')}" for s in strains]
    # fermenters = [f"Fermenter/{get_hash(f, prefix='F')}" for f in fermenters]
    
    query = '''
        FOR doc IN Run
            FOR strain_vertex, strain_edge IN 1..1 OUTBOUND doc cultures_strain
                FILTER strain_edge._to IN @strains
                FOR fermenter_vertex, fermenter_edge IN 1..1 OUTBOUND doc uses_fermenter
                    FILTER fermenter_edge._to IN @fermenters
                    FOR v, e IN 1..1 OUTBOUND doc has_condition
                        FILTER e._to IN @conditions
                        RETURN { source: doc, fermenter: fermenter_vertex, strain: strain_vertex, target: v, edge: e}
    '''
    cursor = get_aql().execute(query, bind_vars={'strains': strains,
                                                'conditions': conditions, 
                                                'fermenters': fermenters})
    result = [doc for doc in cursor]
    return result

def plot_pcondition_chart(strain, pcondition, fermenter ):
    result = get_pcondition_data(strain, pcondition, fermenter)
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
    fig = pxl.line(df, x="time", y="data", color='run', line_dash='condition')
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

def plot_pcondition_table(strain, pcondition, fermenter ):
    result = get_pcondition_data(strain, pcondition, fermenter)
    data_dict = {}
    
    for r in result:
        source = r['source']['_key']
        strain = r['strain']['name']
        fermenter = r['fermenter']['name']
        target = r['target']['name']
        data = r['edge']['data']
        timestamps = r['edge']['timestamps']
        
        # Create a unique key for grouping
        key = (source, strain, fermenter, target)
        if key not in data_dict:
            data_dict[key] = {'data': [], 'timestamps': []}
        data_dict[key]['data'].extend(data)
        data_dict[key]['timestamps'].extend(timestamps)
    
    rows = []
    for (source, strain, fermenter, target), values in data_dict.items():
        sorted_pairs = sorted(zip(values['timestamps'], values['data']))
        sorted_timestamps, sorted_data = zip(*sorted_pairs)
    
        row = {
            'run': source,
            'strain': strain,
            'fermenter': fermenter,
            'condition': target,
            'data': list(sorted_data),
            'time': [datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S') for t in sorted_timestamps]
        }
        rows.append(row)
    df = pd.DataFrame(rows)

    # Convert lists to string with line breaks 
    df['data'] = df['data'].apply(lambda x: '<br>'.join(map(str, x)))
    df['time'] = df['time'].apply(lambda x: '<br>'.join(x))

    table_data = df[['run', 'strain', 'fermenter', 'condition', 'data', 'time']] # Prepare data for table
    # st.write(df)
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(table_data.columns),
                    fill_color='grey',
                    align='center'),
        cells=dict(values=[table_data['run'], table_data['strain'], table_data['fermenter'], table_data['condition'], table_data['data'], table_data['time'] ],
                   align='center', height=900))
    ])
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
def load_pcondition_exploration():
    # Initialize variables
    if 'strain_disabled' not in ss:
        ss.strain_disabled = True
    if 'ferm_disabled' not in ss:
        ss.ferm_disabled = True
    if 'cultivation_disabled' not in ss:
        ss.cultivation_disabled = True
    if 'pcond_disabled' not in ss:
        ss.pcond_disabled = True
    if 'display_data' not in ss:
        st.session_state.display_data = False

    st.markdown("<p style='text-align: left; margin-top: 30px'>Select organism of interest </p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.selectbox(
            'Species: ',
            get_doc_name('Species'),
            key = "sb_species",
            index= None,
            placeholder="Choose species",
            help = "Select the type of microorganism you wish to study")

    if ss.sb_species is not None:
        ss.strain_disabled = False
    
    col2.selectbox( # st.multiselect()
            'Strain:',
            get_strains(ss.sb_species),
            key = "sb_strain",
            index=None,
            placeholder="Choose strain",
            disabled = ss.strain_disabled,
            help = "Select a specific strain of your chosen organism. Each strain has unique characteristics and applications")

    if ss.sb_strain is not None:
        ss.ferm_disabled = False


    st.markdown("<p style='text-align: left; margin-top: 30px'>Select Fermenter </p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.selectbox(
            'Fermenter type:',
            get_fermenter_type(ss.sb_strain),
            key = "sb_fermenter_type",
            index=None,
            placeholder='Choose fermenter',
            disabled = ss.ferm_disabled,
            help = "Select a specific fermenter type.")

    if ss.sb_fermenter_type is not None:
        ss.cultivation_disabled = False

    col2.selectbox(
            'Cultivation Type:',
            ("Fed-Batch",),
            key = 'sb_cultivationtype',
            index=None,
            placeholder="Choose cultivation type",
            disabled = ss.cultivation_disabled,
            help = "Select a specific cultivation type of your fermenter")

    if ss.sb_cultivationtype is not None:
        ss.pcond_disabled = False
    
    st.markdown("<p style='text-align: left; margin-top: 30px'> Select Condition of Interest </p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.selectbox(
        'Process Condition:',
        get_pconditions(ss.sb_strain, ss.sb_fermenter_type),
        key = 'sb_pcondition',
        index=None,
        placeholder='Choose condition',
        disabled = ss.pcond_disabled,
        help = "Select the specific process condition")

    col1, col2, col3 = st.columns(3)   
    col2.button('GO!', on_click=click_go_button)

    if ss.display_data: 
        st.divider()
        st.markdown("<h5>Fermentation Data Visualization</h5>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Line Graph", "Table"])
        with tab1:
            plot_pcondition_chart(strain=ss.sb_strain, pcondition=ss.sb_pcondition, fermenter= ss.sb_fermenter_type)
        with tab2:
            plot_pcondition_table(strain= ss.sb_strain, pcondition=ss.sb_pcondition, fermenter= ss.sb_fermenter_type)

#### ------ iMODULON EXPLORE SECTION -------- ####
 
def get_imodulon(strains, fermenters):
    strains = [f"Strain/{get_hash(strains, prefix='ST')}"]
    fermenters = [f"Fermenter/{get_hash(fermenters, prefix='F')}"]
    # strains = [f"Strain/{get_hash(s, prefix='ST')}" for s in strains]
    # fermenters = [f"Fermenter/{get_hash(f, prefix='F')}" for f in fermenters]

    query = """
        FOR doc IN Run
            FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
                FILTER strain_e._to IN @strains
                FOR fermenter_v, fermenter_e IN 1..1 OUTBOUND doc uses_fermenter
                    FILTER fermenter_e._to IN @fermenters
                    FOR v, e IN 1..1 OUTBOUND doc has_measured_imodulon
                        RETURN v.name
    """

    cursor = get_aql().execute(query, bind_vars={'strains': strains,
                                                 'fermenters': fermenters})
    
    result = [doc for doc in cursor]
    # result = set()
    # for item in cursor:
    #     result.add(item)
    return result

def get_imodulon_data(strains, conditions, fermenters):
    imodulon = [f"iModulon/{get_hash(conditions, prefix='iM')}"]
    strains = [f"Strain/{get_hash(strains, prefix='ST')}"]
    fermenters = [f"Fermenter/{get_hash(fermenters, prefix='F')}"]
    # conditions = [f"Process_condition/{get_hash(c, prefix='C')}" for c in conditions]
    # strains = [f"Strain/{get_hash(s, prefix='S')}" for s in strains]
    # fermenters = [f"Fermenter/{get_hash(f, prefix='F')}" for f in fermenters]
    
    query = '''
        FOR doc IN Run
            FOR strain_vertex, strain_edge IN 1..1 OUTBOUND doc cultures_strain
                FILTER strain_edge._to IN @strains
                FOR fermenter_vertex, fermenter_edge IN 1..1 OUTBOUND doc uses_fermenter
                    FILTER fermenter_edge._to IN @fermenters
                    FOR v, e IN 1..1 OUTBOUND doc has_measured_imodulon
                        FILTER e._to IN @imodulon
                        RETURN { source: doc, fermenter: fermenter_vertex, strain: strain_vertex, target: v, edge: e}
    '''
    cursor = get_aql().execute(query, bind_vars={'strains': strains,
                                                'imodulon': imodulon, 
                                                'fermenters': fermenters})
    result = [doc for doc in cursor]
    return result
# get_pcondition_data("Strain1", "pH", "AMBR 250")


# TODO: 
def plot_imodulon_chart(strain, imodulon, fermenter ):
    result = get_imodulon_data(strain, imodulon, fermenter)
    rows = []
    for r in result:
        source = r['source']['_key']
        target = r['target']['name']
        data = r['edge']['data']
        timestamps = r['edge']['timestamps']
        rows.append(pd.DataFrame({'run': source, 'data':data, 'time': timestamps, 'iModulon': target}))
    
    df = pd.concat(rows)
    df['time'] = df['time'].apply(lambda t: datetime.fromtimestamp(t))
    df = df.sort_values(by="time")
    fig = pxl.line(df, x="time", y="data", color='run', line_dash='iModulon')
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


# TODO: 
def plot_imodulon_table(strain, imodulon, fermenter ):
    result = get_imodulon_data(strain, imodulon, fermenter)
    data_dict = {}
    
    for r in result:
        source = r['source']['_key']
        strain = r['strain']['name']
        fermenter = r['fermenter']['name']
        target = r['target']['name']
        data = r['edge']['data']
        timestamps = r['edge']['timestamps']
        
        # Create a unique key for grouping
        key = (source, strain, fermenter, target)
        if key not in data_dict:
            data_dict[key] = {'data': [], 'timestamps': []}
        data_dict[key]['data'].extend(data)
        data_dict[key]['timestamps'].extend(timestamps)
    
    rows = []
    for (source, strain, fermenter, target), values in data_dict.items():
        sorted_pairs = sorted(zip(values['timestamps'], values['data']))
        sorted_timestamps, sorted_data = zip(*sorted_pairs)
    
        row = {
            'run': source,
            'strain': strain,
            'fermenter': fermenter,
            'iModulon': target,
            'data': list(sorted_data),
            'time': [datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S') for t in sorted_timestamps]
        }
        rows.append(row)
    df = pd.DataFrame(rows)

    # Convert lists to string with line breaks 
    df['data'] = df['data'].apply(lambda x: '<br>'.join(map(str, x)))
    df['time'] = df['time'].apply(lambda x: '<br>'.join(x))

    table_data = df[['run', 'strain', 'fermenter', 'iModulon', 'data', 'time']] # Prepare data for table
    # st.write(df)
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(table_data.columns),
                    fill_color='grey',
                    align='center'),
        cells=dict(values=[table_data['run'], table_data['strain'], table_data['fermenter'], table_data['iModulon'], table_data['data'], table_data['time'] ],
                   align='center', height=900))
    ])
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

def click_go_button():
    ss.display_data = True

def click_im_button():
    ss.im_display_data = True


def load_imodulon_exploration():
    # Initialize variables
    if 'im_strain_disabled' not in ss:
        ss.im_strain_disabled = True
    if 'im_ferm_disabled' not in ss:
        ss.im_ferm_disabled = True
    if 'im_cultivation_disabled' not in ss:
        ss.im_cultivation_disabled = True
    if 'imodulon_disabled' not in ss:
        ss.imodulon_disabled = True
    if 'im_display_data' not in ss:
        ss.im_display_data = False

    st.markdown("<p style='text-align: left; margin-top: 30px'>Select organism of interest </p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.selectbox(
            'Species: ',
            get_doc_name('Species'),
            key = "sb_im_species",
            index= None,
            placeholder="Choose species",
            help = "Select the type of microorganism you wish to study")

    if ss.sb_im_species is not None:
        ss.im_strain_disabled = False
    
    col2.selectbox( # st.multiselect()
            'Strain:',
            get_strains(ss.sb_im_species),
            key = "sb_im_strain",
            index=None,
            placeholder="Choose strain",
            disabled = ss.im_strain_disabled,
            help = "Select a specific strain of your chosen organism. Each strain has unique characteristics and applications")

    if ss.sb_im_strain is not None:
        ss.im_ferm_disabled = False


    st.markdown("<p style='text-align: left; margin-top: 30px'>Select Fermenter </p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.selectbox(
            'Fermenter type:',
            get_fermenter_type(ss.sb_im_strain),
            key = "sb_im_fermenter_type",
            index=None,
            placeholder='Choose fermenter',
            disabled = ss.im_ferm_disabled,
            help = "Select a specific fermenter type.")

    if ss.sb_im_fermenter_type is not None:
        ss.im_cultivation_disabled = False

    col2.selectbox(
            'Cultivation Type:',
            ("Fed-Batch",),
            key = 'sb_im_cultivationtype',
            index=None,
            placeholder="Choose cultivation type",
            disabled = ss.im_cultivation_disabled,
            help = "Select a specific cultivation type of your fermenter")

    if ss.sb_im_cultivationtype is not None:
        ss.imodulon_disabled = False
    
    st.markdown("<p style='text-align: left; margin-top: 30px'> Select iModulon of Interest </p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.selectbox(
        'iModulon Activity:',
        get_imodulon(ss.sb_im_strain, ss.sb_im_fermenter_type),
        key = 'sb_imodulon',
        index=None,
        placeholder='Choose iModulon',
        disabled = ss.imodulon_disabled,
        help = "Select the specific iModulon activity to explore")

    col1, col2, col3 = st.columns(3)   
    col2.button('Search iModulon!', on_click=click_im_button)

    if ss.im_display_data: 
        st.divider()
        st.markdown("<h5>iModulonn Activity Visualization</h5>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Line Graph", "Table"])
        with tab1:
            plot_imodulon_chart(strain=ss.sb_im_strain, imodulon=ss.sb_imodulon, fermenter= ss.sb_im_fermenter_type)
        with tab2:
            plot_imodulon_table(strain= ss.sb_im_strain, imodulon=ss.sb_imodulon, fermenter= ss.sb_im_fermenter_type)

#### ------ FOOTER -------- ####

def image(src_as_string, **style):
    return img(src=src_as_string, style=styles(**style))

def link(link, text, **style):
    return a(_href=link, _target="_blank", style=styles(**style))(text)

def layout(*args):

    style = """
    <style>
    # MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
        .stApp { bottom: 75px; }
        </style>
        """

    style_div = styles(
        position="fixed",
        left=0,
        bottom=0,
        margin=px(0, 0, 0, 0),
        width=percent(100),
        color="black",
        text_align="left",
        # height=px(120),
        height=px(75), 
          # Set the desired height for the footer
        padding_top=px(35),  # Adjust padding to vertically center the text
        box_sizing="border-box", 
        opacity=1,
    )

    style_hr = styles(
        display="block",
        margin=px(0, 0, 0,0),
        padding_left=px(20),
        # margin=px(8, 8, "auto", "auto"),
        border_style="inset",
        border_width=px(2)
    )

    body = p()
    foot = div(
        style=style_div
    )(
        hr(
            style=style_hr
        ),
        body
    )

    st.markdown(style, unsafe_allow_html=True)

    for arg in args:
        if isinstance(arg, str):
            body(arg)

        elif isinstance(arg, HtmlElement):
            body(arg)

    st.markdown(str(foot), unsafe_allow_html=True)

def footer():

    myargs = [
        "FermentDB® ",
    ]
    
    layout(*myargs)

# - - - - - - - - - - - - - - - - - - - APP LOGIC - - - - - - - - - - - - - - - - - - - 
def app(): 
# - - - - - - - - - - - - - - - - STATISTICAL SECTION - - - - - - - - - - - - - - - - - 
    
    #st.header('FermentDB', divider='grey')
    st.markdown("<h1 style='text-align: center; font-size: 30px;'>Welcome to <span style= 'font-size: 40px;'>FermentDB</span></h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center;'>A Database for High-cell Density Fermentations</h5>", unsafe_allow_html=True)

    load_statistics_data()
       

    # - - - - - - - - - - - - - - - - BIOPROCESS CONDITIONS EXPLORE SECTION - - - - - - - - - - - - - - - - - 
    st.divider()

    st.markdown("<h3 style='text-align: center;'>Explore Bioprocess Conditions</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Dive into the depths of FermentDB's comprehensive data to cross-reference multiple fermentation experiments at once </p>", unsafe_allow_html=True)

    load_pcondition_exploration()

    # - - - - - - - - - - - - -  iMODULON EXPLORE SECTION - - - - - - - - - - - - - - - - - 
    st.divider()

    st.markdown("<h3 style='text-align: center;'> Explore iModulons </h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'> Dive deep into the science of iModulons and high-cell density fermentations </p>", unsafe_allow_html=True)

    load_imodulon_exploration()


    # @st.cache_data
    # def init_graph():
    # # Initialize d3graph
    #     d3 = d3graph()
    
    # # Sample Data Preparation
    # # Create an adjacency matrix for 5 nodes
    #     adjmat = np.array([
    #         [0, 1, 1, 0, 0],  # Connections for node A
    #         [1, 0, 1, 1, 0],  # Connections for node B
    #         [1, 1, 0, 1, 1],  # Connections for node C
    #         [0, 1, 1, 0, 1],  # Connections for node D
    #         [0, 0, 1, 1, 0]   # Connections for node E
    #     ])

    # # Create a DataFrame for node properties
    #     data = {
    #         'label': ['A', 'B', 'C', 'D', 'E'],      # Labels for the nodes
    #         'degree': [2, 3, 4, 3, 2]                # Degrees for the nodes
    #     }
    #     df = pd.DataFrame(data)

    # # Node properties
    #     label = df["label"].values
    #     node_size = df["degree"].values

    #     return d3, adjmat, df, label, node_size

    # @st.cache_data
    # def graph_one(_d3, adjmat, df, label, node_size):
    #     _d3.graph(adjmat)
    #     _d3.set_node_properties(
    #         color=label,
    #         size=node_size,
    #         edge_size=node_size,
    #         edge_color="#00FFFF",
    #         cmap="Set1"
    #     )
    #     return _d3

    # # Initialize the graph
    # d3, adjmat, df, label, node_size = init_graph()

    # # Create and display the graph
    # d3 = graph_one(d3, adjmat, df, label, node_size)
    # d3.show()
    
    # - - - - - - - - - - - - - FOOTER - - - - - - - - - - - - - - - - - 
    footer()
    
# if __name__ == '__main__':
#     app()


def show_about():
    st.write("About")


# #### ------ DEFINE PAGES -------- ####


# pages = ["Home","About", "Explore Bioprocess", "Explore iModulon"]
parent_dir = os.path.dirname(os.path.abspath(__file__))
#logo_path = os.path.join(parent_dir, "./assets/images/page_icon.png")

styles_navbar = {
    "nav": {
        "background-color": "royalblue",
        "justify-content": "left",
    },
    "img": {
        "padding-right": "14px",
    },
    "span": {
        "color": "white",
        "padding": "14px",
    },
    "active": {
        "background-color": "white",
        "color": "var(--text-color)",
        "font-weight": "normal",
        "padding": "14px",
    }
}
options = {
    "show_menu": False,
    "show_sidebar": False,
}

pages = ["FermentDB","About"]

page = st_navbar(pages)
# page = st_navbar(
#     pages,
#     #logo_path=logo_path,
#     styles=styles_navbar,
#     options=options
# )

if page == "FermentDB":
    app()
elif page == "About":
    show_about()


# functions = {
#     "Home": pg.app,
#     "About": pg.show_about,
#     #"Explore Bioprocess": pg.show_bioprocess,
#     #"Explore iModulon": pg.show_imodulon,
# }

# go_to = functions.get(page)
# if go_to:
#     go_to()


# page()












