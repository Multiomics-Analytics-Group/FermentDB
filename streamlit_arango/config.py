import os
import streamlit as st


class Config:
    class ArangoDB:
            host: str = os.getenv("ARANGO_HOST", st.secrets.get("ARANGO_HOST"))
            database: str = os.getenv("ARANGO_DATABASE", st.secrets.get("ARANGO_DATABASE"))
            username: str = os.getenv("ARANGO_USERNAME", st.secrets.get("ARANGO_USERNAME")) 
            password: str = os.getenv("ARANGO_PASSWORD", st.secrets.get("ARANGO_PASSWORD"))