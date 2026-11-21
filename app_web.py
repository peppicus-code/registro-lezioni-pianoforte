import streamlit as st
import json
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Registro Lezioni di Pianoforte", page_icon="🎹", layout="wide")

if "allievi" not in st.session_state:
    st.session_state.allievi = {}
if "allievo_selezionato" not in st.session_state:
    st.session_state.allievo_selezionato = None

def pulisci_testo_pdf(testo):
    for k, v in {"’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."}.items():
        testo = testo.replace(k, v)
    return testo.encode("latin-1", "replace").decode("latin-1")

def genera_pdf_bytes(nome_allievo, dati):
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

with st.sidebar:
    st.title("🎹 Allievi")
    
    nuovo_nome = st.text_input("Nuovo allievo", placeholder="Nome e Cognome...", label_visibility="collapsed")
    if st.button("+ Aggiungi Allievo", use_container_width=True, type="primary"):
        nome = nuovo_nome.strip()
        if not nome:
            st.warning("Inserisci un nome.")
        elif nome in st.session_state.allievi:
            st.warning("Questo allievo è già presente.")
        else:
            st.session_state.allievi[nome] = {
                "livello": "", "orario": "", "telefono": "",
                "data": datetime.now().strftime("%d/%m/%Y"),
                "bpm": "", "pedale": "", "tocco": "",
                "tecnica": "", "brani": "", "compiti": "",
                "storico": []
            }
            st.session_state.allievo_selezionato = nome
            st.rerun()

    st.divider()
    st.subheader("I tuoi allievi")
    
    if not st.session_state.allievi:
        st.caption("Nessun allievo in lista.")
    else:
        for nome in sorted(st.session_state.allievi.keys()):
            tipo_btn = "primary" if nome == st.session_state.allievo_selezionato else "secondary"
            if st.button(nome, key=f"btn_{nome}", use_container_width=True, type=tipo_btn):
                st.session_state.allievo_selezionato = nome
                st.rerun()

    st.divider()
    st.subheader("💾 Salvataggio Dati")
    json_str = json.dumps(st.session_state.allievi, ensure_ascii=False, indent=4)
    st.download_button(
        label="⬇️ Scarica Archivio (.json)",
        data=json_str,
        file_name="archivio_allievi.json",
        mime="application/json",
        use_container_width=True
    )
    file_caricato = st.file_uploader("⬆️ Carica Archivio (.json)", type=["json"])
    if file_caricato is not None:
        if st.button("Ripristina dati caricati", use_container_width=True):
            try:
                st.session_state.allievi = json.load(file_caricato)
                st.session_state.allievo_selezionato = next(iter(sorted(st.session_state.allievi.keys())), None)
                st.success("Archivio ripristinato!")
                st.rerun()
            except Exception:
                st.error("File non valido.")

st.title("Registro Lezioni di Pianoforte")

allievo = st.session_state.allievo_selezionato

if not allievo or allievo not in st.session_state.allievi:
    st.info("👈 Seleziona o crea un allievo dalla barra a sinistra (su tablet/cellulare premi la freccia `>` in alto a sinistra per aprire il menu).")
else:
    dati = st.session_state.allievi[allievo]
    
    col_titolo, col_storico = st.columns(2)
    with col_titolo:
        st.subheader(f"Scheda di: {allievo}")
    with col_storico:
        storico = dati.get("storico", [])
        if storico:
            opzioni = ["Scheda attuale"] + [f"{i+1}. {item.get('data_salvataggio', 'Senza data')}" for i, item in enumerate(storico)]
            scelta_storico = st.selectbox("Storico lezioni:", opzioni)
            if scelta_storico != "Scheda attuale":
                parti = scelta_storico.split(".")
                idx = int(parti.pop(0)) - 1
                dati = storico[idx]
        else:
            st.selectbox("Storico lezioni:", ["Nessuna lezione archiviata"], disabled=True)

    c1, c2, c3, c4 = st.columns(4)
    livello = c1.text_input("Livello / Corso:", value=dati.get("livello", ""), placeholder="Es. Base, 2 Anno...")
    orario = c2.text_input("Giorno e Ora Fissa:", value=dati.get("orario", ""), placeholder="Es. Giovedi 16:30")
    telefono = c3.text_input("Telefono / Contatto:", value=dati.get("telefono", ""), placeholder="Es. 333 1234567")
    data_lez = c4.text_input("Data Lezione:", value=dati.get("data", ""), placeholder="Es. 20/11/2026")

    st.markdown("---")
    k1, k2, k3 = st.columns(3)
    bpm = k1.text_input("Metronomo (BPM):", value=dati.get("bpm", ""), placeholder="Es. 72 -> 84 BPM")
    pedale = k2.text_input("Uso Pedale:", value=dati.get("pedale", ""), placeholder="Es. Legato / Mezzo pedale")
    tocco = k3.text_input("Focus Tocco (Tasti Pesati):", value=dati.get("tocco", ""), placeholder="Es. Peso braccio / Polso morbido")

    tecnica = st.text_area("Tecnica, Scale ed Esercizi:", value=dati.get("tecnica", ""), height=100)
    brani = st.text_area("Brani in Studio e Obiettivi della Lezione:", value=dati.get("brani", ""), height=130)
    compiti = st.text_area("Compiti per Casa (ogni riga diventa una casella da spuntare sul PDF):", value=dati.get("compiti", ""), height=130)

    scheda_aggiornata = {
        "livello": livello.strip(),
        "orario": orario.strip(),
        "telefono": telefono.strip(),
        "data": data_lez.strip(),
        "bpm": bpm.strip(),
        "pedale": pedale.strip(),
        "tocco": tocco.strip(),
        "tecnica": tecnica.strip(),
        "brani": brani.strip(),
        "compiti": compiti.strip(),
        "storico": st.session_state.allievi[allievo].get("storico", [])
    }

    b1, b2, b3, b4 = st.columns([1.2, 1.5, 1.5, 1])
    
    if b1.button("💾 Salva Scheda", use_container_width=True, type="primary"):
        st.session_state.allievi[allievo] = scheda_aggiornata
        st.success(f"Scheda di {allievo} aggiornata!")

    if b2.button("📚 Archivia nello Storico", use_container_width=True):
        etichetta_data = scheda_aggiornata["data"] if scheda_aggiornata["data"] else datetime.now().strftime("%d/%m/%Y %H:%M")
        copia_lezione = {k: v for k, v in scheda_aggiornata.items() if k != "storico"}
        copia_lezione["data_salvataggio"] = etichetta_data
        scheda_aggiornata["storico"].append(copia_lezione)
        st.session_state.allievi[allievo] = scheda_aggiornata
        st.success(f"Lezione del '{etichetta_data}' archiviata!")
        st.rerun()

    pdf_bytes = genera_pdf_bytes(allievo, scheda_aggiornata)
    nome_pulito = "".join(c for c in allievo if c.isalnum() or c in (" ", "_")).rstrip().replace(" ", "_")
    b3.download_button(
        label="📄 Scarica / Stampa PDF",
        data=pdf_bytes,
        file_name=f"Lezione_{nome_pulito}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    if b4.button("🗑️ Elimina", use_container_width=True):
        del st.session_state.allievi[allievo]
        st.session_state.allievo_selezionato = None
        st.rerun()
