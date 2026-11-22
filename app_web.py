import streamlit as st
import json
import requests
from datetime import datetime
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="Registro Lezioni di Pianoforte", page_icon="🎹", layout="wide")

# --- 1. GESTIONE LOGIN TRAMITE SECRETS ---
def controlla_accesso():
    if "ruolo" not in st.session_state:
        st.session_state["ruolo"] = None

    if st.session_state["ruolo"] is None:
        st.title("🎹 Registro Lezioni di Pianoforte")
        st.subheader("Accesso Riservato")
        
        pwd = st.text_input("Inserisci la password di accesso:", type="password")
        if st.button("Accedi", type="primary"):
            if pwd == st.secrets["password_maestro"]:
                st.session_state["ruolo"] = "maestro"
                st.rerun()
            elif pwd == st.secrets["password_studente"]:
                st.session_state["ruolo"] = "studente"
                st.rerun()
            else:
                st.error("❌ Password errata. Riprova.")
        st.stop()

controlla_accesso()
is_maestro = (st.session_state["ruolo"] == "maestro")

# --- 2. DATABASE PERMANENTE SU GITHUB GIST ---
GIST_ID = st.secrets["gist_id"]
GITHUB_TOKEN = st.secrets["github_token"]
FILENAME = "archivio_allievi.json"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def carica_dati():
    if "allievi" not in st.session_state:
        try:
            url = f"https://github.com{GIST_ID}"
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                contenuto = res.json()["files"][FILENAME]["content"]
                st.session_state["allievi"] = json.loads(contenuto)
            else:
                st.session_state["allievi"] = {}
        except Exception as e:
            st.error(f"Errore di connessione al database: {e}")
            st.session_state["allievi"] = {}
    return st.session_state["allievi"]

def salva_dati_cloud(dati_aggiornati):
    st.session_state["allievi"] = dati_aggiornati
    url = f"https://github.com{GIST_ID}"
    payload = {
        "files": {
            FILENAME: {
                "content": json.dumps(dati_aggiornati, ensure_ascii=False, indent=4)
            }
        }
    }
    res = requests.patch(url, headers=HEADERS, json=payload)
    if res.status_code != 200:
        st.error("⚠️ Errore durante il salvataggio online!")

allievi = carica_dati()

# --- 3. GENERAZIONE PDF ---
def pulisci_testo_pdf(testo):
    for k, v in {"’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."}.items():
        testo = testo.replace(k, v)
    return testo.encode("latin-1", "replace").decode("latin-1")

def crea_pdf_bytes(nome_allievo, dati):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 11, pulisci_testo_pdf(f"PIANOFORTE - {nome_allievo}"), new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 11)
    info_riga = f"Livello: {dati.get('livello') or '---'}  |  Orario: {dati.get('orario') or '---'}  |  Data: {dati.get('data') or '---'}"
    pdf.cell(0, 7, pulisci_testo_pdf(info_riga), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(180, 190, 200)
    pdf.set_font("Helvetica", "B", 10)
    riga_tecnica_pdf = f"  METRONOMO: {dati.get('bpm') or '---'}    |    PEDALE: {dati.get('pedale') or '---'}    |    TOCCO: {dati.get('tocco') or '---'}"
    pdf.cell(0, 10, pulisci_testo_pdf(riga_tecnica_pdf), border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(6)
    
    for titolo, chiave in [("TECNICA, SCALE ED ESERCIZI", "tecnica"), ("BRANI IN STUDIO E OBIETTIVI", "brani")]:
        pdf.set_fill_color(230, 238, 248)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, pulisci_testo_pdf(f"  {titolo}"), new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 7, pulisci_testo_pdf(dati.get(chiave) or "Nessuna nota inserita."))
        pdf.ln(5)
        
    pdf.set_fill_color(230, 238, 248)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, pulisci_testo_pdf("  COMPITI PER CASA (Spuntare al controllo)"), new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 12)
    
    if dati.get("compiti"):
        for riga in dati["compiti"].splitlines():
            riga_pulita = riga.strip()
            if riga_pulita:
                x_box = pdf.get_x() + 2
                y_box = pdf.get_y() + 1.5
                pdf.rect(x_box, y_box, 4, 4)
                pdf.set_x(x_box + 7)
                pdf.multi_cell(0, 7, pulisci_testo_pdf(riga_pulita))
                pdf.ln(1)
    else:
        pdf.multi_cell(0, 7, "Nessun compito assegnato.")
        
    return bytes(pdf.output())

