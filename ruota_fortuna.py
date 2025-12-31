import sys
import json
import random
import os
import shutil
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGridLayout, QMessageBox,
                             QInputDialog, QFrame, QProgressBar, QGraphicsOpacityEffect,
                             QTextEdit, QDialog, QMainWindow)
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QRectF
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist, QSound

# --- CONFIGURAZIONE VERSIONING ---
VERSION_ATTUALE = "1.1.4"
GITHUB_REPO = "PakyITA/Ruota-Della-Fortuna"

# --- CLASSE SUPPORTO CORIANDOLI ---
class Coriandolo:
    def __init__(self, screen_width):
        self.x = random.randint(0, screen_width)
        self.y = random.randint(-800, -50)
        self.color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.size = random.randint(6, 14)
        self.speed = random.randint(5, 11)
        self.swing = random.uniform(-3, 3)

    def caduta(self):
        self.y += self.speed
        self.x += self.swing

# --- FUNZIONI DI SERVIZIO ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "1.0.0").replace("v", "")
            if latest_version > VERSION_ATTUALE:
                return latest_version
    except: pass
    return None

def get_db_path():
    home_docs = os.path.expanduser("~/Documents")
    db_path = os.path.join(home_docs, 'frasi_gira_la_ruota.json')
    if not os.path.exists(db_path):
        try:
            base_json = resource_path('frasi.json')
            if os.path.exists(base_json):
                shutil.copy(base_json, db_path)
            else:
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump({"GENERAL": ["GIRA LA RUOTA"]}, f, indent=4, ensure_ascii=False)
        except: pass
    return db_path

# --- EDITOR DATABASE ---
class JsonEditorDialog(QDialog):
    def __init__(self, current_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor Manuale Database")
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(json.dumps(current_data, indent=4, ensure_ascii=False))
        self.text_edit.setFont(QFont("Courier", 12))
        layout.addWidget(self.text_edit)
        btns = QHBoxLayout()
        self.btn_save = QPushButton("Salva"); self.btn_cancel = QPushButton("Annulla")
        self.btn_save.clicked.connect(self.accept); self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_save); btns.addWidget(self.btn_cancel); layout.addLayout(btns)
    def get_data(self):
        try: return json.loads(self.text_edit.toPlainText())
        except Exception as e: return str(e)

