"""Server-only settings; never copy secrets into client-visible state."""
import os

def setting(name,default=''):
    value=os.getenv(name)
    if value is not None:return value
    try:
        import streamlit as st
        return st.secrets.get(name,default)
    except (FileNotFoundError,KeyError):return default