# --- 4. BARRA LATERALE ---
with st.sidebar:
    st.title("🎹 Allievi")
    st.caption(f"Accesso effettuato come: **{st.session_state['ruolo'].upper()}**")
    
    if is_maestro:
        nuovo_nome = st.text_input("Nome e Cognome...", key="input_nuovo_allievo")
        if st.button("➕ Aggiungi Allievo", type="primary", use_container_width=True):
            nome_pulito = nuovo_nome.strip()
            if nome_pulito:
                if nome_pulito in allievi:
                    st.warning("Allievo già presente!")
                else:
                    allievi[nome_pulito] = {
                        "livello": "", "orario": "", "telefono": "",
                        "data": datetime.now().strftime("%d/%m/%Y"),
                        "bpm": "", "pedale": "", "tocco": "",
                        "tecnica": "", "brani": "", "compiti": "",
                        "storico": []
                    }
                    salva_dati_cloud(allievi)
                    st.session_state["allievo_attivo"] = nome_pulito
                    st.rerun()

    st.divider()
    st.subheader("I tuoi allievi")
    
    lista_nomi = sorted(allievi.keys())
    if not lista_nomi:
        st.info("Nessun allievo in lista.")
        allievo_selezionato = None
    else:
        indice_default = 0
        if "allievo_attivo" in st.session_state and st.session_state["allievo_attivo"] in lista_nomi:
            indice_default = lista_nomi.index(st.session_state["allievo_attivo"])
        allievo_selezionato = st.radio("Seleziona allievo:", lista_nomi, index=indice_default, label_visibility="collapsed")
        st.session_state["allievo_attivo"] = allievo_selezionato

    st.divider()
    if is_maestro:
        with st.expander("💾 Backup Manuale (.json)"):
            json_str = json.dumps(allievi, ensure_ascii=False, indent=4)
            st.download_button("⬇️ Scarica Archivio", data=json_str, file_name="archivio_allievi.json", mime="application/json", use_container_width=True)
            
            file_caricato = st.file_uploader("⬆️ Ripristina da JSON", type=["json"])
            if file_caricato is not None:
                if st.button("Conferma Ripristino", use_container_width=True):
                    dati_importati = json.load(file_caricato)
                    salva_dati_cloud(dati_importati)
                    st.success("Archivio ripristinato!")
                    st.rerun()

    if st.button("🚪 Esci (Logout)", use_container_width=True):
        st.session_state["ruolo"] = None
        st.rerun()

# --- 5. AREA PRINCIPALE ---
if not allievo_selezionato:
    st.title("Registro Lezioni di Pianoforte")
    st.info("👈 Seleziona un allievo dalla barra a sinistra (su tablet/cellulare premi la freccia `>` in alto a sinistra per aprire il menu).")
else:
    dati_allievo = allievi[allievo_selezionato]
    
    col_titolo, col_storico = st.columns([2, 1])
    with col_titolo:
        st.title(f"Scheda di: {allievo_selezionato}")
    with col_storico:
        storico = dati_allievo.get("storico", [])
        opzioni_storico = ["📌 Scheda Attuale (In corso)"] + [
            f"{i+1}. {item.get('data_salvataggio', 'Senza data')}" for i, item in enumerate(storico)
        ]
        scelta_storico = st.selectbox("Storico lezioni:", opzioni_storico)

    if scelta_storico == "📌 Scheda Attuale (In corso)":
        dati_mostrati = dati_allievo
        in_storico = False
    else:
        indice_st = int(scelta_storico.split(".")[0]) - 1
        dati_mostrati = storico[indice_st]
        in_storico = True
        st.warning(f"Stai visualizzando una lezione archiviata ({scelta_storico}).")

    disabilitato = (not is_maestro) or in_storico

    c1, c2, c3, c4 = st.columns(4)
    livello = c1.text_input("Livello / Corso:", value=dati_mostrati.get("livello", ""), placeholder="Es. Base, 2° Anno...", disabled=disabilitato)
    orario = c2.text_input("Giorno e Ora Fissa:", value=dati_mostrati.get("orario", ""), placeholder="Es. Giovedì 16:30", disabled=disabilitato)
    if is_maestro:
        telefono = c3.text_input("Telefono / Contatto:", value=dati_mostrati.get("telefono", ""), placeholder="Es. 333 1234567", disabled=disabilitato)
    else:
        telefono = dati_mostrati.get("telefono", "")
        c3.text_input("Telefono:", value="Riservato", disabled=True)
    data_lez = c4.text_input("Data Lezione:", value=dati_mostrati.get("data", ""), placeholder="Es. 20/11/2026", disabled=disabilitato)

    st.markdown("---")
    t1, t2, t3 = st.columns(3)
    bpm = t1.text_input("Metronomo (BPM):", value=dati_mostrati.get("bpm", ""), placeholder="Es. 72 -> 84 BPM", disabled=disabilitato)
    pedale = t2.text_input("Uso Pedale:", value=dati_mostrati.get("pedale", ""), placeholder="Es. Legato / Mezzo pedale", disabled=disabilitato)
    tocco = t3.text_input("Focus Tocco (Tasti Pesati):", value=dati_mostrati.get("tocco", ""), placeholder="Es. Peso braccio / Polso morbido", disabled=disabilitato)

