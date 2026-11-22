import streamlit as st
import json
import requests
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Registro Lezioni di Pianoforte", page_icon="🎹", layout="wide")

# --- 1. CONNESSIONE AL DATABASE GITHUB GIST ---
GIST_ID = st.secrets["gist_id"]
GITHUB_TOKEN = st.secrets["github_token"]
FILENAME = "archivio_allievi.json"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def carica_dati():
    if "db" not in st.session_state:
        try:
            url = "https://github.com" + GIST_ID
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                contenuto = res.json()["files"][FILENAME]["content"]
                dati_grezzi = json.loads(contenuto)
                if "_config" not in dati_grezzi:
                    dati_grezzi = {
                        "_config": {"password_maestro": st.secrets["password_maestro_iniziale"]},
                        "allievi": dati_grezzi
                    }
                st.session_state["db"] = dati_grezzi
            else:
                st.session_state["db"] = {
                    "_config": {"password_maestro": st.secrets["password_maestro_iniziale"]},
                    "allievi": {}
                }
        except Exception as e:
            st.error(f"Errore di connessione al database: {e}")
            st.session_state["db"] = {
                "_config": {"password_maestro": st.secrets["password_maestro_iniziale"]},
                "allievi": {}
            }
    return st.session_state["db"]

def salva_dati_cloud(db_aggiornato):
    st.session_state["db"] = db_aggiornato
    url = "https://github.com" + GIST_ID
    payload = {
        "files": {
            FILENAME: {
                "content": json.dumps(db_aggiornato, ensure_ascii=False, indent=4)
            }
        }
    }
    res = requests.patch(url, headers=HEADERS, json=payload)
    if res.status_code != 200:
        st.error("⚠️ Errore durante il salvataggio online!")

db = carica_dati()
allievi = db["allievi"]

# --- 2. SISTEMA DI LOGIN E RECUPERO PASSWORD ---
def controlla_accesso():
    if "ruolo" not in st.session_state:
        st.session_state["ruolo"] = None
        st.session_state["utente_loggato"] = None

    if st.session_state["ruolo"] is None:
        st.title("🎹 Registro Lezioni di Pianoforte")
        st.subheader("Accesso Riservato - Conservatorio")
        
        pwd = st.text_input("Inserisci la tua password personale:", type="password")
        if st.button("Accedi", type="primary"):
            pwd_pulita = pwd.strip()
            pwd_maestro_attuale = db["_config"].get("password_maestro", st.secrets["password_maestro_iniziale"])
            
            if pwd_pulita and pwd_pulita == pwd_maestro_attuale:
                st.session_state["ruolo"] = "maestro"
                st.session_state["utente_loggato"] = "Maestro"
                st.rerun()
            
            allievo_trovato = None
            for nome_allievo, info in allievi.items():
                pwd_allievo = info.get("password", "").strip()
                if pwd_pulita and pwd_allievo and pwd_pulita == pwd_allievo:
                    allievo_trovato = nome_allievo
                    break
            
            if allievo_trovato:
                st.session_state["ruolo"] = "studente"
                st.session_state["utente_loggato"] = allievo_trovato
                st.rerun()
            else:
                st.error("❌ Password non riconosciuta. Controlla di averla scritta correttamente.")

        st.markdown("---")
        with st.expander("❓ Hai dimenticato la password?"):
            st.info("👨‍🎓 **Sei un Allievo?** Chiedi al Maestro durante la lezione o via messaggio: può visualizzare o reimpostare la tua password in pochi secondi dalla sua area riservata.")
            
            st.markdown("🎼 **Sei il Maestro?** Inserisci il Codice di Emergenza (PIN) per impostare una nuova password:")
            pin_inserito = st.text_input("Codice di Emergenza (PIN):", type="password", key="pin_reset")
            nuova_pwd_maestro = st.text_input("Nuova password Maestro:", type="password", key="new_pwd_reset")
            conferma_pwd_maestro = st.text_input("Ripeti nuova password Maestro:", type="password", key="conf_pwd_reset")
            
            if st.button("Reimposta Password Maestro"):
                pin_corretto = st.secrets.get("pin_recupero_maestro", "")
                if not pin_corretto or pin_inserito.strip() != pin_corretto:
                    st.error("❌ Codice di emergenza errato.")
                elif not nuova_pwd_maestro.strip():
                    st.error("❌ Inserisci una nuova password valida.")
                elif nuova_pwd_maestro.strip() != conferma_pwd_maestro.strip():
                    st.error("❌ Le due password non coincidono.")
                else:
                    db["_config"]["password_maestro"] = nuova_pwd_maestro.strip()
                    salva_dati_cloud(db)
                    st.success("✅ Password Maestro reimpostata con successo! Ora puoi accedere qui sopra.")

        st.stop()

