''' FermentDB Streamlit App '''

# - - - - - - - - - - - IMPORT MODULES - - - - - - - - - - - - - - - - - 

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import hashlib
import plotly.figure_factory as ff
from collections import Counter
import time

from arango import ArangoClient
from streamlit_arango.config import Config
from streamlit import session_state as ss



st.set_page_config(page_title="FermentDB",page_icon="./assets/images/page_icon.png")
# - - - - - - - - - - - - - - - CSS CODE FOR CUSTOMIZATION - - - - - - - - - - - - -

with open('style.css', "r") as file:
    style_css = file.read()

st.markdown(f'<style>{style_css}</style>', unsafe_allow_html=True)

# - - - - - - - - - - - - - - - CONNECT TO ARANGODB - - - - - - - - - - - - - 

# Initialize the ArangoDB client. 
client = ArangoClient(hosts=Config.ArangoDB.host)

# Initialize connection to database: "fermentdb" as root user
@st.cache_data
def connect_to_db():
    if 'db' not in ss:
        ss.db = client.db(
            name = Config.ArangoDB.database,
            username = Config.ArangoDB.username,
            password = Config.ArangoDB.password
    )
    return ss.db

@st.cache_data
def get_aql():
    if 'aql' not in ss:
        ss.aql = connect_to_db().aql
    return ss.aql


# - - - - - - - - - - - - - - - - - - QUERY DATA FROM ARANGODB - - - - - -- - - - - - 

#### ------ STATISTICS SECTION -------- ####

@st.cache_data(show_spinner=False)
def get_num_node_documents():
    vertex_collections = connect_to_db().graph('fermentdb').vertex_collections()
    total_nodes = 0

    for collection_name in vertex_collections:
        collection = connect_to_db().collection(collection_name)
        total_nodes += collection.count()

    return total_nodes

@st.cache_data(show_spinner=False)
def get_num_edge_documents():
    edge_definitions = connect_to_db().graph('fermentdb').edge_definitions()
    total_edges = 0

    for edge_def in edge_definitions:
        collection_name = edge_def['edge_collection']
        collection = connect_to_db().collection(collection_name)
        total_edges += collection.count()
    
    return total_edges

@st.cache_data(show_spinner=False)
def get_icicle_chart():
    time.sleep(8)
    query = """
        FOR doc IN Run
            FOR fermenter_v, fermenter_e IN 1..1 OUTBOUND doc uses_fermenter
                FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
                    FOR species_v, species_e IN 1..1 OUTBOUND strain_v belongs_to
                        COLLECT fermenter = fermenter_v.name, species = species_v.name, strains = strain_v.name
                        WITH COUNT INTO num_runs 
                        RETURN { fermenter: fermenter, species: species, strains: strains, num_runs: num_runs  }  
    """
    cursor = get_aql().execute(query)
    result = [doc for doc in cursor] 
    print(f"Result icicle: {result}")  
    df = pd.DataFrame(result)
    fig = px.icicle(df, path=[px.Constant("High-cell density fermentations"), 'fermenter', 'species', 'strains'], values='num_runs',
                   color='num_runs', hover_data=['num_runs'],
                    color_continuous_scale='RdBu',
                    color_continuous_midpoint=np.average(df['num_runs'], weights=df['num_runs']))
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

    st.plotly_chart(fig, theme="streamlit")

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


# @st.cache_data
# def get_icicle_chart():
#     # Query to get the number of runs per fermenter, species, and strain
#     query = """
#         FOR doc IN Run
#             FOR fermenter_v, fermenter_e IN 1..1 OUTBOUND doc uses_fermenter
#                 FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
#                     FOR species_v, species_e IN 1..1 OUTBOUND strain_v belongs_to
#                         COLLECT fermenter = fermenter_v.name, species = species_v.name, strain = strain_v.name
#                         WITH COUNT INTO num_runs 
#                         RETURN { fermenter: fermenter, species: species, strain: strain, num_runs: num_runs }
#     """

#     # Execute the query
#     cursor = get_aql().execute(query)
#     result = [doc for doc in cursor]
#     df = pd.DataFrame(result)

