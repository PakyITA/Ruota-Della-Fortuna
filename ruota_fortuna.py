import sys
import json
import random
import os
import shutil
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGridLayout, QMessageBox,
                             QInputDialog, QFrame, QProgressBar, QGraphicsOpacityEffect,
                             QTextEdit, QDialog)
from PyQt5.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QKeyEvent
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist

# --- CONFIGURAZIONE ---
VERSION_ATTUALE = "1.1.6"
GITHUB_REPO = "PakyITA/Ruota-Della-Fortuna"
VOCALI = set("AEIOU")
CONSONANTI = set("BCDFGHJKLMNPQRSTVWXYZ")

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "1.0.0").replace("v", "")
            if latest_version > VERSION_ATTUALE: return latest_version
    except: pass
    return None

def get_db_path():
    home_docs = os.path.expanduser("~/Documents")
    db_path = os.path.join(home_docs, 'frasi_gira_la_ruota.json')
    if not os.path.exists(db_path):
        try:
            base_json = resource_path('frasi.json')
            if os.path.exists(base_json): shutil.copy(base_json, db_path)
            else:
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump({"GENERAL": ["GIRA LA RUOTA"]}, f, indent=4, ensure_ascii=False)
        except: pass
    return db_path

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

class JsonEditorDialog(QDialog):
    def __init__(self, current_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor Database")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(json.dumps(current_data, indent=4, ensure_ascii=False))
        layout.addWidget(self.text_edit)
        btns = QHBoxLayout()
        self.btn_save = QPushButton("Salva"); self.btn_cancel = QPushButton("Annulla")
        self.btn_save.clicked.connect(self.accept); self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_save); btns.addWidget(self.btn_cancel); layout.addLayout(btns)
    def get_data(self):
        try: return json.loads(self.text_edit.toPlainText())
        except: return None

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.media_player = QMediaPlayer()
        self.init_ui()
        self.showFullScreen()
        self.play_intro_music()
        self.nuova_versione = check_for_updates()

    def init_ui(self):
        self.layout_centrale = QVBoxLayout(self)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        path_logo = resource_path(os.path.join("images", "logo.png"))
        if os.path.exists(path_logo):
            pix = QPixmap(path_logo)
            screen_w = QApplication.primaryScreen().size().width()
            self.logo_label.setPixmap(pix.scaled(int(screen_w * 0.8), int(screen_w * 0.5), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("GIRA LA RUOTA")
            self.logo_label.setStyleSheet("color: gold; font-size: 100px; font-weight: bold;")
        self.opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        self.logo_label.setGraphicsEffect(self.opacity_effect)
        self.layout_centrale.addWidget(self.logo_label)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(2500); self.anim.setStartValue(0); self.anim.setEndValue(1); self.anim.start()
        self.btn_skip = QPushButton("SALTA INTRO ⏭", self)
        self.btn_skip.setFixedSize(220, 60)
        self.btn_skip.setStyleSheet("background-color: gold; color: black; font-weight: bold; border-radius: 15px;")
        self.btn_skip.clicked.connect(self.concludi_intro)

    def resizeEvent(self, event):
        self.btn_skip.move(self.width() - 250, self.height() - 100)

    def play_intro_music(self):
        sigla = resource_path("sound/sigla.wav")
        if os.path.exists(sigla):
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(sigla)))
            self.media_player.play()
            self.media_player.mediaStatusChanged.connect(lambda s: self.concludi_intro() if s == QMediaPlayer.EndOfMedia else None)
        else: QTimer.singleShot(4000, self.concludi_intro)

    def concludi_intro(self):
        self.media_player.stop()
        if self.nuova_versione:
            QMessageBox.information(self, "Aggiornamento", f"Nuova versione v{self.nuova_versione} disponibile!")
        self.game = GiraLaRuota()
        self.game.avvia_configurazione()
        self.close()