controlla_accesso()
is_maestro = (st.session_state["ruolo"] == "maestro")

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
    if is_maestro:
        st.title("🎹 Area Maestro")
        nuovo_nome = st.text_input("Nome e Cognome Allievo...", key="input_nuovo_allievo")
        nuova_pwd_allievo = st.text_input("Password iniziale per l'allievo...", key="input_pwd_allievo")
        
        if st.button("➕ Aggiungi Allievo", type="primary", use_container_width=True):
            nome_pulito = nuovo_nome.strip()
            pwd_all_pulita = nuova_pwd_allievo.strip()
            if not nome_pulito:
                st.warning("Inserisci il nome dell'allievo.")
            elif nome_pulito in allievi:
                st.warning("Allievo già presente!")
            else:
                db["allievi"][nome_pulito] = {
                    "password": pwd_all_pulita,
                    "livello": "", "orario": "", "telefono": "",
                    "data": datetime.now().strftime("%d/%m/%Y"),
                    "bpm": "", "pedale": "", "tocco": "",
                    "tecnica": "", "brani": "", "compiti": "",
                    "storico": []
                }
                salva_dati_cloud(db)
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
    else:
        allievo_selezionato = st.session_state["utente_loggato"]
        st.title("🎹 Area Allievo")
        st.success(f"Benvenuto/a,\n**{allievo_selezionato}**")
        st.caption("Stai visualizzando esclusivamente il tuo piano di studio personale.")

    st.divider()
    
    with st.expander("🔑 Cambia la mia Password"):
        nuova_pass = st.text_input("Nuova password:", type="password", key="change_pwd_1")
        conferma_pass = st.text_input("Ripeti nuova password:", type="password", key="change_pwd_2")
        if st.button("Aggiorna Password", use_container_width=True):
            np = nuova_pass.strip()
            if not np:
                st.error("La password non può essere vuota.")
            elif np != conferma_pass.strip():
                st.error("Le due password non coincidono.")
            else:
                gia_usata = (np == db["_config"].get("password_maestro")) or any(
                    info.get("password") == np for k, info in allievi.items() if k != allievo_selezionato
                )
                if gia_usata:
                    st.error("Questa password non è disponibile, scegline un'altra.")
                else:
                    if is_maestro:
                        db["_config"]["password_maestro"] = np
                    else:
                        db["allievi"][allievo_selezionato]["password"] = np
                    salva_dati_cloud(db)
                    st.success("✅ Password aggiornata con successo!")

    if is_maestro:
        with st.expander("💾 Backup Manuale (.json)"):
            json_str = json.dumps(db, ensure_ascii=False, indent=4)
            st.download_button("⬇️ Scarica Archivio", data=json_str, file_name="archivio_conservatorio.json", mime="application/json", use_container_width=True)
            
            file_caricato = st.file_uploader("⬆️ Ripristina da JSON", type=["json"])
            if file_caricato is not None:
                if st.button("Conferma Ripristino", use_container_width=True):
                    dati_importati = json.load(file_caricato)
                    if "_config" not in dati_importati:
                        dati_importati = {
                            "_config": {"password_maestro": db["_config"]["password_maestro"]},
                            "allievi": dati_importati
                        }
                    salva_dati_cloud(dati_importati)
                    st.success("Archivio ripristinato!")
                    st.rerun()

    if st.button("🚪 Esci (Logout)", use_container_width=True):
        st.session_state["ruolo"] = None
        st.session_state["utente_loggato"] = None
        st.rerun()

# --- 5. AREA PRINCIPALE ---
if not allievo_selezionato:
    st.title("Registro Lezioni di Pianoforte")
    st.info("👈 Crea o seleziona un allievo dalla barra a sinistra.")
