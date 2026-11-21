import customtkinter as ctk
from tkinter import messagebox
import json
import os
import subprocess
from datetime import datetime
from fpdf import FPDF

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

FILE_DATI = "archivio_allievi.json"

class AppPiano(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Registro Lezioni di Pianoforte (v2.0)")
        self.geometry("1080x760")
        self.minsize(920, 650)
        self.allievi = self.carica_dati()
        self.allievo_selezionato = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.crea_barra_laterale()
        self.crea_area_scheda()
        self.aggiorna_lista_allievi()

    def carica_dati(self):
        if os.path.exists(FILE_DATI):
            try:
                with open(FILE_DATI, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def salva_dati_su_file(self):
        with open(FILE_DATI, "w", encoding="utf-8") as f:
            json.dump(self.allievi, f, ensure_ascii=False, indent=4)

    def crea_barra_laterale(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self.sidebar, text="Allievi", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 15))
        self.entry_nuovo = ctk.CTkEntry(self.sidebar, placeholder_text="Nome e Cognome...")
        self.entry_nuovo.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="ew")
        self.entry_nuovo.bind("<Return>", lambda e: self.aggiungi_allievo())
        ctk.CTkButton(self.sidebar, text="+ Aggiungi Allievo", command=self.aggiungi_allievo, fg_color="#2E7D32", hover_color="#1B5E20").grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.scroll_allievi = ctk.CTkScrollableFrame(self.sidebar, label_text="I tuoi allievi")
        self.scroll_allievi.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="nsew")

    def crea_area_scheda(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(8, weight=1)

        top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(18, 5), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)
        self.lbl_nome_allievo = ctk.CTkLabel(top_bar, text="Seleziona o crea un allievo a sinistra", font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_nome_allievo.grid(row=0, column=0, sticky="w")

        box_storico = ctk.CTkFrame(top_bar, fg_color="transparent")
        box_storico.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(box_storico, text="Storico lezioni:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.combo_storico = ctk.CTkComboBox(box_storico, values=["Nessuna lezione archiviata"], command=self.carica_da_storico, width=210)
        self.combo_storico.pack(side="left")

        riga_info = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        riga_info.grid(row=1, column=0, padx=25, pady=4, sticky="ew")
        riga_info.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(riga_info, text="Livello / Corso:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        self.entry_livello = ctk.CTkEntry(riga_info, placeholder_text="Es. Base, 2 Anno...")
        self.entry_livello.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkLabel(riga_info, text="Giorno e Ora Fissa:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, sticky="w")
        self.entry_orario = ctk.CTkEntry(riga_info, placeholder_text="Es. Giovedi 16:30")
        self.entry_orario.grid(row=1, column=1, padx=(0, 8), sticky="ew")

        ctk.CTkLabel(riga_info, text="Telefono / Contatto:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=2, sticky="w")
        self.entry_telefono = ctk.CTkEntry(riga_info, placeholder_text="Es. 333 1234567")
        self.entry_telefono.grid(row=1, column=2, padx=(0, 8), sticky="ew")

        ctk.CTkLabel(riga_info, text="Data Lezione:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=3, sticky="w")
        self.entry_data = ctk.CTkEntry(riga_info, placeholder_text="Es. 20/11/2026")
        self.entry_data.grid(row=1, column=3, sticky="ew")

        riga_tastiera = ctk.CTkFrame(self.main_frame, corner_radius=8)
        riga_tastiera.grid(row=2, column=0, padx=25, pady=(8, 4), sticky="ew")
        riga_tastiera.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(riga_tastiera, text="Metronomo (BPM):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10, pady=(6, 0), sticky="w")
        self.entry_bpm = ctk.CTkEntry(riga_tastiera, placeholder_text="Es. 72 -> 84 BPM")
        self.entry_bpm.grid(row=1, column=0, padx=10, pady=(2, 8), sticky="ew")

        ctk.CTkLabel(riga_tastiera, text="Uso Pedale:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, padx=10, pady=(6, 0), sticky="w")
        self.entry_pedale = ctk.CTkEntry(riga_tastiera, placeholder_text="Es. Legato / Mezzo pedale")
        self.entry_pedale.grid(row=1, column=1, padx=10, pady=(2, 8), sticky="ew")

        ctk.CTkLabel(riga_tastiera, text="Focus Tocco (Tasti Pesati):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=2, padx=10, pady=(6, 0), sticky="w")
        self.entry_tocco = ctk.CTkEntry(riga_tastiera, placeholder_text="Es. Peso braccio / Polso morbido")
        self.entry_tocco.grid(row=1, column=2, padx=10, pady=(2, 8), sticky="ew")

        ctk.CTkLabel(self.main_frame, text="Tecnica, Scale ed Esercizi:", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, padx=25, pady=(6, 2), sticky="w")
        self.txt_tecnica = ctk.CTkTextbox(self.main_frame, height=85, font=ctk.CTkFont(size=14))
        self.txt_tecnica.grid(row=4, column=0, padx=25, sticky="ew")

        ctk.CTkLabel(self.main_frame, text="Brani in Studio e Obiettivi della Lezione:", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, padx=25, pady=(8, 2), sticky="w")
        self.txt_brani = ctk.CTkTextbox(self.main_frame, height=115, font=ctk.CTkFont(size=14))
        self.txt_brani.grid(row=6, column=0, padx=25, sticky="ew")

        ctk.CTkLabel(self.main_frame, text="Compiti per Casa (ogni riga diventa una casella da spuntare sul PDF):", font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, padx=25, pady=(8, 2), sticky="nw")
        self.txt_compiti = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(size=14))
        self.txt_compiti.grid(row=8, column=0, padx=25, pady=(0, 12), sticky="nsew")

        barra_bottoni = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        barra_bottoni.grid(row=9, column=0, padx=25, pady=(0, 18), sticky="ew")

        ctk.CTkButton(barra_bottoni, text="Salva Scheda", command=self.salva_scheda_corrente, width=130, height=38).pack(side="left", padx=(0, 8))
        ctk.CTkButton(barra_bottoni, text="Archivia nello Storico", command=self.archivia_lezione, fg_color="#5E35B1", hover_color="#4527A0", width=165, height=38).pack(side="left", padx=(0, 8))
        ctk.CTkButton(barra_bottoni, text="Anteprima PDF", command=lambda: self.genera_pdf(stampa_diretta=False), fg_color="#D84315", hover_color="#BF360C", width=140, height=38).pack(side="left", padx=(0, 8))
        ctk.CTkButton(barra_bottoni, text="Stampa Subito", command=lambda: self.genera_pdf(stampa_diretta=True), fg_color="#2E7D32", hover_color="#1B5E20", width=140, height=38).pack(side="left")
        ctk.CTkButton(barra_bottoni, text="Elimina", command=self.elimina_allievo, fg_color="transparent", border_width=1, text_color=("gray20", "gray80"), width=90, height=38).pack(side="right")

    def aggiorna_lista_allievi(self):
        for widget in self.scroll_allievi.winfo_children():
            widget.destroy()
        for nome in sorted(self.allievi.keys()):
            colore = "#1976D2" if nome == self.allievo_selezionato else "transparent"
            testo_colore = "white" if nome == self.allievo_selezionato else ("black", "white")
            ctk.CTkButton(self.scroll_allievi, text=nome, anchor="w", fg_color=colore, text_color=testo_colore, command=lambda n=nome: self.seleziona_allievo(n)).pack(fill="x", pady=2)

    def aggiungi_allievo(self):
        nome = self.entry_nuovo.get().strip()
        if not nome:
            return
        if nome in self.allievi:
            messagebox.showwarning("Attenzione", "Questo allievo e gia presente nella lista.")
            return
        self.allievi[nome] = {"livello": "", "orario": "", "telefono": "", "data": datetime.now().strftime("%d/%m/%Y"), "bpm": "", "pedale": "", "tocco": "", "tecnica": "", "brani": "", "compiti": "", "storico": []}
        self.salva_dati_su_file()
        self.entry_nuovo.delete(0, "end")
        self.seleziona_allievo(nome)

    def compila_campi_da_dizionario(self, dati):
        for widget, chiave in [(self.entry_livello, "livello"), (self.entry_orario, "orario"), (self.entry_telefono, "telefono"), (self.entry_data, "data"), (self.entry_bpm, "bpm"), (self.entry_pedale, "pedale"), (self.entry_tocco, "tocco")]:
            widget.delete(0, "end")
            widget.insert(0, dati.get(chiave, ""))
        for widget, chiave in [(self.txt_tecnica, "tecnica"), (self.txt_brani, "brani"), (self.txt_compiti, "compiti")]:
            widget.delete("1.0", "end")
            widget.insert("1.0", dati.get(chiave, ""))

    def aggiorna_menu_storico(self):
        storico = self.allievi[self.allievo_selezionato].get("storico", [])
        if not storico:
            self.combo_storico.configure(values=["Nessuna lezione archiviata"])
            self.combo_storico.set("Nessuna lezione archiviata")
        else:
            voci = [f"{i+1}. {item.get('data_salvataggio', 'Senza data')}" for i, item in enumerate(storico)]
            self.combo_storico.configure(values=voci)
            self.combo_storico.set(voci[-1])

    def seleziona_allievo(self, nome):
        self.allievo_selezionato = nome
        dati = self.allievi[nome]
        self.lbl_nome_allievo.configure(text=f"Scheda di: {nome}")
        self.compila_campi_da_dizionario(dati)
        self.aggiorna_menu_storico()
        self.aggiorna_lista_allievi()

    def leggi_campi_correnti(self):
        storico_esistente = self.allievi[self.allievo_selezionato].get("storico", [])
        return {
            "livello": self.entry_livello.get().strip(),
            "orario": self.entry_orario.get().strip(),
            "telefono": self.entry_telefono.get().strip(),
            "data": self.entry_data.get().strip(),
            "bpm": self.entry_bpm.get().strip(),
            "pedale": self.entry_pedale.get().strip(),
            "tocco": self.entry_tocco.get().strip(),
            "tecnica": self.txt_tecnica.get("1.0", "end-1c").strip(),
            "brani": self.txt_brani.get("1.0", "end-1c").strip(),
            "compiti": self.txt_compiti.get("1.0", "end-1c").strip(),
            "storico": storico_esistente
        }

    def salva_scheda_corrente(self, silenzioso=False):
        if not self.allievo_selezionato:
            if not silenzioso:
                messagebox.showinfo("Info", "Seleziona prima un allievo dalla lista a sinistra.")
            return
        self.allievi[self.allievo_selezionato] = self.leggi_campi_correnti()
        self.salva_dati_su_file()
        if not silenzioso:
            messagebox.showinfo("Salvato", f"Scheda di {self.allievo_selezionato} salvata!")

    def archivia_lezione(self):
        if not self.allievo_selezionato:
            messagebox.showinfo("Info", "Seleziona prima un allievo.")
            return
        dati = self.leggi_campi_correnti()
        etichetta_data = dati["data"] if dati["data"] else datetime.now().strftime("%d/%m/%Y %H:%M")
        copia_lezione = {k: v for k, v in dati.items() if k != "storico"}
        copia_lezione["data_salvataggio"] = etichetta_data
        dati["storico"].append(copia_lezione)
        self.allievi[self.allievo_selezionato] = dati
        self.salva_dati_su_file()
        self.aggiorna_menu_storico()
        messagebox.showinfo("Archiviato", f"Lezione del '{etichetta_data}' salvata nello storico di {self.allievo_selezionato}!")

    def carica_da_storico(self, scelta):
        if not self.allievo_selezionato or scelta == "Nessuna lezione archiviata":
            return
        try:
            indice = int(scelta.split(".")[0]) - 1
            lezione_passata = self.allievi[self.allievo_selezionato]["storico"][indice]
            self.compila_campi_da_dizionario(lezione_passata)
        except Exception:
            pass

    def elimina_allievo(self):
        if not self.allievo_selezionato:
            return
        if messagebox.askyesno("Conferma", f"Vuoi eliminare definitivamente {self.allievo_selezionato}?"):
            del self.allievi[self.allievo_selezionato]
            self.salva_dati_su_file()
            self.allievo_selezionato = None
            self.lbl_nome_allievo.configure(text="Seleziona o crea un allievo a sinistra")
            self.compila_campi_da_dizionario({})
            self.combo_storico.configure(values=["Nessuna lezione archiviata"])
            self.combo_storico.set("Nessuna lezione archiviata")
            self.aggiorna_lista_allievi()

    def pulisci_testo_pdf(self, testo):
        for k, v in {"’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."}.items():
            testo = testo.replace(k, v)
        return testo.encode("latin-1", "replace").decode("latin-1")

    def genera_pdf(self, stampa_diretta=False):
        if not self.allievo_selezionato:
            messagebox.showinfo("Info", "Seleziona prima un allievo.")
            return
        self.salva_scheda_corrente(silenzioso=True)
        dati = self.allievi[self.allievo_selezionato]

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 11, self.pulisci_testo_pdf(f"PIANOFORTE - {self.allievo_selezionato}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        info_riga = f"Livello: {dati['livello'] or '---'}  |  Orario: {dati['orario'] or '---'}  |  Data: {dati['data'] or '---'}"
        pdf.cell(0, 7, self.pulisci_testo_pdf(info_riga), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_fill_color(245, 247, 250)
        pdf.set_draw_color(180, 190, 200)
        pdf.set_font("Helvetica", "B", 10)
        riga_tecnica_pdf = f"  METRONOMO: {dati['bpm'] or '---'}    |    PEDALE: {dati['pedale'] or '---'}    |    TOCCO: {dati['tocco'] or '---'}"
        pdf.cell(0, 10, self.pulisci_testo_pdf(riga_tecnica_pdf), border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(6)

        for titolo, chiave in [("TECNICA, SCALE ED ESERCIZI", "tecnica"), ("BRANI IN STUDIO E OBIETTIVI", "brani")]:
            pdf.set_fill_color(230, 238, 248)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 9, self.pulisci_testo_pdf(f"  {titolo}"), new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 12)
            pdf.multi_cell(0, 7, self.pulisci_testo_pdf(dati[chiave] or "Nessuna nota inserita."))
            pdf.ln(5)

        pdf.set_fill_color(230, 238, 248)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, self.pulisci_testo_pdf("  COMPITI PER CASA (Spuntare al controllo)"), new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 12)
        if dati["compiti"]:
            for riga in dati["compiti"].splitlines():
                riga_pulita = riga.strip()
                if riga_pulita:
                    x_box = pdf.get_x() + 2
                    y_box = pdf.get_y() + 1.5
                    pdf.rect(x_box, y_box, 4, 4)
                    pdf.set_x(x_box + 7)
                    pdf.multi_cell(0, 7, self.pulisci_testo_pdf(riga_pulita))
                    pdf.ln(1)
        else:
            pdf.multi_cell(0, 7, "Nessun compito assegnato.")

        os.makedirs("PDF_Leggio", exist_ok=True)
        nome_pulito = "".join(c for c in self.allievo_selezionato if c.isalnum() or c in (" ", "_")).rstrip().replace(" ", "_")
        nome_pdf = os.path.join("PDF_Leggio", f"Lezione_{nome_pulito}.pdf")
        pdf.output(nome_pdf)

        if stampa_diretta:
            try:
                os.startfile(nome_pdf, "print")
                messagebox.showinfo("Stampa avviata", f"Foglio di {self.allievo_selezionato} inviato alla stampante!")
            except Exception:
                os.startfile(nome_pdf)
        else:
            try:
                os.startfile(nome_pdf)
            except Exception:
                subprocess.Popen(["start", nome_pdf], shell=True)

if __name__ == "__main__":
    app = AppPiano()
    app.mainloop()
