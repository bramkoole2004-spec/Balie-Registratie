"""
TIELBEKE BEZOEKERSREGISTRATIE SYSTEEM
=====================================

INSTALLATIE & OPSTARTEN:
------------------------
1. Installeer vereiste packages:
   pip install streamlit pandas qrcode pillow

2. Start de applicatie:
   streamlit run visitor_registration.py

3. De app opent automatisch in je browser op http://localhost:8501

GEBRUIK:
--------
- Bezoekers scannen de QR-code en vullen het formulier in
- Bij vertrek kunnen bezoekers zichzelf afmelden
- Receptie gebruikt de 'Receptie Dashboard' tab om bezoekers te beheren
- Admin tab voor QR-code generatie en systeem beheer
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import qrcode
from io import BytesIO
import re

# ===== DATABASE SETUP =====
def init_database():
    """Initialiseer SQLite database met bezoekers tabel"""
    conn = sqlite3.connect('bezoekers.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bezoekers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            email TEXT NOT NULL,
            telefoon TEXT NOT NULL,
            bedrijf TEXT NOT NULL,
            bezoekt TEXT NOT NULL,
            reden TEXT NOT NULL,
            tijdstip_in TEXT NOT NULL,
            tijdstip_uit TEXT,
            status TEXT DEFAULT 'actief'
        )
    ''')
    conn.commit()
    return conn

# ===== VALIDATIE FUNCTIES =====
def valideer_email(email):
    """Valideer email formaat"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def valideer_telefoon(telefoon):
    """Valideer Nederlands telefoonnummer"""
    # Verwijder spaties, streepjes en haakjes
    clean = re.sub(r'[\s\-\(\)]', '', telefoon)
    # Check of het begint met 0 of +31 en minimaal 10 cijfers heeft
    if re.match(r'^(\+31|0)[0-9]{9,10}$', clean):
        return True
    return False