else:
    dati_allievo = allievi[allievo_selezionato]
    
    col_titolo, col_storico = st.columns([2, 1])
    with col_titolo:
        st.title(f"Piano di Studio: {allievo_selezionato}")
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

    if is_maestro:
        with st.expander("🔐 Gestione Password di questo Allievo"):
            pwd_corrente_allievo = st.text_input(
                "Password attuale dell'allievo (puoi vederla o reimpostarla qui se la dimentica):",
                value=dati_allievo.get("password", ""),
                disabled=in_storico
            )
    else:
        pwd_corrente_allievo = dati_allievo.get("password", "")

    c1, c2, c3, c4 = st.columns(4)
    livello = c1.text_input("Livello / Corso:", value=dati_mostrati.get("livello", ""), placeholder="Es. Triennio, Propedeutico...", disabled=disabilitato)
    orario = c2.text_input("Giorno e Ora Fissa:", value=dati_mostrati.get("orario", ""), placeholder="Es. Giovedì 16:30", disabled=disabilitato)
    telefono = c3.text_input("Telefono / Contatto:", value=dati_mostrati.get("telefono", ""), placeholder="Es. 333 1234567", disabled=disabilitato)
    data_lez = c4.text_input("Data Lezione:", value=dati_mostrati.get("data", ""), placeholder="Es. 22/11/2026", disabled=disabilitato)

    st.markdown("---")
    t1, t2, t3 = st.columns(3)
    bpm = t1.text_input("Metronomo (BPM):", value=dati_mostrati.get("bpm", ""), placeholder="Es. 72 -> 84 BPM", disabled=disabilitato)
    pedale = t2.text_input("Uso Pedale:", value=dati_mostrati.get("pedale", ""), placeholder="Es. Legato / Mezzo pedale", disabled=disabilitato)
    tocco = t3.text_input("Focus Tocco (Tasti Pesati):", value=dati_mostrati.get("tocco", ""), placeholder="Es. Peso braccio / Polso morbido", disabled=disabilitato)

    tecnica = st.text_area("Tecnica, Scale ed Esercizi:", value=dati_mostrati.get("tecnica", ""), height=100, disabled=disabilitato)
    brani = st.text_area("Brani in Studio e Obiettivi della Lezione:", value=dati_mostrati.get("brani", ""), height=130, disabled=disabilitato)
    compiti = st.text_area("Compiti per Casa (ogni riga diventa una casella da spuntare sul PDF):", value=dati_mostrati.get("compiti", ""), height=130, disabled=disabilitato)

    st.markdown("---")
    
    b1, b2, b3, b4 = st.columns([1.2, 1.4, 1.4, 1])
    
    pdf_pronto = crea_pdf_bytes(allievo_selezionato, {
        "livello": livello, "orario": orario, "data": data_lez,
        "bpm": bpm, "pedale": pedale, "tocco": tocco,
        "tecnica": tecnica, "brani": brani, "compiti": compiti
    })
    nome_file_pdf = f"Lezione_{allievo_selezionato.replace(' ', '_')}.pdf"
    b3.download_button("📄 Scarica PDF Lezione", data=pdf_pronto, file_name=nome_file_pdf, mime="application/pdf", use_container_width=True)

    if is_maestro and not in_storico:
        if b1.button("💾 Salva Scheda", type="primary", use_container_width=True):
            db["allievi"][allievo_selezionato] = {
                "password": pwd_corrente_allievo.strip(),
                "livello": livello, "orario": orario, "telefono": telefono,
                "data": data_lez, "bpm": bpm, "pedale": pedale, "tocco": tocco,
                "tecnica": tecnica, "brani": brani, "compiti": compiti,
                "storico": dati_allievo.get("storico", [])
            }
            salva_dati_cloud(db)
            st.success(f"Scheda di {allievo_selezionato} salvata!")

        if b2.button("📚 Archivia nello Storico", use_container_width=True):
            etichetta_data = data_lez.strip() if data_lez.strip() else datetime.now().strftime("%d/%m/%Y %H:%M")
            copia_lezione = {
                "livello": livello, "orario": orario, "telefono": telefono,
                "data": data_lez, "bpm": bpm, "pedale": pedale, "tocco": tocco,
                "tecnica": tecnica, "brani": brani, "compiti": compiti,
                "data_salvataggio": etichetta_data
            }
            storico_att = dati_allievo.get("storico", [])
            storico_att.append(copia_lezione)
            db["allievi"][allievo_selezionato] = {
                **copia_lezione,
                "password": pwd_corrente_allievo.strip(),
                "storico": storico_att
            }
            salva_dati_cloud(db)
            st.success(f"Lezione del {etichetta_data} archiviata nello storico!")
            st.rerun()

        if b4.button("🗑️ Elimina Allievo", use_container_width=True):
            del db["allievi"][allievo_selezionato]
            salva_dati_cloud(db)
            st.session_state["allievo_attivo"] = None
            st.rerun()
 
