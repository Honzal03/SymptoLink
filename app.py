import streamlit as st
import pandas as pd
from streamlit_geolocation import streamlit_geolocation

# --- IMPORT NAŠICH VLASTNÍCH MODULŮ Z SRC_UTILS ---
from src_utils.geodata import spocitej_km
from src_utils.ai_engine import nacti_model_a_data, predikuj_obor

# --- 1. NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="SymptoLink", page_icon="🏥", layout="wide")


# --- 2. NAČTENÍ MODELU A DAT ---
# Funkci jsme obalili přes st.cache_resource, aby se moduly z ai_engine nečítaly pořád dokola
@st.cache_resource
def load_resources_cached():
    return nacti_model_a_data()


# Zobrazení načítací hlášky, než se model natáhne do paměti
with st.spinner("Načítám umělou inteligenci a databázi lékařů..."):
    embedder, clf, metadata, df_registr = load_resources_cached()

# --- 3. HLAVNÍ UŽIVATELSKÉ ROZHRANÍ (UI) ---
st.title("🏥 SymptoLink: Váš průvodce k lékaři")
st.markdown("Popište své příznaky vlastními slovy a my vám pomocí AI najdeme nejbližšího vhodného specialistu.")

# Rozdělení obrazovky na dva sloupce
col1, col2 = st.columns([2, 1])

with col1:
    st.info("🔎 Jak chcete vyhledávat?")
    hledani_volba = st.radio("Metoda vyhledávání:",
                             ["💡 Popsat potíže (AI vybere vhodného specialistu)", "📋 Vybrat konkrétní obor ze seznamu"],
                             label_visibility="collapsed")

    if "AI" in hledani_volba:
        user_input = st.text_area("Jaké máte potíže?",
                                  placeholder="Např.: Hrozně mě bolí koleno a nemůžu na něj došlápnout.", height=150)
        vybrany_obor = None
    else:
        user_input = ""
        vsechny_obory = sorted(
            df_registr['OborPece_List'].dropna().astype(str).str.split(',').explode().str.strip().unique())
        vsechny_obory = [o for o in vsechny_obory if o != ""]

        vybrany_obor = st.selectbox("Vyberte hledaný lékařský obor:", vsechny_obory)

with col2:
    st.info("📍 Kde hledat lékaře?")
    lokace_volba = st.radio("Způsob zadání polohy:", ["Vybrat město ze seznamu", "Použít moji přesnou GPS"])

    if lokace_volba == "Vybrat město ze seznamu":
        mesta_gps = {
            "Praha": (50.0880, 14.4208), "Brno": (49.1951, 16.6068), "Ostrava": (49.8209, 18.2625),
            "Plzeň": (49.7384, 13.3736), "Liberec": (50.7671, 15.0562), "Olomouc": (49.5938, 17.2509),
            "České Budějovice": (48.9745, 14.4743), "Hradec Králové": (50.2104, 15.8328),
            "Ústí nad Labem": (50.6607, 14.0322), "Pardubice": (50.0343, 15.7720), "Zlín": (49.2265, 17.6670),
            "Jihlava": (49.3961, 15.5904), "Karlovy Vary": (50.2327, 12.8712), "Kladno": (50.1473, 14.1029),
            "Havířov": (49.7839, 18.4250), "Mladá Boleslav": (50.4113, 14.9032), "Opava": (49.9387, 17.9026),
            "Frýdek-Místek": (49.6833, 18.3500)
        }
        vybrane_mesto = st.selectbox("Vyberte výchozí město:", list(mesta_gps.keys()))
        moje_poloha = mesta_gps[vybrane_mesto]

    else:
        st.write("Klikněte na tlačítko pro zaměření:")
        loc = streamlit_geolocation()
        if loc['latitude'] is not None and loc['longitude'] is not None:
            moje_poloha = (float(loc['latitude']), float(loc['longitude']))
            st.success("Poloha zaměřena!")
        else:
            moje_poloha = (50.0880, 14.4208)
            st.caption("Zatím nastavena Praha. Povolte zaměření v prohlížeči.")

st.markdown("---")

