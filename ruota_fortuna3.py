import sys
import json
import random
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGridLayout, QMessageBox,
                             QInputDialog, QFrame, QProgressBar, QGraphicsOpacityEffect,
                             QTextEdit, QDialog)
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QKeyEvent, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

# --- FUNZIONE PER PERCORSI RISORSE INTERNE ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- FUNZIONE PER PERCORSO DATABASE (DOCUMENTI UTENTE) ---
def get_db_path():
    home_docs = os.path.expanduser("~/Documents")
    db_path = os.path.join(home_docs, 'frasi_ruota_fortuna.json')

    if not os.path.exists(db_path):
        try:
            base_json = resource_path('frasi.json')
            if os.path.exists(base_json):
                shutil.copy(base_json, db_path)
            else:
                default_data = {"GENERAL": ["LA RUOTA DELLA FORTUNA"]}
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=4, ensure_ascii=False)
        except:
            pass
    return db_path

# --- DIALOGO PER EDITING MANUALE JSON ---
class JsonEditorDialog(QDialog):
    def __init__(self, current_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor Manuale Database")
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Modifica il file JSON (attenzione alla sintassi):"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(json.dumps(current_data, indent=4, ensure_ascii=False))
        self.text_edit.setFont(QFont("Courier", 12))
        layout.addWidget(self.text_edit)
        btns = QHBoxLayout()
        self.btn_save = QPushButton("Salva e Applica")
        self.btn_cancel = QPushButton("Annulla")
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_save); btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        try:
            return json.loads(self.text_edit.toPlainText())
        except Exception as e:
            return str(e)

# --- SCHERMATA INTRO ---
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gira la ruota")
        self.setStyleSheet("background-color: black;")
        self.media_player = QMediaPlayer()
        self.init_ui()
        self.showFullScreen()
        self.play_intro_music()
        self.avvia_dissolvenza()

    def init_ui(self):
        self.layout_principale = QVBoxLayout(self)
        self.layout_principale.setContentsMargins(0, 0, 0, 0)
        self.logo_label = QLabel(self)
        logo_path = resource_path(os.path.join("images", "logo.png"))
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            screen_size = QApplication.primaryScreen().size()
            self.logo_label.setPixmap(pixmap.scaled(screen_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("GIRA LA RUOTA\nCreato da PakyITA")
            self.logo_label.setStyleSheet("color: white; font-size: 50px; font-weight: bold;")
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        self.logo_label.setGraphicsEffect(self.opacity_effect)
        self.layout_principale.addWidget(self.logo_label)

        # Ripristino Label Salta Intro posizionata correttamente
        self.hint_label = QLabel("Premi INVIO ↵ per saltare l'intro", self)
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet("""
            background-color: rgba(0,0,0,200);
            color: #FFD700;
            font-size: 22px;
            font-weight: bold;
            border: 2px solid #FFD700;
            border-radius: 20px;
            padding: 15px 35px;
        """)
        self.hint_label.adjustSize()

    def posiziona_hint(self):
        # Calcola la posizione centrale in basso
        x = (self.width() - self.hint_label.width()) // 2
        y = self.height() - 180
        self.hint_label.move(x, y)
        self.hint_label.raise_()

    def resizeEvent(self, event):
        self.posiziona_hint()
        super().resizeEvent(event)

    def avvia_dissolvenza(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(2500); self.anim.setStartValue(0); self.anim.setEndValue(1); self.anim.start()

    def play_intro_music(self):
        p = resource_path(os.path.join("sound", "sigla.wav"))
        if os.path.exists(p):
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(p)))
            self.media_player.play()
            self.media_player.mediaStatusChanged.connect(lambda s: self.concludi_intro() if s == QMediaPlayer.EndOfMedia else None)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter): self.concludi_intro()
        elif event.key() == Qt.Key_Escape: self.close()

    def concludi_intro(self):
        self.media_player.stop()
        self.game = RuotaDellaFortuna()
        self.game.avvia_configurazione()
        self.close()