#     # Group by fermenter and species to get the number of strains at the species level
#     counts_species_strains = df.groupby(['fermenter', 'species']).nunique('strain').reset_index()
#     counts_species_strains = counts_species_strains.rename(columns={'strain': 'count_strains'})

#     # Group by fermenter and species to get the number of runs at the species level
#     counts_species = df.groupby(['fermenter', 'species']).sum('num_runs').reset_index()
#     counts_species = counts_species.rename(columns={'num_runs': 'edges_species'})

#     # Group by fermenter to get the number of runs at the fermenter level
#     counts_fermenter = df.groupby(['fermenter']).sum('num_runs').reset_index()
#     counts_fermenter = counts_fermenter.rename(columns={'num_runs': 'edges_fermenter'})

#     # Merge counts back into the original DataFrame
#     aux = pd.merge(df, counts_species, on=['fermenter', 'species'], how='left')
#     aux = pd.merge(aux, counts_species_strains, on=['fermenter', 'species'], how='left')
#     aux = pd.merge(aux, counts_fermenter, on=['fermenter'], how='left')

#     # Add a color value based on num_runs for strains and edges_species for higher levels
#     aux['color_value'] = aux.apply(lambda row: row.get('num_runs') if row.get('strain') else row.get('edges_species'), axis=1)

#     # Adjust the color scale based on the cumulative runs at the species level
#     # max_color_value = aux['color_value'].max()
#     # min_color_value = aux['color_value'].min()

#     # Create the icicle chart
#     fig = px.icicle(aux, 
#                     path=[px.Constant("High-cell density fermentations"), 'fermenter', 'species', 'strain'], 
#                     values='num_runs_x',  # Adjust 'values' parameter
#                     color='color_value',  
#                     hover_data=['edges_fermenter', 'edges_species', 'num_runs_x'],
#                     color_continuous_scale='Viridis')
    
#     fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

#     st.plotly_chart(fig)

def get_doc_count(collection):
    cursor = get_aql().execute( f'''
        FOR doc IN {collection}
        RETURN doc.name
    ''')
    result = []
    for item in cursor:
        result.append(item)
    #print(f"Get doc: {result}")
    return len(result)

#### ------ FERMENTATION EXPLORE SECTION -------- ####

def get_doc_name(collection):

    cursor = get_aql().execute( f'''
        FOR doc IN {collection}
        RETURN doc.name
    ''')

    result = []
    for item in cursor:
        result.append(item)
    #print(f"Get doc: {result}")
    return result

def get_hash(key, prefix=""):
    hkey = str(int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % (10 ** 8))
    hkey = f"{prefix}{hkey}"
    return hkey

def get_strains():
    cursor = get_aql().execute('''
                               
        FOR doc IN Run
            RETURN doc.strain_batch                           
    ''')
    
    result = set()
    for item in cursor:
        result.add(item)
    return result

def get_strains_2(species):
    species = [f"Species/{get_hash(s, prefix='SP')}" for s in species]
    
    query= """
        FOR doc IN Strain
            FOR v, e IN 1..1 OUTBOUND doc belongs_to
                FILTER e._to IN @species
                RETURN doc.name
    """

    cursor = get_aql().execute(query, bind_vars={'species': species})
    
    result = [doc for doc in cursor]
    # result = set()
    # for item in cursor:
    #     result.add(item)
    # print(result)
    return result

def get_fermenter_type_2(strains):
    strains = [f"Strain/{get_hash(s, prefix='S')}" for s in strains]

    query = """
        FOR doc IN Run
            FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
                FILTER strain_e._to IN @strains
                    FOR fermenter_v, fermenter_e IN 1..1 OUTBOUND doc uses_fermenter
                    RETURN fermenter_v.name
    """

    cursor = get_aql().execute(query, bind_vars={'strains': strains})

    result = [doc for doc in cursor]
    # result = set()
    # for item in cursor:
    #     result.add(item)
    # print(result)
    return result

