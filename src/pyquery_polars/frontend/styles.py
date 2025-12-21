import streamlit as st


def inject_custom_css():
    """
    Injects custom CSS to create a more compact, enterprise-dense UI.
    """
    compact_css = """
    <style>
        /* --- GLOBAL --- */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
            font-size: 15px; /* Slightly larger for readability */
        }

        /* --- LAYOUT PADDING --- */
        /* Reduce top padding but keep it reasonable */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            max-width: 95% !important;
        }
        
        /* --- HEADERS --- */
        h1 { font-size: 2.0rem !important; padding-bottom: 0.5rem !important; }
        h2 { font-size: 1.6rem !important; padding-bottom: 0.5rem !important; }
        h3 { font-size: 1.3rem !important; padding-bottom: 0.5rem !important; }
        
        /* --- WIDGET SPACING --- */
        /* Neutralize massive default spacing without overlap */
        .stElementContainer {
            margin-bottom: 0.0rem !important; /* From -0.5rem to 0 */
        }
        
        /* Sidebar spacing - slightly tighter than main */
        section[data-testid="stSidebar"] .stElementContainer {
            margin-bottom: 0.0rem !important;
        }

        /* --- BUTTONS --- */
        button {
            /* Let Streamlit handle height to prevent text cutting */
            height: auto !important; 
        }


    </style>
    """
    st.markdown(compact_css, unsafe_allow_html=True)
