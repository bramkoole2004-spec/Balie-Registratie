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

4. Voor QR-code: gebruik de 'Admin' tab om een QR-code te genereren
   met de URL van je gedeployde app (of lokale URL voor testen)

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

# ===== DATABASE SETUP =====
def init_database():
    """Initialiseer SQLite database met bezoekers tabel"""
    conn = sqlite3.connect('bezoekers.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bezoekers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
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

# ===== DATABASE FUNCTIES =====
def voeg_bezoeker_toe(naam, bedrijf, bezoekt, reden):
    """Voeg nieuwe bezoeker toe aan database"""
    conn = sqlite3.connect('bezoekers.db')
    c = conn.cursor()
    tijdstip = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO bezoekers (naam, bedrijf, bezoekt, reden, tijdstip_in, status)
        VALUES (?, ?, ?, ?, ?, 'actief')
    ''', (naam, bedrijf, bezoekt, reden, tijdstip))
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

def zoek_actieve_bezoeker(naam):
    """Zoek actieve bezoeker op naam"""
    conn = sqlite3.connect('bezoekers.db')
    c = conn.cursor()
    c.execute(
        "SELECT * FROM bezoekers WHERE naam LIKE ? AND status='actief' ORDER BY tijdstip_in DESC LIMIT 5",
        (f'%{naam}%',)
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
    img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    
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
    
    # Custom CSS voor professionele styling
    st.markdown("""
        <style>
        .main {
            background-color: #F0F4F8;
        }
        .stButton>button {
            width: 100%;
            background-color: #1E3A8A;
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 15px;
            border-radius: 10px;
            border: none;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #2563EB;
            transform: scale(1.02);
        }
        .success-box {
            background-color: #D1FAE5;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #10B981;
            margin: 20px 0;
        }
        .goodbye-box {
            background-color: #FEF3C7;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #F59E0B;
            margin: 20px 0;
        }
        .welcome-header {
            text-align: center;
            color: #1E3A8A;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #64748B;
            font-size: 1.2em;
            margin-bottom: 30px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Tabs voor verschillende interfaces
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Aanmelden", 
        "👋 Afmelden",
        "🖥️ Receptie Dashboard", 
        "⚙️ Admin & QR-Code"
    ])
    
    # ===== TAB 1: BEZOEKERSREGISTRATIE (AANMELDEN) =====
    with tab1:
        st.markdown('<div class="welcome-header">🏢 Welkom bij Tielbeke</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Registreer jezelf als bezoeker</div>', unsafe_allow_html=True)
        
        # Check of er een success message moet worden getoond
        if 'registratie_success' in st.session_state and st.session_state.registratie_success:
            st.markdown(f"""
                <div class="success-box">
                    <h2 style="color: #10B981; margin: 0;">✅ Welkom bij Tielbeke, {st.session_state.bezoeker_naam}!</h2>
                    <p style="margin: 10px 0 0 0; font-size: 1.1em;">
                        Je registratie is succesvol ontvangen. Iemand van ons team komt je zo ophalen. 
                        Voel je vrij om plaats te nemen in de wachtruimte. ☕
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 0.9em; color: #059669;">
                        💡 <strong>Tip:</strong> Vergeet niet jezelf af te melden bij vertrek via het "Afmelden" tabblad!
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("➕ Nieuwe bezoeker registreren"):
                st.session_state.registratie_success = False
                st.rerun()
        else:
            # Registratieformulier
            with st.form("bezoeker_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    naam = st.text_input(
                        "👤 Volledige naam *",
                        placeholder="bijv. Jan Jansen",
                        help="Vul je voor- en achternaam in"
                    )
                    bezoekt = st.text_input(
                        "🎯 Wie bezoek je? *",
                        placeholder="bijv. Piet Pietersen",
                        help="Naam van de persoon die je komt bezoeken"
                    )
                
                with col2:
                    bedrijf = st.text_input(
                        "🏭 Bedrijf/Organisatie *",
                        placeholder="bijv. ABC Consulting",
                        help="Naam van je bedrijf of organisatie"
                    )
                    reden = st.text_input(
                        "📋 Reden van bezoek *",
                        placeholder="bijv. Zakelijke bespreking",
                        help="Korte beschrijving van je bezoek"
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit_button = st.form_submit_button("✅ Aanmelden")
                
                if submit_button:
                    # Validatie
                    if not naam or not bedrijf or not bezoekt or not reden:
                        st.error("❌ Alle velden zijn verplicht! Vul alle gegevens in.")
                    elif len(naam.strip()) < 2:
                        st.error("❌ Vul een geldige naam in (minimaal 2 karakters).")
                    else:
                        # Opslaan in database
                        try:
                            bezoeker_id = voeg_bezoeker_toe(
                                naam.strip(),
                                bedrijf.strip(),
                                bezoekt.strip(),
                                reden.strip()
                            )
                            st.session_state.registratie_success = True
                            st.session_state.bezoeker_naam = naam.strip()
                            st.session_state.bezoeker_id = bezoeker_id
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Er is een fout opgetreden: {str(e)}")
            
            st.markdown("---")
            st.info("ℹ️ **Privacy**: Je gegevens worden alleen gebruikt voor bezoekersregistratie en worden beveiligd opgeslagen.")
    
    # ===== TAB 2: AFMELDEN =====
    with tab2:
        st.markdown('<div class="welcome-header">👋 Afmelden</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Meld jezelf af bij het verlaten van het pand</div>', unsafe_allow_html=True)
        
        # Check of er een afmeld success message moet worden getoond
        if 'afmeld_success' in st.session_state and st.session_state.afmeld_success:
            st.markdown(f"""
                <div class="goodbye-box">
                    <h2 style="color: #D97706; margin: 0;">👋 Tot ziens, {st.session_state.afgemelde_naam}!</h2>
                    <p style="margin: 10px 0 0 0; font-size: 1.1em;">
                        Je bent succesvol afgemeld. Bedankt voor je bezoek aan Tielbeke!
                        We hopen je snel weer te zien. 🚗
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("➕ Nog een persoon afmelden"):
                st.session_state.afmeld_success = False
                st.rerun()
        else:
            st.info("👇 Zoek jezelf op en meld je af bij vertrek")
            
            # Zoekformulier
            with st.form("afmeld_form"):
                zoek_naam = st.text_input(
                    "🔍 Zoek op naam",
                    placeholder="Typ je naam...",
                    help="Typ minimaal 2 letters van je naam"
                )
                zoek_button = st.form_submit_button("🔍 Zoeken")
            
            if zoek_button and zoek_naam and len(zoek_naam.strip()) >= 2:
                resultaten = zoek_actieve_bezoeker(zoek_naam)
                
                if len(resultaten) == 0:
                    st.warning(f"❌ Geen actieve bezoekers gevonden met de naam '{zoek_naam}'")
                else:
                    st.success(f"✅ {len(resultaten)} actieve bezoeker(s) gevonden:")
                    
                    for bezoeker in resultaten:
                        bezoeker_id, naam, bedrijf, bezoekt, reden, tijdstip_in, tijdstip_uit, status = bezoeker
                        
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                tijd_in = datetime.strptime(tijdstip_in, '%Y-%m-%d %H:%M:%S')
                                st.markdown(f"""
                                **👤 {naam}**  
                                🏭 {bedrijf} | 🎯 Bezoekt: {bezoekt}  
                                🕐 Ingecheckt om: {tijd_in.strftime('%H:%M')}
                                """)
                            
                            with col2:
                                if st.button("👋 Afmelden", key=f"afmelden_{bezoeker_id}"):
                                    rows = checkout_bezoeker(bezoeker_id)
                                    if rows > 0:
                                        st.session_state.afmeld_success = True
                                        st.session_state.afgemelde_naam = naam
                                        st.rerun()
                                    else:
                                        st.error("❌ Fout bij afmelden. Probeer opnieuw.")
                            
                            st.markdown("---")
            elif zoek_button:
                st.warning("⚠️ Vul minimaal 2 letters in om te zoeken")
        
        st.markdown("---")
        st.markdown("**💡 Tips voor afmelden:**")
        st.markdown("""
        - Typ je voor- of achternaam in het zoekveld
        - Klik op de juiste persoon als er meerdere resultaten zijn
        - Druk op "Afmelden" om jezelf uit te checken
        """)
    
    # ===== TAB 3: RECEPTIE DASHBOARD =====
    with tab3:
        st.markdown("## 🖥️ Receptie Dashboard")
        st.markdown("*Beheer actieve bezoekers en bekijk bezoekersgeschiedenis*")
        
        # Refresh button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("🔄 Ververs gegevens"):
                st.rerun()
        
        # Actieve bezoekers
        st.markdown("### 📊 Actieve bezoekers")
        actieve_bezoekers = haal_actieve_bezoekers()
        
        if len(actieve_bezoekers) == 0:
            st.info("📭 Geen actieve bezoekers op dit moment.")
        else:
            st.metric("Totaal actief", len(actieve_bezoekers), delta=None)
            
            # Toon tabel met actieve bezoekers
            for idx, row in actieve_bezoekers.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**👤 {row['naam']}**")
                    with col2:
                        st.markdown(f"🏭 {row['bedrijf']}")
                    with col3:
                        st.markdown(f"🎯 {row['bezoekt']}")
                    with col4:
                        st.markdown(f"📋 {row['reden']}")
                    with col5:
                        tijd = datetime.strptime(row['tijdstip_in'], '%Y-%m-%d %H:%M:%S')
                        st.markdown(f"🕐 {tijd.strftime('%H:%M')}")
                    with col6:
                        if st.button("✅", key=f"checkout_{row['id']}", help="Check uit"):
                            checkout_bezoeker(row['id'])
                            st.success(f"✅ {row['naam']} uitgecheckt!")
                            st.rerun()
                    
                    st.markdown("---")
        
        # Bezoekersgeschiedenis
        st.markdown("### 📚 Bezoekersgeschiedenis")
        
        with st.expander("📖 Bekijk volledige geschiedenis"):
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
                with col2:
                    datum_filter = st.date_input("Filter op datum (optioneel):")
                
                # Toepassen filters
                gefilterde_data = alle_bezoekers.copy()
                if status_filter == "Actief":
                    gefilterde_data = gefilterde_data[gefilterde_data['status'] == 'actief']
                elif status_filter == "Uitgecheckt":
                    gefilterde_data = gefilterde_data[gefilterde_data['status'] == 'uitgecheckt']
                
                # Toon gefilterde data
                st.dataframe(
                    gefilterde_data[['naam', 'bedrijf', 'bezoekt', 'reden', 'tijdstip_in', 'tijdstip_uit', 'status']],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download optie
                csv = gefilterde_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download als CSV",
                    data=csv,
                    file_name=f"bezoekers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # ===== TAB 4: ADMIN & QR CODE =====
    with tab4:
        st.markdown("## ⚙️ Admin & QR-Code Generatie")
        
        st.markdown("### 📱 QR-Code Genereren")
        st.info("Genereer een QR-code die bezoekers kunnen scannen om direct naar het registratieformulier te gaan.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Probeer automatisch de externe URL te detecteren
            default_url = "http://localhost:8501"
            
            st.markdown("**🌐 Kies je URL optie:**")
            url_optie = st.radio(
                "Waar wil je de QR-code voor maken?",
                ["Lokaal testen (localhost)", "Externe toegang (ngrok/Streamlit Cloud)", "Custom URL"],
                help="Kies 'Externe toegang' voor productie gebruik"
            )
            
            if url_optie == "Lokaal testen (localhost)":
                app_url = st.text_input(
                    "🏠 Lokale URL",
                    value="http://localhost:8501",
                    help="Alleen voor testen op dezelfde computer"
                )
                st.warning("⚠️ Deze URL werkt alleen op deze computer. Voor externe toegang kies een andere optie.")
            
            elif url_optie == "Externe toegang (ngrok/Streamlit Cloud)":
                st.info("""
                **📱 Voor externe toegang heb je 2 opties:**
                
                **Optie 1: Streamlit Cloud (Aanbevolen)**
                1. Ga naar https://streamlit.io/cloud
                2. Upload je app (gratis)
                3. Kopieer de URL (bijv. https://jouw-app.streamlit.app)
                4. Plak hieronder
                
                **Optie 2: ngrok (Tijdelijk, voor testen)**
                1. Download ngrok: https://ngrok.com/download
                2. Run in nieuwe terminal: `ngrok http 8501`
                3. Kopieer de https URL (bijv. https://abc123.ngrok.io)
                4. Plak hieronder
                """)
                app_url = st.text_input(
                    "🌍 Externe URL",
                    placeholder="https://jouw-app.streamlit.app of https://abc123.ngrok.io",
                    help="Vul hier je Streamlit Cloud of ngrok URL in"
                )
            
            else:  # Custom URL
                app_url = st.text_input(
                    "🔗 Custom URL",
                    placeholder="https://jouw-domein.nl",
                    help="Vul je eigen URL in"
                )
            
            if st.button("🎨 Genereer QR-Code"):
                if app_url:
                    try:
                        qr_bytes = genereer_qr_code(app_url)
                        
                        st.success("✅ QR-Code gegenereerd!")
                        st.image(qr_bytes, caption="Scan deze QR-code voor bezoekersregistratie", width=300)
                        
                        st.download_button(
                            label="📥 Download QR-Code",
                            data=qr_bytes,
                            file_name="tielbeke_qr_code.png",
                            mime="image/png"
                        )
                    except Exception as e:
                        st.error(f"❌ Fout bij genereren QR-code: {str(e)}")
                        st.write("Debug info:", type(e).__name__)
                else:
                    st.error("❌ Vul een geldige URL in!")
        
        with col2:
            st.markdown("**💡 Tips:**")
            st.markdown("""
            - Print de QR-code en hang deze bij de ingang
            - Voor testen: gebruik localhost URL
            - Voor productie: deploy naar Streamlit Cloud
            - Zorg dat de URL toegankelijk is voor bezoekers
            """)
        
        st.markdown("---")
        st.markdown("### 📊 Statistieken")
        
        alle_bezoekers = haal_alle_bezoekers()
        actieve_bezoekers = haal_actieve_bezoekers()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totaal bezoekers (vandaag)", len(alle_bezoekers))
        with col2:
            st.metric("Momenteel actief", len(actieve_bezoekers))
        with col3:
            uitgecheckt = len(alle_bezoekers) - len(actieve_bezoekers)
            st.metric("Uitgecheckt", uitgecheckt)
        
        st.markdown("---")
        st.markdown("### 🗑️ Database beheer")
        st.warning("⚠️ Pas op: deze acties kunnen niet ongedaan worden gemaakt!")
        
        if st.button("🗑️ Verwijder alle uitgecheckte bezoekers"):
            conn = sqlite3.connect('bezoekers.db')
            c = conn.cursor()
            c.execute("DELETE FROM bezoekers WHERE status='uitgecheckt'")
            conn.commit()
            conn.close()
            st.success("✅ Alle uitgecheckte bezoekers verwijderd!")
            st.rerun()

if __name__ == "__main__":
    main()