def get_pconditions_2(strains, fermenters):
    strains = [f"Strain/{get_hash(s, prefix='S')}" for s in strains]
    fermenters = [f"Fermenter/{get_hash(f, prefix='F')}" for f in fermenters]

    query = """
        FOR doc IN Run
            FOR strain_v, strain_e IN 1..1 OUTBOUND doc cultures_strain
                FILTER strain_e._to IN @strains
                FOR fermenter_v, fermenter_e IN 1..1 OUTBOUND doc uses_fermenter
                    FILTER fermenter_e._to IN @fermenters
                    FOR v, e IN 1..1 doc has_condition
                        RETURN v.name
    """

    cursor = get_aql().execute(query, bind_vars={'strains': strains,
                                                 'fermenters': fermenters})
    
    result = [doc for doc in cursor]
    # result = set()
    # for item in cursor:
    #     result.add(item)
    # print(result)
    return result



def get_pcondition_data2(strains, conditions, fermenters):
    conditions = [f"Process_condition/{get_hash(c, prefix='C')}" for c in conditions]
    strains = [f"Strain/{get_hash(s, prefix='S')}" for s in strains]
    fermenters = [f"Fermenter/{get_hash(f, prefix='F')}" for f in fermenters]
    
    query = '''
        FOR doc IN Run
            FOR strain_vertex, strain_edge IN 1..1 INBOUND doc cultures_strain
                FILTER strain_edge._to IN @strains
                FOR fermenter_vertex, fermenter_edge IN 1..1 INBOUND doc uses_fermenter
                    FILTER fermenter_edge._to IN @fermenters
                    FOR v, e IN 1..1 OUTBOUND doc has_condition
                        FILTER e._to IN @conditions
                        RETURN { source: doc, target: v, edge: e}
    '''
    cursor = get_aql().execute(query, bind_vars={'strains': strains,
                                                'conditions': conditions, 
                                                'fermenters': fermenters})
    result = [doc for doc in cursor]
    print(result)
    return result


# def query_sum_strains_from_db():
#     cursor = get_aql().execute('''
                               
#         FOR doc IN Run
#             FOR v, e IN 1..1 OUTBOUND doc cultures_strain
#                 COLLECT strain = e.strain_batch WITH COUNT INTO counter 
#                 RETURN { strain: strain, count: counter}                          
#     ''')
    
#     result = []
#     for item in cursor:
#         result.append(item)
#     print(result)
#     return result

# def query_sum_runs_from_db():
#     cursor = get_aql().execute('''
                               
#         FOR doc IN Run
#             COLLECT run = doc.name WITH COUNT INTO counter 
#                 RETURN { run: run, count: counter}                          
#     ''')
    
#     result = []
#     for item in cursor:
#         result.append(item)
#     print(result)
#     return result

# def query_sum_pconditions_from_db():
#     cursor = get_aql().execute('''
#         FOR doc IN Run
#             FOR v, e IN 1..1 OUTBOUND doc has_condition
#                 LET pcondition = SPLIT(e._to, '/')[1] //Extract part after "/"
#                 COLLECT pcondition_hash = e._to WITH COUNT INTO counter 
#                 RETURN { process_condition: pcondition_hash, count: counter}                          
#     ''')
    
#     result = []
#     for item in cursor:
#         pcondition_hash = item['process_condition']
#         pcondition_name = get_hash(pcondition_hash, "C")
#         item['process_condition'] = pcondition_name
#         result.append(item)
#     return result

def get_pcondition_data(strain, pcondition, fermenter):
    pcondition = [f"Process_condition/{get_hash(c, prefix='C')}" for c in pcondition]
    
    query = '''FOR doc IN Run
      FILTER doc.strain_batch == @val AND doc.container_type == @fermenter
      FOR v, e IN 1..1 OUTBOUND doc has_condition
        FILTER e._to IN @condition
        RETURN { source: doc, target: v, edge: e }
    '''           
    cursor = get_aql().execute(query,bind_vars={'val': strain,
                                                'condition': pcondition,
                                                'fermenter': fermenter})
    result = [doc for doc in cursor]
    #print(result)
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
    fig = px.line(df, x="time", y="data", color='run', line_dash='condition')
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


#TODO: check function to update new chart
if 'go_clicked' not in st.session_state:
    st.session_state.go_clicked = False