class GiraLaRuota(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = get_db_path()
        self.carica_database()

        # --- LOGICA MEMORIA FRASI ---
        self.frasi_usate = set()

        self.turno_attuale = 0
        self.round_corrente = 1
        self.tot_round = 3
        self.portafogli_round = [0, 0, 0]
        self.montepremi_totale = [0, 0, 0]
        self.ha_jolly = [False, False, False]
        self.lettere_indovinate = set()
        self.is_muted = False
        self.coriandoli = []
        self.timer_abilitato = True
        self.secondi_timer = 7
        self.valore_ruota = 0
        self.premi_base = [100, 300, 500, 1000, "BANCAROTTA", "PASSA", 200, 400, 800, 150, 250, 600]
        self.premi_correnti = []

        self.timer_gioco = QTimer(); self.timer_gioco.timeout.connect(self.aggiorna_timer)
        self.timer_coriandoli = QTimer(); self.timer_coriandoli.timeout.connect(self.aggiorna_animazione_coriandoli)
        self.timer_spin_visivo = QTimer(); self.timer_spin_visivo.timeout.connect(self.effetto_ruota_scorrimento)

        self.init_audio(); self.init_ui()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space and self.btn_spin.isEnabled():
            self.anim_ruota()

    def carica_database(self):
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f: self.database = json.load(f)
        except: self.database = {"GENERAL": ["GIRA LA RUOTA"]}

    def salva_database(self):
        with open(self.db_path, 'w', encoding='utf-8') as f: json.dump(self.database, f, indent=4, ensure_ascii=False)

    def init_audio(self):
        self.suoni = {}
        for k in ["spin", "bad", "correct", "victory"]:
            p = QMediaPlayer()
            p.setMedia(QMediaContent(QUrl.fromLocalFile(resource_path(f"sound/{k}.wav"))))
            self.suoni[k] = p
        self.bg_player = QMediaPlayer()
        bg_file = resource_path("sound/background.wav")
        if os.path.exists(bg_file):
            self.playlist = QMediaPlaylist(); self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(bg_file)))
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop); self.bg_player.setPlaylist(self.playlist); self.bg_player.setVolume(15)

    def init_ui(self):
        self.setWindowTitle(f"Gira la Ruota v{VERSION_ATTUALE}")
        self.setStyleSheet("background-color: #002244;")
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.btn_set = QPushButton("🛠"); self.btn_next_phrase = QPushButton("⏭️")
        self.btn_mute = QPushButton("🔊"); self.btn_cheat = QPushButton("👁️"); self.btn_exit = QPushButton("❌")
        for b in [self.btn_set, self.btn_next_phrase, self.btn_mute, self.btn_cheat, self.btn_exit]:
            b.setFixedSize(60, 60); b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet("background-color: #333; color: gold; border: 2px solid gold; border-radius: 30px; font-size: 22px;")
        self.btn_exit.setStyleSheet("background-color: #900; color: white; border: 2px solid white; border-radius: 30px;")
        self.btn_set.clicked.connect(self.menu_impostazioni); self.btn_next_phrase.clicked.connect(self.skip_phrase)
        self.btn_mute.clicked.connect(self.toggle_mute); self.btn_exit.clicked.connect(self.close)
        self.btn_cheat.clicked.connect(lambda: QMessageBox.information(self, "Soluzione", f"La frase è: {self.soluzione}"))
        top.addWidget(self.btn_set); top.addWidget(self.btn_next_phrase); top.addWidget(self.btn_mute); top.addStretch(); top.addWidget(self.btn_cheat); top.addWidget(self.btn_exit)
        layout.addLayout(top)

        info_lay = QHBoxLayout()
        self.label_round = QLabel("ROUND 1/3")
        self.label_round.setStyleSheet("font-size: 24px; color: white; font-weight: bold; background: rgba(0,0,0,0.3); padding: 5px 15px; border-radius: 10px;")
        self.label_cat = QLabel(""); self.label_cat.setAlignment(Qt.AlignCenter)
        self.label_cat.setStyleSheet("font-size: 32px; color: gold; font-weight: bold; padding: 10px;")
        info_lay.addWidget(self.label_round); info_lay.addStretch(); info_lay.addWidget(self.label_cat); info_lay.addStretch(); info_lay.addWidget(QLabel("          "))
        layout.addLayout(info_lay)

        self.grid_container = QFrame()
        self.grid_layout = QGridLayout(self.grid_container); self.grid_layout.setSpacing(5)
        self.celle = []
        self.righe_config = [12, 14, 14, 12]
        for r in range(4):
            riga = []
            for c in range(14):
                lbl = QLabel(""); lbl.setFixedSize(58, 78); lbl.setAlignment(Qt.AlignCenter)
                lbl.setFont(QFont("Arial", 30, QFont.Bold))
                self.grid_layout.addWidget(lbl, r, c); riga.append(lbl)
            self.celle.append(riga)
        layout.addWidget(self.grid_container, alignment=Qt.AlignCenter)

        self.progress = QProgressBar(); self.progress.setFixedHeight(15); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #0F0; }")
        layout.addWidget(self.progress)

        self.label_ruota = QLabel("GIRA LA RUOTA!"); self.label_ruota.setAlignment(Qt.AlignCenter)
        self.label_ruota.setStyleSheet("color: white; font-size: 38px; background: black; border: 3px solid gold; padding: 15px; font-weight: bold;")
        layout.addWidget(self.label_ruota)

        self.lay_gio = QHBoxLayout(); self.lab_gio = []
        for i in range(3):
            l = QLabel(""); l.setAlignment(Qt.AlignCenter); l.setMinimumWidth(300)
            self.lay_gio.addWidget(l); self.lab_gio.append(l)
        layout.addLayout(self.lay_gio)

        btns = QHBoxLayout()
        self.btn_spin = QPushButton("🎡 GIRA RUOTA (Space)"); self.btn_vow = QPushButton("💵 VOCALE (-500€)")
        self.btn_pass = QPushButton("✋ PASSA"); self.btn_sol = QPushButton("💡 RISOLVI")
        for b in [self.btn_spin, self.btn_vow, self.btn_pass, self.btn_sol]:
            b.setFixedSize(260, 75); b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet("background-color: gold; color: black; font-weight: bold; border-radius: 15px; font-size: 18px;")
            btns.addWidget(b)
        self.btn_spin.clicked.connect(self.anim_ruota); self.btn_vow.clicked.connect(self.buy_vowel)
        self.btn_pass.clicked.connect(self.manual_pass); self.btn_sol.clicked.connect(self.solve)
        layout.addLayout(btns)

    def agg_tabellone(self):
        stile_vuoto = "background-color: transparent; border: none;"
        stile_blu = "background-color: #003366; border: 2px solid #001122;"
        stile_bianco = "background-color: white; border: 2px solid #000;"
        for r in range(4):
            for c in range(14):
                self.celle[r][c].setText(""); self.celle[r][c].setStyleSheet(stile_vuoto)
        parole = self.soluzione.split(" "); righe_testo = [[], [], [], []]; r_idx = 1
        spazio_rimanente = self.righe_config[r_idx]
        for p in parole:
            if len(p) > spazio_rimanente:
                r_idx += 1
                if r_idx > 3: r_idx = 3
                spazio_rimanente = self.righe_config[r_idx]
            righe_testo[r_idx].append(p); spazio_rimanente -= (len(p) + 1)
        for r in range(4):
            num_attive = self.righe_config[r]
            off_griglia = (14 - num_attive) // 2
            for c in range(num_attive): self.celle[r][off_griglia + c].setStyleSheet(stile_blu)
            if righe_testo[r]:
                frase_riga = " ".join(righe_testo[r])
                inizio_testo = off_griglia + (num_attive - len(frase_riga)) // 2
                for i, char in enumerate(frase_riga):
                    colonna_dest = inizio_testo + i
                    if 0 <= colonna_dest < 14:
                        lbl = self.celle[r][colonna_dest]
                        if char != " ":
                            lbl.setStyleSheet(stile_bianco)
                            if char in self.lettere_indovinate or not char.isalpha():
                                lbl.setText(char); lbl.setStyleSheet("background-color: white; color: black; border: 2px solid #000;")

    def avvia_configurazione(self):
        self.giocatori = []
        for i in range(3):
            n, ok = QInputDialog.getText(self, "Setup", f"Nome Giocatore {i+1}:")
            self.giocatori.append(n.strip().upper() if ok and n.strip() else f"GIOCATORE {i+1}")
        res = QMessageBox.question(self, "Timer", "Attivare il timer?", QMessageBox.Yes|QMessageBox.No)
        self.timer_abilitato = (res == QMessageBox.Yes)
        if self.timer_abilitato:
            sec, _ = QInputDialog.getInt(self, "Timer", "Secondi:", 7, 3, 60); self.secondi_timer = sec
        nr, _ = QInputDialog.getInt(self, "Round", "Quanti round?", 3, 1, 10); self.tot_round = nr
        self.showFullScreen(); self.nuovo_round()

    def nuovo_round(self):
        if self.round_corrente > self.tot_round: self.classifica(); return
        self.bg_player.play()
        self.label_round.setText(f"ROUND {self.round_corrente}/{self.tot_round}")

        # --- LOGICA SELEZIONE FRASE UNICA ---
        scelte_possibili = []
        for cat, frasi in self.database.items():
            for f in frasi:
                if f.upper() not in self.frasi_usate:
                    scelte_possibili.append((cat, f.upper()))

        if not scelte_possibili: # Se abbiamo finito le frasi, resetta la memoria
            self.frasi_usate.clear()
            cat = random.choice(list(self.database.keys()))
            f_scelta = random.choice(self.database[cat]).upper()
        else:
            cat, f_scelta = random.choice(scelte_possibili)

        self.frasi_usate.add(f_scelta)
        self.categoria = cat
        self.soluzione = f_scelta
        # ------------------------------------

        self.lettere_indovinate = set(); self.portafogli_round = [0,0,0]
        self.label_cat.setText(self.categoria); self.agg_tabellone(); self.agg_giocatori()
        self.btn_spin.setEnabled(True); self.btn_sol.setEnabled(True)

    def anim_ruota(self):
        self.btn_spin.setEnabled(False); self.btn_vow.setEnabled(False); self.btn_sol.setEnabled(False)
        self.play_sound("spin"); self.timer_spin_visivo.start(80)

    def effetto_ruota_scorrimento(self):
        if self.suoni["spin"].state() == QMediaPlayer.PlayingState:
            self.label_ruota.setText(str(random.choice(self.premi_correnti)))
        else: self.timer_spin_visivo.stop(); self.stop_ruota()

    def stop_ruota(self):
        res = random.choice(self.premi_correnti if self.premi_correnti else self.premi_base)
        self.label_ruota.setText(str(res))
        if res == "BANCAROTTA":
            usato = False
            if self.ha_jolly[self.turno_attuale]:
                if QMessageBox.question(self, "Jolly", "Usi il JOLLY?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    self.ha_jolly[self.turno_attuale] = False; usato = True; self.btn_spin.setEnabled(True); self.btn_sol.setEnabled(True)
            if not usato: self.portafogli_round[self.turno_attuale] = 0; self.play_sound("bad"); self.next_turn()
        elif res == "PASSA":
            usato = False
            if self.ha_jolly[self.turno_attuale]:
                if QMessageBox.question(self, "Jolly", "Usi il JOLLY?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    self.ha_jolly[self.turno_attuale] = False; usato = True; self.btn_spin.setEnabled(True); self.btn_sol.setEnabled(True)
            if not usato: self.play_sound("bad"); self.next_turn()
        elif res == "JOLLY":
            self.ha_jolly[self.turno_attuale] = True
            if "JOLLY" in self.premi_correnti: self.premi_correnti.remove("JOLLY")
            self.valore_ruota = 500; self.start_timer(consonants_only=True)
        else: self.valore_ruota = res; self.start_timer(consonants_only=True)

    def start_timer(self, consonants_only=False):
        if self.timer_abilitato:
            self.rem_t = self.secondi_timer * 10; self.progress.setMaximum(self.rem_t); self.timer_gioco.start(100)
        self.ask_letter(is_vowel=False, consonants_only=consonants_only)

    def ask_letter(self, is_vowel=False, consonants_only=False):
        tipo = "CONSONANTE" if consonants_only else ("VOCALE" if is_vowel else "LETTERA")
        let, ok = QInputDialog.getText(self, "Lettera", f"Chiama una {tipo}:")
        self.timer_gioco.stop()
        if ok and len(let.strip()) == 1:
            let = let.strip().upper()
            if consonants_only and let not in CONSONANTI: self.next_turn(); return
            if is_vowel and let not in VOCALI: self.next_turn(); return
            if let in self.soluzione and let not in self.lettere_indovinate:
                self.lettere_indovinate.add(let)
                if not is_vowel: self.portafogli_round[self.turno_attuale] += (self.soluzione.count(let) * self.valore_ruota)
                self.play_sound("correct"); self.agg_tabellone(); self.agg_giocatori()
                self.btn_spin.setEnabled(True); self.btn_sol.setEnabled(True)
            else: self.play_sound("bad"); self.next_turn()
        else: self.next_turn()

    def aggiorna_timer(self):
        self.rem_t -= 1; self.progress.setValue(self.rem_t)
        if self.rem_t <= 0: self.timer_gioco.stop(); self.next_turn()

    def next_turn(self):
        self.turno_attuale = (self.turno_attuale + 1) % 3
        self.btn_spin.setEnabled(True); self.btn_sol.setEnabled(True); self.agg_giocatori()

    def agg_giocatori(self):
        for i in range(3):
            att = (i == self.turno_attuale); j = " 🍀" if self.ha_jolly[i] else ""
            self.lab_gio[i].setStyleSheet(f"background: {'#0F0' if att else '#333'}; color: {'#000' if att else '#FFF'}; border: 2px solid gold; border-radius: 12px; padding: 15px; font-weight: bold;")
            self.lab_gio[i].setText(f"{self.giocatori[i]}{j}\nRound: {self.portafogli_round[i]}€\nTot: {self.montepremi_totale[i]}€")
        self.btn_vow.setEnabled(self.portafogli_round[self.turno_attuale] >= 500)

    def buy_vowel(self):
        if self.portafogli_round[self.turno_attuale] >= 500:
            self.portafogli_round[self.turno_attuale] -= 500
            self.btn_spin.setEnabled(False); self.btn_sol.setEnabled(False); self.agg_giocatori(); self.ask_letter(is_vowel=True)

    def manual_pass(self):
        if QMessageBox.question(self, "Passa", "Passi il turno?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes: self.next_turn()

    def skip_phrase(self):
        if QMessageBox.question(self, "Salta", "Passi alla prossima frase?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes: self.nuovo_round()

    def solve(self):
        self.timer_gioco.stop()
        res, ok = QInputDialog.getText(self, "Risolvi", "La soluzione è:")
        if ok and res.strip().upper() == self.soluzione:
            self.lettere_indovinate = set(self.soluzione.replace(" ", ""))
            self.agg_tabellone(); self.play_sound("victory")
            self.portafogli_round[self.turno_attuale] += 2000
            QTimer.singleShot(3000, self.sequenza_vittoria_finale)
        else: self.play_sound("bad"); self.next_turn()

    def sequenza_vittoria_finale(self):
        self.avvia_coriandoli(); self.montepremi_totale[self.turno_attuale] += self.portafogli_round[self.turno_attuale]
        self.agg_giocatori(); QTimer.singleShot(4000, self.incrementa_round)

    def incrementa_round(self): self.round_corrente += 1; self.nuovo_round()

    def avvia_coriandoli(self): self.coriandoli = [Coriandolo(self.width()) for _ in range(160)]; self.timer_coriandoli.start(30)
    def aggiorna_animazione_coriandoli(self):
        for c in self.coriandoli: c.caduta()
        if all(c.y > self.height() for c in self.coriandoli): self.timer_coriandoli.stop(); self.coriandoli = []
        self.update()
    def paintEvent(self, e):
        if self.coriandoli:
            p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
            for c in self.coriandoli: p.setBrush(c.color); p.drawRect(int(c.x), int(c.y), c.size, c.size)

    def toggle_mute(self):
        self.is_muted = not self.is_muted; self.bg_player.setMuted(self.is_muted)
        for s in self.suoni.values(): s.setMuted(self.is_muted)
        self.btn_mute.setText("🔇" if self.is_muted else "🔊")

    def play_sound(self, n):
        if n in self.suoni and not self.is_muted: self.suoni[n].stop(); self.suoni[n].play()

    def menu_impostazioni(self):
        d = JsonEditorDialog(self.database, self)
        if d.exec_():
            new = d.get_data()
            if isinstance(new, dict): self.database = new; self.salva_database()

    def classifica(self):
        self.bg_player.stop()
        risultati = sorted(zip(self.giocatori, self.montepremi_totale), key=lambda x: x[1], reverse=True)
        testo = "📊 CLASSIFICA FINALE 📊\n\n"
        for i, (n, p) in enumerate(risultati):
            m = "🥇 " if i == 0 else ("🥈 " if i == 1 else "🥉 ")
            testo += f"{m}{n}: {p}€\n"
        testo += "\nVuoi iniziare una nuova partita?"
        if QMessageBox.question(self, "Fine Gioco", testo, QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes: self.reset_totale_gioco()
        else: self.close()

    def reset_totale_gioco(self):
        self.montepremi_totale = [0, 0, 0]; self.portafogli_round = [0, 0, 0]
        self.ha_jolly = [False, False, False]; self.round_corrente = 1; self.turno_attuale = 0
        self.lettere_indovinate = set(); self.avvia_configurazione()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    sys.exit(app.exec_())