# --- GIOCO PRINCIPALE ---
class RuotaDellaFortuna(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = get_db_path()
        self.carica_database()
        self.turno_attuale = 0
        self.round_corrente = 1
        self.portafogli_round = [0, 0, 0]
        self.montepremi_totale = [0, 0, 0]
        self.lettere_indovinate = set()
        self.valore_ruota = 0
        self.premi = [100, 300, 500, 1000, "BANCAROTTA", "PASSA", 200, 400, 800, 150, 250, 600, "JOLLY"]
        self.timer_gioco = QTimer()
        self.timer_gioco.timeout.connect(self.aggiorna_timer)
        self.init_audio(); self.init_ui()

    def carica_database(self):
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.database = json.load(f)
        except: self.database = {"GENERAL": ["LA RUOTA DELLA FORTUNA"]}

    def salva_database(self):
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.database, f, indent=4, ensure_ascii=False)
        except Exception as e: QMessageBox.critical(self, "Errore", f"Salvataggio fallito: {e}")

    def menu_impostazioni(self):
        opz = ["Aggiungi Nuova Frase", "Rimuovi Frase/Categoria", "Modifica Database (Manuale)", "Annulla"]
        s, ok = QInputDialog.getItem(self, "Menu 🛠", "Cosa vuoi fare?", opz, 0, False)
        if ok:
            if "Aggiungi" in s: self.aggiungi_frase()
            elif "Rimuovi" in s: self.rimuovi_frase()
            elif "Manuale" in s: self.edit_manuale()

    def edit_manuale(self):
        d = JsonEditorDialog(self.database, self)
        if d.exec_():
            new = d.get_data()
            if isinstance(new, dict): self.database = new; self.salva_database()
            else: QMessageBox.critical(self, "Errore", "Sintassi JSON non valida!")

    def aggiungi_frase(self):
        c, ok1 = QInputDialog.getText(self, "Aggiungi", "Categoria:")
        if ok1 and c.strip():
            f, ok2 = QInputDialog.getText(self, "Aggiungi", "Frase:")
            if ok2 and f.strip():
                cat = c.strip().upper()
                if cat not in self.database: self.database[cat] = []
                self.database[cat].append(f.strip().upper()); self.salva_database()

    def rimuovi_frase(self):
        cats = list(self.database.keys())
        if not cats: return
        c, ok1 = QInputDialog.getItem(self, "Rimuovi", "Categoria:", cats, 0, False)
        if ok1:
            frasi = ["--- ELIMINA TUTTO ---"] + self.database[c]
            f, ok2 = QInputDialog.getItem(self, "Rimuovi", "Cosa eliminare?", frasi, 0, False)
            if ok2:
                if f == "--- ELIMINA TUTTO ---": del self.database[c]
                else:
                    self.database[c].remove(f)
                    if not self.database[c]: del self.database[c]
                self.salva_database()

    def init_audio(self):
        self.suoni = {}
        for k, v in {"spin": "spin.wav", "bad": "bad.wav", "correct": "correct.wav", "vittoria": "vittoria.wav"}.items():
            p = QMediaPlayer(); p.setMedia(QMediaContent(QUrl.fromLocalFile(resource_path(os.path.join("sound", v)))))
            self.suoni[k] = p

    def play_sound(self, n):
        if n in self.suoni: self.suoni[n].stop(); self.suoni[n].play()

    def init_ui(self):
        self.setWindowTitle("Gira la ruota"); self.setStyleSheet("background-color: #002244;")
        self.main_layout = QVBoxLayout(self)
        self.top_bar = QHBoxLayout()

        self.btn_set = QPushButton("🛠")
        self.btn_set.setFixedSize(50, 50)
        self.btn_set.setStyleSheet("background-color: #333; color: #FFD700; border: 2px solid #FFD700; border-radius: 25px; font-size: 24px;")
        self.btn_set.clicked.connect(self.menu_impostazioni)

        self.btn_cheat = QPushButton("👁️")
        self.btn_cheat.setFixedSize(50, 50)
        self.btn_cheat.setStyleSheet("background: transparent; color: #FFD700; border: none; font-size: 24px;")
        self.btn_cheat.clicked.connect(lambda: QMessageBox.information(self, "Solution", f"Soluzione: {self.soluzione}"))

        self.btn_exit = QPushButton("❌")
        self.btn_exit.setFixedSize(50, 50)
        self.btn_exit.setStyleSheet("background-color: #900; color: white; border: 2px solid white; border-radius: 25px; font-size: 20px;")
        self.btn_exit.clicked.connect(self.close)

        self.top_bar.addWidget(self.btn_set); self.top_bar.addStretch(); self.top_bar.addWidget(self.btn_cheat); self.top_bar.addSpacing(10); self.top_bar.addWidget(self.btn_exit)
        self.main_layout.addLayout(self.top_bar)

        self.label_info = QLabel(""); self.label_info.setStyleSheet("color: #00FFFF; font-size: 18px; font-weight: bold;"); self.label_info.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.label_info)
        self.label_cat = QLabel(""); self.label_cat.setAlignment(Qt.AlignCenter); self.label_cat.setStyleSheet("font-size: 24px; color: #FFD700; font-weight: bold; background: rgba(0,0,0,100); border-radius: 10px; padding: 5px;")
        self.main_layout.addWidget(self.label_cat)

        self.grid_container = QFrame(); self.grid_layout = QGridLayout(self.grid_container); self.celle = []
        for r in range(4):
            riga = []
            for c in range(14):
                lbl = QLabel(""); lbl.setFixedSize(55, 75); lbl.setAlignment(Qt.AlignCenter); lbl.setFont(QFont("Sans Serif", 24, QFont.Bold)); lbl.setStyleSheet("background-color: #003366; border: 2px solid #001122; border-radius: 4px;")
                self.grid_layout.addWidget(lbl, r, c); riga.append(lbl)
            self.celle.append(riga)
        self.main_layout.addWidget(self.grid_container, alignment=Qt.AlignCenter)

        self.progress = QProgressBar(); self.progress.setFixedHeight(10); self.progress.setTextVisible(False); self.progress.setStyleSheet("QProgressBar::chunk { background-color: #00FF00; }")
        self.main_layout.addWidget(self.progress)
        self.label_ruota = QLabel("GIRA LA RUOTA!"); self.label_ruota.setAlignment(Qt.AlignCenter); self.label_ruota.setStyleSheet("color: white; font-size: 32px; font-weight: bold; padding: 10px; background: #000; border: 2px solid gold;")
        self.main_layout.addWidget(self.label_ruota)

        self.lay_gio = QHBoxLayout(); self.lab_gio = []
        for i in range(3):
            l = QLabel(""); l.setAlignment(Qt.AlignCenter); l.setMinimumWidth(250); self.lay_gio.addWidget(l); self.lab_gio.append(l)
        self.main_layout.addLayout(self.lay_gio)

        btns = QHBoxLayout()
        self.btn_spin = QPushButton("🎡 GIRA (SPAZIO)"); self.btn_vow = QPushButton("💵 VOCALE"); self.btn_sol = QPushButton("💡 RISOLVI")
        for b in [self.btn_spin, self.btn_vow, self.btn_sol]:
            b.setFixedSize(250, 60); b.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold; border-radius: 10px;"); btns.addWidget(b)
        self.btn_spin.clicked.connect(self.anim_ruota); self.btn_vow.clicked.connect(self.buy_vowel); self.btn_sol.clicked.connect(self.solve)
        self.main_layout.addLayout(btns)

    def avvia_configurazione(self):
        self.giocatori = []
        for i in range(3):
            n, ok = QInputDialog.getText(self, "Config", f"Giocatore {i+1}:")
            self.giocatori.append(n.strip().upper() if ok and n.strip() else f"G{i+1}")
        nr, ok = QInputDialog.getInt(self, "Round", "Quanti round?", 3, 1, 10); self.tot_round = nr if ok else 3
        self.showFullScreen(); self.nuovo_round()

    def nuovo_round(self):
        self.timer_gioco.stop()
        if self.round_corrente > self.tot_round: self.classifica(); return
        if not self.database: return
        cat = random.choice(list(self.database.keys())); self.soluzione = random.choice(self.database[cat]).upper(); self.categoria = cat; self.lettere_indovinate = set(); self.portafogli_round = [0, 0, 0]
        self.label_info.setText(f"ROUND {self.round_corrente} / {self.tot_round}"); self.label_cat.setText(self.categoria)
        self.agg_tabellone(); self.agg_giocatori()

    def agg_tabellone(self):
        cur, riga = 1, 1
        for char in self.soluzione:
            if cur >= 13: riga += 1; cur = 1
            if riga > 3: break
            cella = self.celle[riga][cur]
            if char == " ": cella.setStyleSheet("background-color: #003366; border: none;"); cella.setText("")
            elif not char.isalpha() or char in self.lettere_indovinate: cella.setText(char); cella.setStyleSheet("background-color: white; color: black; border: 2px solid #444;")
            else: cella.setStyleSheet("background-color: white; border: 2px solid #444;"); cella.setText("")
            cur += 1

    def anim_ruota(self):
        self.timer_gioco.stop(); self.btn_spin.setEnabled(False); self.play_sound("spin")
        self.timer_f = QTimer(); self.timer_f.timeout.connect(self.flash); self.timer_f.start(100)

    def flash(self):
        if self.suoni["spin"].state() == QMediaPlayer.PlayingState: self.label_ruota.setText(str(random.choice(self.premi)))
        else:
            self.timer_f.stop(); res = random.choice(self.premi); self.label_ruota.setText(str(res))
            if res in ["BANCAROTTA", "PASSA"]:
                if res == "BANCAROTTA": self.portafogli_round[self.turno_attuale] = 0
                self.play_sound("bad"); self.next_turn()
            else: self.valore_ruota = res; self.start_timer(7); self.ask_letter()

    def ask_letter(self, is_v=False):
        let, ok = QInputDialog.getText(self, "Lettera", "Digita:"); self.timer_gioco.stop()
        let = let.upper().strip()
        if ok and let.isalpha() and len(let) == 1:
            cnt = self.soluzione.count(let)
            if cnt > 0 and let not in self.lettere_indovinate:
                self.play_sound("correct"); self.lettere_indovinate.add(let)
                if not is_v: self.portafogli_round[self.turno_attuale] += (cnt * self.valore_ruota)
                self.agg_tabellone(); self.agg_giocatori(); self.btn_spin.setEnabled(True)
            else: self.play_sound("bad"); self.next_turn()
        else: self.next_turn()

    def start_timer(self, s):
        self.max_t = s * 10; self.rem_t = self.max_t; self.progress.setMaximum(self.max_t); self.timer_gioco.start(100)

    def aggiorna_timer(self):
        self.rem_t -= 1; self.progress.setValue(self.rem_t)
        if self.rem_t <= 0: self.timer_gioco.stop(); self.play_sound("bad"); self.next_turn()

    def buy_vowel(self):
        if self.portafogli_round[self.turno_attuale] >= 500: self.portafogli_round[self.turno_attuale] -= 500; self.agg_giocatori(); self.ask_letter(True)

    def solve(self):
        res, ok = QInputDialog.getText(self, "SOLVE", "Frase:"); self.timer_gioco.stop()
        if ok and res.upper().strip() == self.soluzione:
            self.play_sound("vittoria"); self.portafogli_round[self.turno_attuale] += 2000
            self.montepremi_totale[self.turno_attuale] += self.portafogli_round[self.turno_attuale]
            self.round_corrente += 1; self.nuovo_round()
        else: self.play_sound("bad"); self.next_turn()

    def next_turn(self):
        self.turno_attuale = (self.turno_attuale + 1) % 3; self.btn_spin.setEnabled(True); self.agg_giocatori()
        self.label_ruota.setText(f"TURNO: {self.giocatori[self.turno_attuale]}")

    def agg_giocatori(self):
        for i in range(3):
            att = (i == self.turno_attuale)
            self.lab_gio[i].setStyleSheet(f"background: {'#0F0' if att else '#333'}; color: {'#000' if att else '#FFF'}; border: 2px solid gold; border-radius: 10px; padding: 10px;")
            self.lab_gio[i].setText(f"{self.giocatori[i]}\nRound: {self.portafogli_round[i]}€\nTOT: {self.montepremi_totale[i]}€")

    def classifica(self):
        r = sorted(zip(self.giocatori, self.montepremi_totale), key=lambda x: x[1], reverse=True)
        m = "🏆 CLASSIFICA 🏆\n" + "\n".join([f"{n}: {s}€" for n, s in r])
        QMessageBox.information(self, "Fine", m); self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space and self.btn_spin.isEnabled(): self.anim_ruota()
        elif e.key() == Qt.Key_Escape: self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv); splash = SplashScreen(); sys.exit(app.exec_())