def click_go():
    st.session_state.go_clicked = True


def plot_pcondition_table(strain, pcondition, fermenter ):
    result = get_pcondition_data(strain, pcondition, fermenter)
    data_dict = {}
    
    for r in result:
        source = r['source']['_key']
        strain = r['source']['strain_batch']
        fermenter = r['source']['container_type']
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

# - - - - - - - - - - - - - - - - - - - APP LOGIC - - - - - - - - - - - - - - - - - - - 
def app(): 
# - - - - - - - - - - - - - - - - STATISTICAL SECTION - - - - - - - - - - - - - - - - - 
    
    st.header('FermentDB', divider='grey')
    st.markdown("<h1 style='text-align: center; font-size: 30px;'>Welcome to <span style= 'font-size: 40px;'>FermentDB</span></h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center;'>A Database for High-cell Density Fermentations</h5>", unsafe_allow_html=True)

    load_statistics_data()
       

    # - - - - - - - - - - - - - - - - FERMENTATION EXPLORE SECTION - - - - - - - - - - - - - - - - - 
    st.divider()

    ss

    # Initialize variables
    ss.strain_disabled = True
    ss.ferm_disabled = True
    ss.cultivation_disabled = True
    ss.pcond_disabled = True


        
    st.markdown("<h3 style='text-align: center;'>Explore Fermentations</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Dive into the depths of FermentDB's comprehensive data to cross-reference multiple fermentation experiments at once </p>", unsafe_allow_html=True)

    ss.strain_disabled
    st.markdown("<p style='text-align: left; margin-top: 30px'>Select organism of interest: </p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.selectbox(
            'Species: ',
            get_doc_name('Species'),
            key = "sb_species",
            index=None,
            placeholder="Choose species",
            help = "Select the type of microorganism you wish to study")

    if ss.sb_species is not None:
        ss.strain_disabled = False

    st.write(f"sb_species: {ss.sb_species}")
    ss.strain_disabled

    col2.selectbox( # st.multiselect()
            'Strain:',
            get_strains_2(ss.sb_species),
            key = "sb_strain",
            index=None,
            placeholder="Choose strain",
            disabled = ss.strain_disabled,
            help = "Select a specific strain of your chosen organism. Each strain has unique characteristics and applications")

    if ss.sb_strain is not None:
        ss.ferm_disabled = False


    st.markdown("<p style='text-align: left; margin-top: 30px'>Select Fermenter: </p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.selectbox(
            'Fermenter type:',
            get_fermenter_type_2(ss.sb_strain),
            key = 'sb_fermenter_type',
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

    st.markdown("<p style='text-align: left; margin-top: 30px'> Select Condition of Interest: </p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.selectbox(
        'Process Condition:',
        get_doc_name('Process_condition'),
        key = 'sb_pcondition',
        index=None,
        placeholder='Choose condition',
        disabled = ss.pcond_disabled,
        help = "Select the specific process condition")
        
    col1, col2, col3 = st.columns(3)   
    col2.button('GO!', on_click=click_go)

    if ss.go_clicked:
        st.divider()
        st.markdown("<h5>Fermentation Data Visualization</h5>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Line Graph", "Table"])
        with tab1:
            plot_pcondition_chart(strain=ss.sb_strain, pcondition=[ss.sb_pcondition], fermenter= ss.sb_fermenter_type)
        with tab2:
            plot_pcondition_table(strain= ss.sb_strain, pcondition=[ss.sb_pcondition], fermenter= ss.sb_fermenter_type)

    ss


    # - - - - - - - - - - - - -  iMODULON EXPLORE SECTION - - - - - - - - - - - - - - - - - 
    st.divider()


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
        plot_pcondition_table(strain= ss.sb_strain, pcondition=[ss.sb_pcondition], fermenter= ss.sb_fermenter_type)

ss

###############################################
### ------ iModulon Explore Section ------- ###
###############################################
st.divider()

st.markdown("<h3 style='text-align: center;'> Explore iModulons </h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'> Dive deep into the science of iModulons and high-cell density fermentations </p>", unsafe_allow_html=True)

if __name__ == '__main__':
    app()

