# ===== DATABASE FUNCTIES =====
def voeg_bezoeker_toe(naam, email, telefoon, bedrijf, bezoekt, reden):
    """Voeg nieuwe bezoeker toe aan database"""
    conn = sqlite3.connect('bezoekers.db')
    c = conn.cursor()
    tijdstip = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO bezoekers (naam, email, telefoon, bedrijf, bezoekt, reden, tijdstip_in, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'actief')
    ''', (naam, email, telefoon, bedrijf, bezoekt, reden, tijdstip))
    bezoeker_id = c.lastrowid
    conn.commit()
    conn.close()
    return bezoeker_id

def haal_actieve_bezoekers():
    """Haal alle actieve bezoekers op"""
    conn = sqlite3.connect('bezoekers.db')
    df = pd.read_sql_query(
        "SELECT * FROM bezoekers WHERE status='actief' ORDER BY tijdstip_in DESC", 
        conn
    )
    conn.close()
    return df

def haal_alle_bezoekers():
    """Haal alle bezoekers op (inclusief uitgecheckt)"""
    conn = sqlite3.connect('bezoekers.db')
    df = pd.read_sql_query(
        "SELECT * FROM bezoekers ORDER BY tijdstip_in DESC", 
        conn
    )
    conn.close()
    return df

def checkout_bezoeker(bezoeker_id):
    """Check bezoeker uit (status naar 'uitgecheckt')"""
    conn = sqlite3.connect('bezoekers.db')
    c = conn.cursor()
    tijdstip_uit = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute(
        "UPDATE bezoekers SET status='uitgecheckt', tijdstip_uit=? WHERE id=?", 
        (tijdstip_uit, bezoeker_id)
    )
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected

def zoek_actieve_bezoeker(zoekterm):
    """Zoek actieve bezoeker op naam, email of telefoon"""
    conn = sqlite3.connect('bezoekers.db')
    c = conn.cursor()
    c.execute(
        """SELECT * FROM bezoekers 
           WHERE (naam LIKE ? OR email LIKE ? OR telefoon LIKE ?) 
           AND status='actief' 
           ORDER BY tijdstip_in DESC LIMIT 5""",
        (f'%{zoekterm}%', f'%{zoekterm}%', f'%{zoekterm}%')
    )
    resultaten = c.fetchall()
    conn.close()
    return resultaten

# ===== QR CODE GENERATIE =====
def genereer_qr_code(url):
    """Genereer QR code voor gegeven URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Maak de image
    img = qr.make_image(fill_color="#003B5C", back_color="white")
    
    # Converteer naar bytes voor download
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return buf

# ===== STREAMLIT APP =====
def main():
    # Initialiseer database
    init_database()
    
    # Page config
    st.set_page_config(
        page_title="Tielbeke Bezoekersregistratie",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Professional CSS styling
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* General styling */
        * {
            font-family: 'Inter', sans-serif;
        }
        
        .main {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* Header styling */
        .tielbeke-header {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .tielbeke-logo {
            max-width: 300px;
            margin-bottom: 1rem;
            background: white;
            padding: 1rem 2rem;
            border-radius: 10px;
        }
        
        .header-title {
            color: white;
            font-size: 2rem;
            font-weight: 600;
            margin: 0;
            letter-spacing: -0.5px;
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1rem;
            font-weight: 300;
            margin-top: 0.5rem;
        }
        
        /* Button styling */
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #F00008 0%, #c00006 100%);
            color: white;
            font-size: 16px;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            border: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(240, 0, 8, 0.3);
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(240, 0, 8, 0.4);
            background: linear-gradient(135deg, #d00007 0%, #a00005 100%);
        }
        
        /* Input styling */
        .stTextInput input, .stSelectbox select {
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            padding: 0.75rem;
            font-size: 15px;
        }
        
        /* Success box */
        .success-box {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #10B981;
            margin: 2rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .success-title {
            color: #10B981;
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }
        
        /* Goodbye box */
        .goodbye-box {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #F59E0B;
            margin: 2rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .goodbye-title {
            color: #F59E0B;
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }
        
        /* Card styling */
        .visitor-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 4px solid #F00008;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: white;
            padding: 0.5rem;
            border-radius: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
        }
        
        /* Info box */
        .info-box {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #3B82F6;
            margin: 1rem 0;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Section headers */
        .section-header {
            color: #1a1a1a;
            font-size: 1.5rem;
            font-weight: 600;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #F00008;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Tabs voor verschillende interfaces
    tab1, tab2, tab3, tab4 = st.tabs([
        "Aanmelden", 
        "Afmelden",
        "Receptie Dashboard", 
        "Admin"
    ])
    
    # ===== TAB 1: BEZOEKERSREGISTRATIE (AANMELDEN) =====
    with tab1:
        # Header met logo
        st.markdown("""
            <div class="tielbeke-header">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8IS0tIFJlZCBUIHdpdGggd2luZ3MgLS0+CiAgPGcgaWQ9ImxvZ28iPgogICAgPCEtLSBMZWZ0IHdpbmcgLS0+CiAgICA8cGF0aCBkPSJNIDUwLDEyMCBMIDEwLDEzMCBMIDEwLDE0MCBMIDUwLDEzMCBaIiBmaWxsPSIjRjAwMDA4IiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjMiLz4KICAgIDxwYXRoIGQ9Ik0gNTAsMTEwIEwgMTAsMTE1IEwgMTAsMTI1IEwgNTAsMTIwIFoiIGZpbGw9IiNGMDAwMDgiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMyIvPgogICAgCiAgICA8IS0tIENlbnRyYWwgVCAtLT4KICAgIDxyZWN0IHg9IjUwIiB5PSI2MCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI0YwMDAwOCIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIzIi8+CiAgICA8cmVjdCB4PSIzNSIgeT0iNjAiIHdpZHRoPSIxMTAiIGhlaWdodD0iMjUiIGZpbGw9IiNGMDAwMDgiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMyIvPgogICAgCiAgICA8IS0tIFJpZ2h0IHdpbmcgLS0+CiAgICA8cGF0aCBkPSJNIDEzMCwxMjAgTCAxNzAsMTMwIEwgMTcwLDE0MCBMIDM2MCwxMzAgWiIgZmlsbD0iI0YwMDAwOCIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIzIi8+CiAgICA8cGF0aCBkPSJNIDEzMCwxMTAgTCAxNzAsMTE1IEwgMTcwLDEyNSBMIDEzMCwxMjAgWiIgZmlsbD0iI0YwMDAwOCIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIzIi8+CiAgPC9nPgogIAogIDwhLS0gVGV4dDogdGllbGJla2UgLS0+CiAgPHRleHQgeD0iMjAwIiB5PSIxMzUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSI3MCIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9ImJsYWNrIj50aWVsYmVrZTwvdGV4dD4KPC9zdmc+" 
                     class="tielbeke-logo" alt="Tielbeke Logo">
                <h1 class="header-title">Welkom bij Tielbeke</h1>
                <p class="header-subtitle">Registreer jezelf als bezoeker</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Check of er een success message moet worden getoond
        if 'registratie_success' in st.session_state and st.session_state.registratie_success:
            st.markdown(f"""
                <div class="success-box">
                    <h2 class="success-title">Welkom, {st.session_state.bezoeker_naam}</h2>
                    <p style="margin: 0; font-size: 1.05rem; line-height: 1.6;">
                        Je registratie is succesvol ontvangen. Iemand van ons team komt je zo ophalen. 
                        Voel je vrij om plaats te nemen in de wachtruimte.
                    </p>
                    <p style="margin: 1rem 0 0 0; font-size: 0.95rem; color: #059669;">
                        <strong>Tip:</strong> Vergeet niet jezelf af te melden bij vertrek via het "Afmelden" tabblad.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Nieuwe bezoeker registreren"):
                st.session_state.registratie_success = False
                st.rerun()
        else:
            # Registratieformulier
            with st.form("bezoeker_form", clear_on_submit=True):
                st.markdown('<p style="font-size: 1.1rem; font-weight: 500; margin-bottom: 1.5rem;">Vul je gegevens in</p>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    naam = st.text_input(
                        "Volledige naam *",
                        placeholder="Jan Jansen",
                    )
                    email = st.text_input(
                        "E-mailadres *",
                        placeholder="jan.jansen@bedrijf.nl",
                    )
                    bedrijf = st.text_input(
                        "Bedrijf/Organisatie *",
                        placeholder="ABC Consulting",
                    )
                
                with col2:
                    telefoon = st.text_input(
                        "Telefoonnummer *",
                        placeholder="06 12345678",
                    )
                    bezoekt = st.text_input(
                        "Wie bezoek je? *",
                        placeholder="Piet Pietersen",
                    )
                    reden = st.text_input(
                        "Reden van bezoek *",
                        placeholder="Zakelijke bespreking",
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit_button = st.form_submit_button("Aanmelden")
                
                if submit_button:
                    # Validatie
                    errors = []
                    
                    if not naam or len(naam.strip()) < 2:
                        errors.append("Vul een geldige naam in (minimaal 2 karakters)")
                    
                    if not email or not valideer_email(email):
                        errors.append("Vul een geldig e-mailadres in")
                    
                    if not telefoon or not valideer_telefoon(telefoon):
                        errors.append("Vul een geldig Nederlands telefoonnummer in")
                    
                    if not bedrijf or not bezoekt or not reden:
                        errors.append("Alle velden zijn verplicht")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Opslaan in database
                        try:
                            bezoeker_id = voeg_bezoeker_toe(
                                naam.strip(),
                                email.strip(),
                                telefoon.strip(),
                                bedrijf.strip(),
                                bezoekt.strip(),
                                reden.strip()
                            )
                            st.session_state.registratie_success = True
                            st.session_state.bezoeker_naam = naam.strip()
                            st.session_state.bezoeker_id = bezoeker_id
                            st.rerun()
                        except Exception as e:
                            st.error(f"Er is een fout opgetreden: {str(e)}")
            
            st.markdown('<div class="info-box"><strong>Privacy:</strong> Je gegevens worden alleen gebruikt voor bezoekersregistratie en worden beveiligd opgeslagen.</div>', unsafe_allow_html=True)
    
    # ===== TAB 2: AFMELDEN =====
    with tab2:
        st.markdown("""
            <div class="tielbeke-header">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8IS0tIFJlZCBUIHdpdGggd2luZ3MgLS0+CiAgPGcgaWQ9ImxvZ28iPgogICAgPCEtLSBMZWZ0IHdpbmcgLS0+CiAgICA8cGF0aCBkPSJNIDUwLDEyMCBMIDEwLDEzMCBMIDEwLDE0MCBMIDUwLDEzMCBaIiBmaWxsPSIjRjAwMDA4IiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjMiLz4KICAgIDxwYXRoIGQ9Ik0gNTAsMTEwIEwgMTAsMTE1IEwgMTAsMTI1IEwgNTAsMTIwIFoiIGZpbGw9IiNGMDAwMDgiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMyIvPgogICAgCiAgICA8IS0tIENlbnRyYWwgVCAtLT4KICAgIDxyZWN0IHg9IjUwIiB5PSI2MCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI0YwMDAwOCIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIzIi8+CiAgICA8cmVjdCB4PSIzNSIgeT0iNjAiIHdpZHRoPSIxMTAiIGhlaWdodD0iMjUiIGZpbGw9IiNGMDAwMDgiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMyIvPgogICAgCiAgICA8IS0tIFJpZ2h0IHdpbmcgLS0+CiAgICA8cGF0aCBkPSJNIDEzMCwxMjAgTCAxNzAsMTMwIEwgMTcwLDE0MCBMIDM2MCwxMzAgWiIgZmlsbD0iI0YwMDAwOCIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIzIi8+CiAgICA8cGF0aCBkPSJNIDEzMCwxMTAgTCAxNzAsMTE1IEwgMTcwLDEyNSBMIDEzMCwxMjAgWiIgZmlsbD0iI0YwMDAwOCIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSIzIi8+CiAgPC9nPgogIAogIDwhLS0gVGV4dDogdGllbGJla2UgLS0+CiAgPHRleHQgeD0iMjAwIiB5PSIxMzUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSI3MCIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9ImJsYWNrIj50aWVsYmVrZTwvdGV4dD4KPC9zdmc+" 
                     class="tielbeke-logo" alt="Tielbeke Logo">
                <h1 class="header-title">Afmelden</h1>
                <p class="header-subtitle">Meld jezelf af bij het verlaten van het pand</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Check of er een afmeld success message moet worden getoond
        if 'afmeld_success' in st.session_state and st.session_state.afmeld_success:
            st.markdown(f"""
                <div class="goodbye-box">
                    <h2 class="goodbye-title">Tot ziens, {st.session_state.afgemelde_naam}</h2>
                    <p style="margin: 0; font-size: 1.05rem;">
                        Je bent succesvol afgemeld. Bedankt voor je bezoek aan Tielbeke!
                        We hopen je snel weer te zien.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Nog een persoon afmelden"):
                st.session_state.afmeld_success = False
                st.rerun()
        else:
            st.markdown('<div class="info-box">Zoek jezelf op naam, e-mail of telefoonnummer en meld je af bij vertrek</div>', unsafe_allow_html=True)
            
            # Zoekformulier
            with st.form("afmeld_form"):
                zoekterm = st.text_input(
                    "Zoeken",
                    placeholder="Typ je naam, e-mail of telefoonnummer...",
                )
                zoek_button = st.form_submit_button("Zoeken")
            
            if zoek_button and zoekterm and len(zoekterm.strip()) >= 2:
                resultaten = zoek_actieve_bezoeker(zoekterm)
                
                if len(resultaten) == 0:
                    st.warning(f"Geen actieve bezoekers gevonden met '{zoekterm}'")
                else:
                    st.success(f"{len(resultaten)} actieve bezoeker(s) gevonden:")
                    
                    for bezoeker in resultaten:
                        bezoeker_id, naam, email, telefoon, bedrijf, bezoekt, reden, tijdstip_in, tijdstip_uit, status = bezoeker
                        
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                tijd_in = datetime.strptime(tijdstip_in, '%Y-%m-%d %H:%M:%S')
                                st.markdown(f"""
                                <div class="visitor-card">
                                    <strong style="font-size: 1.1rem;">{naam}</strong><br>
                                    <span style="color: #64748B;">{bedrijf} • Bezoekt: {bezoekt}</span><br>
                                    <span style="color: #64748B; font-size: 0.9rem;">Ingecheckt: {tijd_in.strftime('%H:%M')}</span>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("Afmelden", key=f"afmelden_{bezoeker_id}"):
                                    rows = checkout_bezoeker(bezoeker_id)
                                    if rows > 0:
                                        st.session_state.afmeld_success = True
                                        st.session_state.afgemelde_naam = naam
                                        st.rerun()
                                    else:
                                        st.error("Fout bij afmelden. Probeer opnieuw.")
            elif zoek_button:
                st.warning("Vul minimaal 2 karakters in om te zoeken")
    
    # ===== TAB 3: RECEPTIE DASHBOARD =====
    with tab3:
        st.markdown('<h1 class="section-header">Receptie Dashboard</h1>', unsafe_allow_html=True)
        
        # Refresh button
        if st.button("🔄 Ververs gegevens", key="refresh_dashboard"):
            st.rerun()
        
        # Actieve bezoekers
        st.markdown('<h2 class="section-header">Actieve bezoekers</h2>', unsafe_allow_html=True)
        actieve_bezoekers = haal_actieve_bezoekers()
        
        if len(actieve_bezoekers) == 0:
            st.info("Geen actieve bezoekers op dit moment.")
        else:
            st.metric("Totaal actief", len(actieve_bezoekers))
            
            # Toon tabel met actieve bezoekers
            for idx, row in actieve_bezoekers.iterrows():
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1.5, 2, 2, 1.5, 1])
                
                with col1:
                    st.markdown(f"**{row['naam']}**")
                with col2:
                    st.markdown(f"{row['email']}")
                with col3:
                    st.markdown(f"{row['telefoon']}")
                with col4:
                    st.markdown(f"{row['bedrijf']}")
                with col5:
                    st.markdown(f"Bezoekt: {row['bezoekt']}")
                with col6:
                    tijd = datetime.strptime(row['tijdstip_in'], '%Y-%m-%d %H:%M:%S')
                    st.markdown(f"{tijd.strftime('%H:%M')}")
                with col7:
                    if st.button("✓", key=f"checkout_{row['id']}", help="Check uit"):
                        rows = checkout_bezoeker(row['id'])
                        if rows > 0:
                            st.success(f"{row['naam']} uitgecheckt!")
                            st.rerun()
                        else:
                            st.error("Fout bij uitchecken.")
                
                st.markdown("---")
        
        # Bezoekersgeschiedenis
        st.markdown('<h2 class="section-header">Bezoekersgeschiedenis</h2>', unsafe_allow_html=True)
        
        with st.expander("Bekijk volledige geschiedenis"):
            alle_bezoekers = haal_alle_bezoekers()
            
            if len(alle_bezoekers) == 0:
                st.info("Geen bezoekersgegevens beschikbaar.")
            else:
                # Filter opties
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.selectbox(
                        "Filter op status:",
                        ["Alle", "Actief", "Uitgecheckt"]
                    )
                
                # Toepassen filters
                gefilterde_data = alle_bezoekers.copy()
                if status_filter == "Actief":
                    gefilterde_data = gefilterde_data[gefilterde_data['status'] == 'actief']
                elif status_filter == "Uitgecheckt":
                    gefilterde_data = gefilterde_data[gefilterde_data['status'] == 'uitgecheckt']
                
                # Toon gefilterde data
                st.dataframe(
                    gefilterde_data[['naam', 'email', 'telefoon', 'bedrijf', 'bezoekt', 'reden', 'tijdstip_in', 'tijdstip_uit', 'status']],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download optie
                csv = gefilterde_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download als CSV",
                    data=csv,
                    file_name=f"bezoekers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # ===== TAB 4: ADMIN & QR CODE =====
    with tab4:
        st.markdown('<h1 class="section-header">Admin & QR-Code</h1>', unsafe_allow_html=True)
        
        st.markdown('<h2 class="section-header">QR-Code Genereren</h2>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">Genereer een QR-code die bezoekers kunnen scannen om direct naar het registratieformulier te gaan.</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            url_optie = st.radio(
                "Waar wil je de QR-code voor maken?",
                ["Lokaal testen (localhost)", "Externe toegang (Streamlit Cloud/ngrok)", "Custom URL"],
                help="Kies 'Externe toegang' voor productie gebruik"
            )
            
            if url_optie == "Lokaal testen (localhost)":
                app_url = st.text_input(
                    "Lokale URL",
                    value="http://localhost:8501",
                )
                st.warning("Deze URL werkt alleen op deze computer. Voor externe toegang kies een andere optie.")
            
            elif url_optie == "Externe toegang (Streamlit Cloud/ngrok)":
                st.info("""
                **Voor externe toegang:**
                
                **Streamlit Cloud (Aanbevolen)**
                1. Deploy je app op https://streamlit.io/cloud
                2. Kopieer de URL (bijv. https://jouw-app.streamlit.app)
                3. Plak hieronder
                
                **ngrok (Tijdelijk)**
                1. Run: `ngrok http 8501`
                2. Kopieer de https URL
                3. Plak hieronder
                """)
                app_url = st.text_input(
                    "Externe URL",
                    placeholder="https://jouw-app.streamlit.app",
                )
            
            else:
                app_url = st.text_input(
                    "Custom URL",
                    placeholder="https://jouw-domein.nl",
                )
            
            if st.button("Genereer QR-Code"):
                if app_url:
                    try:
                        qr_bytes = genereer_qr_code(app_url)
                        
                        st.success("QR-Code gegenereerd!")
                        st.image(qr_bytes, caption="Scan deze QR-code voor bezoekersregistratie", width=300)
                        
                        st.download_button(
                            label="Download QR-Code",
                            data=qr_bytes,
                            file_name="tielbeke_qr_code.png",
                            mime="image/png"
                        )
                    except Exception as e:
                        st.error(f"Fout bij genereren QR-code: {str(e)}")
                else:
                    st.error("Vul een geldige URL in!")
        
        st.markdown("---")
        st.markdown('<h2 class="section-header">Statistieken</h2>', unsafe_allow_html=True)
        
        alle_bezoekers = haal_alle_bezoekers()
        actieve_bezoekers = haal_actieve_bezoekers()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totaal bezoekers", len(alle_bezoekers))
        with col2:
            st.metric("Momenteel actief", len(actieve_bezoekers))
        with col3:
            uitgecheckt = len(alle_bezoekers) - len(actieve_bezoekers)
            st.metric("Uitgecheckt", uitgecheckt)
        
        st.markdown("---")
        st.markdown('<h2 class="section-header">Database beheer</h2>', unsafe_allow_html=True)
        st.warning("Pas op: deze acties kunnen niet ongedaan worden gemaakt!")
        
        if st.button("Verwijder alle uitgecheckte bezoekers"):
            conn = sqlite3.connect('bezoekers.db')
            c = conn.cursor()
            c.execute("DELETE FROM bezoekers WHERE status='uitgecheckt'")
            conn.commit()
            conn.close()
            st.success("Alle uitgecheckte bezoekers verwijderd!")
            st.rerun()

if __name__ == "__main__":
    main()
