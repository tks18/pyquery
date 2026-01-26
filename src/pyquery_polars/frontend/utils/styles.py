import streamlit as st


def inject_custom_css():
    """
    Injects custom CSS to create a more compact, enterprise-dense UI.
    """
    compact_css = """
    <style>
        /* --- GLOBAL --- */
        html, body, .stApp {
            font-family: 'Inter', sans-serif;
            font-size: 15px;
        }

        /* --- LAYOUT PADDING --- */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important; /* increased to ensure scrolling clears footer */
            max-width: 95% !important;
        }
        
        /* --- HEADERS --- */
        h1 { font-size: 2.0rem !important; padding-bottom: 0.5rem !important; }
        h2 { font-size: 1.6rem !important; padding-bottom: 0.5rem !important; }
        h3 { font-size: 1.3rem !important; padding-bottom: 0.5rem !important; }
        
        /* --- WIDGET SPACING --- */
        .stElementContainer {
            margin-bottom: 0.0rem !important;
        }
        
        /* Sidebar spacing */
        section[data-testid="stSidebar"] .stElementContainer {
            margin-bottom: 0.0rem !important;
        }

        /* --- BUTTONS --- */
        button {
            height: auto !important; 
        }
    </style>
    """
    st.markdown(compact_css, unsafe_allow_html=True)
