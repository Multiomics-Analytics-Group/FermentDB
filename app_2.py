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




st.set_page_config(page_title="FermentDB",page_icon="./assets/images/page_icon.png", initial_sidebar_state="collapsed")
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

# #### ------ NAVBAR SECTION -------- ####
pages = {
    "Home": app(),
    "About": page_about
}

pages = ["Home","About", "Explore Bioprocess", "Explore iModulon"]
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

page = st_navbar(
    pages,
    #logo_path=logo_path,
    styles=styles_navbar,
    options=options
)


# functions = {
#     "Home": pg.app,
#     "About": pg.show_about,
#     #"Explore Bioprocess": pg.show_bioprocess,
#     #"Explore iModulon": pg.show_imodulon,
# }

# go_to = functions.get(page)
# if go_to:
#     go_to()
