# --- 4. LOGIKA VYHLEDÁVÁNÍ (Spustí se po kliknutí na tlačítko) ---
if st.button("Vyhledat nejbližšího lékaře", type="primary"):
    if "AI" in hledani_volba and user_input.strip() == "":
        st.error("Prosím, popište nejprve své potíže.")
    else:
        with st.spinner('Vyhledávám v registru lékařů...'):

            search_specialties = []
            ai_nejista = False

            if "AI" in hledani_volba:
                # Voláme naši novou funkci z ai_engine.py!
                search_specialties = predikuj_obor(user_input, embedder, clf, metadata)

                if not search_specialties:  # Znamená to, že vrátil prázdný seznam
                    ai_nejista = True
                else:
                    st.success(f"**AI doporučuje tyto obory:** {', '.join(search_specialties).title()}")
            else:
                search_specialties = [vybrany_obor]
                st.success(f"**Hledaný obor:** {vybrany_obor}")

            if ai_nejista:
                st.warning(
                    "⚠️ AI si není jistá. Zkuste příznaky popsat podrobněji, nebo využijte druhou možnost a obor si vyberte ručně ze seznamu.")
            else:
                pattern = '|'.join(search_specialties)
                mask = df_registr['OborPece_List'].str.contains(pattern, case=False, na=False)
                vysledky = df_registr[mask].copy()

                if vysledky.empty:
                    st.info("V registru nebyl nalezen žádný odpovídající lékař v tomto oboru.")
                else:
                    # Voláme naši funkci spocitej_km z geodata.py
                    vysledky['vzdalenost_km'] = vysledky['GPS'].apply(lambda x: spocitej_km(moje_poloha, x))

                    # Seřazení a vybrání TOP 10 (jak jsi to měl ve svém kódu)
                    top_vysledky = vysledky.sort_values('vzdalenost_km').drop_duplicates(subset=['NazevCely'],
                                                                                         keep='first').head(10)

                    # --- ZOBRAZENÍ VÝSLEDKŮ A MAPY ---
                    res_col, map_col = st.columns([1, 1])

                    with res_col:
                        st.subheader("Nejbližší doporučené ordinace:")
                        for _, doc in top_vysledky.iterrows():
                            with st.expander(f"🏥 {doc['NazevCely']} ({doc['vzdalenost_km']:.1f} km)"):
                                st.write(f"**Adresa:** {doc['Ulice']}, {doc['Obec']}")
                                st.write(f"**Specializace:** {doc['OborPece_List']}")

                                telefon = str(doc.get('PoskytovatelTelefon', 'nan')).replace('.0', '')
                                if telefon != 'nan' and telefon.strip() != '':
                                    st.write(f"📞 **Telefon:** {telefon}")

                                email = str(doc.get('PoskytovatelEmail', 'nan'))
                                if email != 'nan' and email.strip() != '':
                                    st.write(f"📧 **E-mail:** {email}")

                                web = str(doc.get('PoskytovatelWeb', 'nan'))
                                if web != 'nan' and web.strip() != '':
                                    odkaz = f"http://{web}" if not web.startswith('http') else web
                                    st.write(f"🌐 **Web:** [{web}]({odkaz})")

                                try:
                                    gps_parts = str(doc['GPS']).strip().split()
                                    if len(gps_parts) == 2:
                                        url_mapy = f"https://www.google.com/maps/dir/?api=1&origin={moje_poloha[0]},{moje_poloha[1]}&destination={gps_parts[0]},{gps_parts[1]}"
                                        st.link_button("🗺️ Navigovat (Google Maps)", url_mapy)
                                except:
                                    pass

                    with map_col:
                        st.subheader("Mapa (Lékaři a vaše poloha)")
                        map_data = [{'lat': moje_poloha[0], 'lon': moje_poloha[1], 'color': '#0000ff', 'size': 150}]

                        for _, row in top_vysledky.iterrows():
                            try:
                                parts = str(row['GPS']).strip().split()
                                map_data.append(
                                    {'lat': float(parts[0]), 'lon': float(parts[1]), 'color': '#ff0000', 'size': 150})
                            except:
                                pass

                        st.map(pd.DataFrame(map_data), color='color', size='size', zoom=10)