# --- SCHERMATA INTRO ---
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.media_player = QMediaPlayer()
        self.init_ui()
        self.showFullScreen()
        self.play_intro_music()
        self.avvia_dissolvenza()
        self.nuova_versione = check_for_updates()

    def init_ui(self):
        self.layout_centrale = QVBoxLayout(self)
        self.logo_label = QLabel()
        logo_path = resource_path(os.path.join("images", "logo.png"))
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            self.logo_label.setPixmap(pix.scaled(QApplication.primaryScreen().size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("GIRA LA RUOTA")
            self.logo_label.setStyleSheet("color: white; font-size: 60px; font-weight: bold;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        self.logo_label.setGraphicsEffect(self.opacity_effect)
        self.layout_centrale.addWidget(self.logo_label)
        self.label_v = QLabel(f"v{VERSION_ATTUALE}", self)
        self.label_v.setStyleSheet("color: gray; font-size: 12px;")
        self.btn_skip = QPushButton("SALTA INTRO ⏭", self)
        self.btn_skip.setFixedSize(200, 60)
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background-color: #FFD700; color: black; font-weight: bold;
                border: 2px solid white; border-radius: 15px; font-size: 16px;
            }
            QPushButton:hover { background-color: white; }
        """)
        self.btn_skip.clicked.connect(self.concludi_intro)

    def resizeEvent(self, event):
        self.btn_skip.move(self.width() - 240, self.height() - 100)
        self.label_v.move(20, self.height() - 30)
        super().resizeEvent(event)

    def avvia_dissolvenza(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(2000); self.anim.setStartValue(0); self.anim.setEndValue(1); self.anim.start()

    def play_intro_music(self):
        p = resource_path(os.path.join("sound", "sigla.wav"))
        if os.path.exists(p):
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(p)))
            self.media_player.play()
            self.media_player.mediaStatusChanged.connect(lambda s: self.concludi_intro() if s == QMediaPlayer.EndOfMedia else None)
        else: QTimer.singleShot(3000, self.concludi_intro)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space): self.concludi_intro()

    def concludi_intro(self):
        self.media_player.stop()
        if self.nuova_versione:
            QMessageBox.information(self, "Aggiornamento Disponibile", f"È disponibile una nuova versione: v{self.nuova_versione}")
        self.game = GiraLaRuota()
        self.game.avvia_configurazione()
        self.close()

# --- CLASSE GIOCO PRINCIPALE ---
class GiraLaRuota(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = get_db_path()
        self.carica_database()
        self.turno_attuale = 0
        self.round_corrente = 1
        self.portafogli_round = [0, 0, 0]
        self.montepremi_totale = [0, 0, 0]
        self.ha_jolly = [False, False, False]
        self.lettere_indovinate = set()
        self.is_muted = False
        self.coriandoli = []

        self.premi_base = [100, 300, 500, 1000, "BANCAROTTA", "PASSA", 200, 400, 800, 150, 250, 600]
        self.premi_correnti = []
        self.jolly_pescati_nel_round = 0

        self.timer_gioco = QTimer(); self.timer_gioco.timeout.connect(self.aggiorna_timer)
        self.timer_coriandoli = QTimer(); self.timer_coriandoli.timeout.connect(self.aggiorna_animazione_coriandoli)

        self.init_audio(); self.init_ui()

    def carica_database(self):
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f: self.database = json.load(f)
        except: self.database = {"GENERAL": ["GIRA LA RUOTA"]}

    def salva_database(self):
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f: json.dump(self.database, f, indent=4, ensure_ascii=False)
        except Exception as e: QMessageBox.critical(self, "Errore", f"Salvataggio fallito: {e}")

    def init_audio(self):
        self.suoni = {}
        suoni_files = {"spin": "spin.wav", "bad": "bad.wav", "correct": "correct.wav", "vittoria": "vittoria.wav", "victory": "victory.wav"}
        for k, v in suoni_files.items():
            path = resource_path(os.path.join("sound", v))
            p = QMediaPlayer()
            p.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            self.suoni[k] = p

        self.bg_player = QMediaPlayer()
        bg_file = resource_path(os.path.join("sound", "background.wav"))
        if os.path.exists(bg_file):
            self.playlist = QMediaPlaylist(); self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(bg_file)))
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop); self.bg_player.setPlaylist(self.playlist); self.bg_player.setVolume(20)

    def play_sound(self, n):
        if n in self.suoni and not self.is_muted:
            self.suoni[n].stop(); self.suoni[n].play()

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        self.bg_player.setMuted(self.is_muted)
        for s in self.suoni.values(): s.setMuted(self.is_muted)
        self.btn_mute.setText("🔇" if self.is_muted else "🔊")

    def init_ui(self):
        self.setWindowTitle(f"Gira la Ruota v{VERSION_ATTUALE}"); self.setStyleSheet("background-color: #002244;")
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.btn_set = QPushButton("🛠"); self.btn_next_phrase = QPushButton("⏭️")
        self.btn_mute = QPushButton("🔊"); self.btn_cheat = QPushButton("👁️"); self.btn_exit = QPushButton("❌")
        for b in [self.btn_set, self.btn_next_phrase, self.btn_mute, self.btn_cheat, self.btn_exit]:
            b.setFixedSize(55, 55)
            b.setStyleSheet("background-color: #333; color: #FFD700; border: 2px solid #FFD700; border-radius: 27px; font-size: 20px;")

        self.btn_exit.setStyleSheet("background-color: #900; color: white; border: 2px solid white; border-radius: 27px; font-size: 20px;")
        self.btn_set.clicked.connect(self.menu_impostazioni); self.btn_next_phrase.clicked.connect(self.skip_phrase)
        self.btn_mute.clicked.connect(self.toggle_mute); self.btn_exit.clicked.connect(self.close)
        self.btn_cheat.clicked.connect(lambda: QMessageBox.information(self, "Soluzione", f"Soluzione: {self.soluzione}"))

        top.addWidget(self.btn_set); top.addWidget(self.btn_next_phrase); top.addWidget(self.btn_mute); top.addStretch(); top.addWidget(self.btn_cheat); top.addSpacing(10); top.addWidget(self.btn_exit); layout.addLayout(top)

        self.label_info = QLabel(""); self.label_info.setStyleSheet("color: #00FFFF; font-size: 18px; font-weight: bold;"); self.label_info.setAlignment(Qt.AlignCenter); layout.addWidget(self.label_info)
        self.label_cat = QLabel(""); self.label_cat.setAlignment(Qt.AlignCenter); self.label_cat.setStyleSheet("font-size: 24px; color: #FFD700; font-weight: bold; background: rgba(0,0,0,120); border-radius: 10px; padding: 5px;"); layout.addWidget(self.label_cat)

        self.grid_container = QFrame(); self.grid_layout = QGridLayout(self.grid_container); self.celle = []
        for r in range(4):
            riga = []
            for c in range(14):
                lbl = QLabel(""); lbl.setFixedSize(55, 75); lbl.setAlignment(Qt.AlignCenter); lbl.setFont(QFont("Arial", 26, QFont.Bold))
                lbl.setStyleSheet("background-color: #003366; border: 2px solid #001122; border-radius: 5px;")
                self.grid_layout.addWidget(lbl, r, c); riga.append(lbl)
            self.celle.append(riga)
        layout.addWidget(self.grid_container, alignment=Qt.AlignCenter)

        self.progress = QProgressBar(); self.progress.setFixedHeight(12); self.progress.setTextVisible(False); self.progress.setStyleSheet("QProgressBar::chunk { background-color: #00FF00; }"); layout.addWidget(self.progress)
        self.label_ruota = QLabel("GIRA LA RUOTA!"); self.label_ruota.setAlignment(Qt.AlignCenter); self.label_ruota.setStyleSheet("color: white; font-size: 32px; font-weight: bold; padding: 10px; background: #000; border: 3px solid gold;"); layout.addWidget(self.label_ruota)

        self.lay_gio = QHBoxLayout(); self.lab_gio = []
        for i in range(3):
            l = QLabel(""); l.setAlignment(Qt.AlignCenter); l.setMinimumWidth(260); self.lay_gio.addWidget(l); self.lab_gio.append(l)
        layout.addLayout(self.lay_gio)

        btns = QHBoxLayout()
        self.btn_spin = QPushButton("🎡 GIRA RUOTA"); self.btn_vow = QPushButton("💵 VOCALE (-500€)"); self.btn_pass = QPushButton("✋ PASSA"); self.btn_sol = QPushButton("💡 RISOLVI")
        for b in [self.btn_spin, self.btn_vow, self.btn_pass, self.btn_sol]:
            b.setFixedSize(200, 65); b.setStyleSheet("background-color: #FFD700; color: black; font-weight: bold; border-radius: 12px; font-size: 14px;"); btns.addWidget(b)
        self.btn_spin.clicked.connect(self.anim_ruota); self.btn_vow.clicked.connect(self.buy_vowel)
        self.btn_pass.clicked.connect(self.manual_pass); self.btn_sol.clicked.connect(self.solve); layout.addLayout(btns)

    def nuovo_round(self):
        if self.round_corrente > self.tot_round: self.classifica(); return
        self.bg_player.play()
        self.jolly_pescati_nel_round = 0
        self.premi_correnti = list(self.premi_base) + ["JOLLY", "JOLLY"]

        # --- LOGICA DI SELEZIONE CASUALE MIGLIORATA ---
        categorie = list(self.database.keys())
        random.shuffle(categorie)  # Mischia le categorie
        cat = categorie[0]

        frasi = self.database[cat]
        random.shuffle(frasi)  # Mischia le frasi della categoria scelta
        self.soluzione = frasi[0].upper()

        self.categoria = cat; self.lettere_indovinate = set(); self.portafogli_round = [0, 0, 0]
        self.label_info.setText(f"ROUND {self.round_corrente} / {self.tot_round}"); self.label_cat.setText(self.categoria); self.agg_tabellone(); self.agg_giocatori()

    def avvia_configurazione(self):
        self.giocatori = []
        for i in range(3):
            n, ok = QInputDialog.getText(self, "Setup Giocatori", f"Nome Giocatore {i+1}:")
            self.giocatori.append(n.strip().upper() if ok and n.strip() else f"GIOCATORE {i+1}")
        nr, ok = QInputDialog.getInt(self, "Configurazione", "Numero di Round:", 3, 1, 10); self.tot_round = nr if ok else 3
        self.showFullScreen(); self.nuovo_round()

    def skip_phrase(self):
        r = QMessageBox.question(self, 'Cambia Frase', "Vuoi rigenerare la frase?", QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes: self.nuovo_round()

    def manual_pass(self):
        r = QMessageBox.question(self, 'Passa Turno', "Cedere il turno?", QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes: self.play_sound("bad"); self.next_turn()

    def agg_tabellone(self):
        for r in range(4):
            for c in range(14):
                self.celle[r][c].setText(""); self.celle[r][c].setStyleSheet("background-color: #003366; border: none;")
        parole = self.soluzione.split(" ")
        riga, col = 1, 1
        for p in parole:
            if col + len(p) > 13: riga += 1; col = 1
            if riga > 3: break
            for char in p:
                cella = self.celle[riga][col]
                if char in self.lettere_indovinate or not char.isalpha():
                    cella.setText(char); cella.setStyleSheet("background-color: white; color: black; border: 2px solid #444;")
                else: cella.setStyleSheet("background-color: white; border: 2px solid #444;")
                col += 1
            col += 1

    def anim_ruota(self):
        self.btn_spin.setEnabled(False); self.play_sound("spin")
        self.timer_f = QTimer(); self.timer_f.timeout.connect(self.flash); self.timer_f.start(100)

    def flash(self):
        if self.suoni["spin"].state() == QMediaPlayer.PlayingState:
            self.label_ruota.setText(str(random.choice(self.premi_correnti)))
        else:
            self.timer_f.stop(); res = random.choice(self.premi_correnti); self.label_ruota.setText(str(res))
            if res in ["BANCAROTTA", "PASSA"]:
                if self.ha_jolly[self.turno_attuale]:
                    self.ha_jolly[self.turno_attuale] = False; self.btn_spin.setEnabled(True)
                else:
                    if res == "BANCAROTTA": self.portafogli_round[self.turno_attuale] = 0
                    self.play_sound("bad"); self.next_turn()
            elif res == "JOLLY":
                self.ha_jolly[self.turno_attuale] = True; self.jolly_pescati_nel_round += 1
                self.premi_correnti.remove("JOLLY"); self.premi_correnti.append(200)
                self.valore_ruota = 500; self.start_timer(7)
            else: self.valore_ruota = res; self.start_timer(7)

    def start_timer(self, s):
        self.rem_t = s * 10; self.progress.setMaximum(self.rem_t); self.timer_gioco.start(100); self.ask_letter()

    def aggiorna_timer(self):
        self.rem_t -= 1; self.progress.setValue(self.rem_t)
        if self.rem_t <= 0: self.timer_gioco.stop(); self.play_sound("bad"); self.next_turn()

    def ask_letter(self, is_v=False):
        let, ok = QInputDialog.getText(self, "Lettera", "Digita una lettera:"); self.timer_gioco.stop()
        let = let.upper().strip() if ok else ""
        if ok and len(let) == 1 and let.isalpha():
            if let in self.soluzione and let not in self.lettere_indovinate:
                cnt = self.soluzione.count(let); self.lettere_indovinate.add(let)
                if not is_v: self.portafogli_round[self.turno_attuale] += (cnt * self.valore_ruota)
                self.play_sound("correct"); self.agg_tabellone(); self.agg_giocatori(); self.btn_spin.setEnabled(True)
            else: self.play_sound("bad"); self.next_turn()
        else: self.next_turn()

    def buy_vowel(self):
        if self.portafogli_round[self.turno_attuale] >= 500:
            self.portafogli_round[self.turno_attuale] -= 500; self.agg_giocatori(); self.ask_letter(True)

    def solve(self):
        res, ok = QInputDialog.getText(self, "Risolvi", "La soluzione è:"); self.timer_gioco.stop()
        if ok and res.upper().strip() == self.soluzione:
            self.play_sound("victory")

            nome_vincitore = self.giocatori[self.turno_attuale]
            msg_vincitore = f"🏆🏆🏆 COMPLIMENTI 🏆🏆🏆\n\n🥇 {nome_vincitore} 🥇\n\nHAI VINTO IL ROUND!"
            QMessageBox.information(self, "RISOLTO!", msg_vincitore)

            self.avvia_coriandoli()
            self.montepremi_totale[self.turno_attuale] += self.portafogli_round[self.turno_attuale]
            QTimer.singleShot(4500, self.prossimo_round_dopo_festa)
        else: self.play_sound("bad"); self.next_turn()

    def avvia_coriandoli(self):
        self.coriandoli = [Coriandolo(self.width()) for _ in range(180)]
        self.timer_coriandoli.start(30)

    def aggiorna_animazione_coriandoli(self):
        for c in self.coriandoli: c.caduta()
        if all(c.y > self.height() for c in self.coriandoli):
            self.timer_coriandoli.stop(); self.coriandoli = []
        self.update()

    def paintEvent(self, event):
        if self.coriandoli:
            painter = QPainter(self)
            for c in self.coriandoli:
                painter.setBrush(c.color)
                painter.setPen(Qt.NoPen)
                painter.drawRect(int(c.x), int(c.y), c.size, c.size)

    def prossimo_round_dopo_festa(self):
        self.round_corrente += 1; self.nuovo_round()

    def next_turn(self):
        self.turno_attuale = (self.turno_attuale + 1) % 3; self.btn_spin.setEnabled(True); self.agg_giocatori()

    def agg_giocatori(self):
        for i in range(3):
            att = (i == self.turno_attuale); jolly = " 🍀" if self.ha_jolly[i] else ""
            self.lab_gio[i].setStyleSheet(f"background: {'#0F0' if att else '#333'}; color: {'#000' if att else '#FFF'}; border: 2px solid gold; border-radius: 12px; padding: 10px;")
            self.lab_gio[i].setText(f"{self.giocatori[i]}{jolly}\nRound: {self.portafogli_round[i]}€\nTOT: {self.montepremi_totale[i]}€")

    def classifica(self):
        self.bg_player.stop()
        r = sorted(zip(self.giocatori, self.montepremi_totale), key=lambda x: x[1], reverse=True)
        m_classifica = "📊 CLASSIFICA GENERALE 📊\n\n" + "\n".join([f"{n}: {s}€" for n, s in r])
        m_classifica += "\n\nVuoi giocare un'altra partita?"

        risp = QMessageBox.question(self, "Fine Gioco", m_classifica, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if risp == QMessageBox.Yes:
            self.round_corrente = 1; self.montepremi_totale = [0, 0, 0]; self.portafogli_round = [0, 0, 0]
            self.ha_jolly = [False, False, False]; self.nuovo_round()
        else: self.close()

    def menu_impostazioni(self):
        d = JsonEditorDialog(self.database, self)
        if d.exec_():
            new = d.get_data()
            if isinstance(new, dict): self.database = new; self.salva_database()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space and self.btn_spin.isEnabled(): self.anim_ruota()
        elif e.key() == Qt.Key_Escape: self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv); splash = SplashScreen(); sys.exit(app.exec_())
