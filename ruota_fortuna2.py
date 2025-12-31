import sys
import random
import json  # <-- Nuovo modulo per gestire il database
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QHBoxLayout, QLabel, QMessageBox, QInputDialog,
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class PrizeSlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.premi = ["1000","500","300","BANCO","400","200","600","JOLLY","150","450",
                      "PASSA","250","800","350","100","PERDE","200","400","700","JOLLY","300","2000","150","BANCO"]
        layout = QVBoxLayout(self)
        self.label = QLabel("🎡 GIRA!")
        self.label.setAlignment(Qt.AlignCenter)
        self.set_style("#3498db")
        layout.addWidget(self.label)
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.current_interval = 50

    def set_style(self, bg_color):
        self.label.setStyleSheet(f"font: bold 60pt sans-serif; color: white; background-color: {bg_color}; border: 8px solid #f1c40f; border-radius: 20px; padding: 10px;")

    def start_flash(self, target):
        self.target_premio = target
        self.current_interval = 50
        self.timer.start(self.current_interval)
        if self.parent: self.parent.play_sound("spin")

    def animate(self):
        if self.parent and self.parent.sounds["spin"].state() == QMediaPlayer.PlayingState:
            self.label.setText(random.choice(self.premi))
            self.set_style(f"#{random.randint(0x222222, 0x888888):06x}")
            pos = self.parent.sounds["spin"].position()
            dur = self.parent.sounds["spin"].duration()
            if dur > 0:
                progresso = pos / dur
                if progresso > 0.7: self.current_interval = 150
                if progresso > 0.9: self.current_interval = 300
                self.timer.setInterval(self.current_interval)
        else:
            self.timer.stop()
            self.label.setText(f"✨ {self.target_premio}")
            self.set_style("#e74c3c" if self.target_premio in ["BANCO", "PERDE", "PASSA"] else "#2ecc71")
            if self.parent: self.parent.handle_wheel_result(self.target_premio)

class RuotaGioco(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("La Ruota della Fortuna")
        self.showFullScreen()
        self.setStyleSheet("background-color: #1e272e; color: white;")

        # Carica il database JSON
        self.dati_gioco = self.load_database()

        self.giocatori = []
        self.portafogli_round, self.montepremi_totale, self.jolly = [], [], []
        self.turno_attuale = 0
        self.round_attuale = 1
        self.totale_round = 1

        self.setup_game()
        self.sounds = {}
        self.load_sounds()
        self.init_ui()
        self.nuovo_round()

    def load_database(self):
        """Carica le frasi dal file JSON esterno."""
        percorso = Path(__file__).parent / "frasi.json"
        try:
            with open(percorso, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Errore", "File 'frasi.json' non trovato!\nIl gioco verrà chiuso.")
            sys.exit()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel database: {e}")
            sys.exit()

    def setup_game(self):
        num, ok = QInputDialog.getInt(self, "⚙️ Setup", "Quanti giocatori? (1-5)", 3, 1, 5)
        if not ok: sys.exit()
        for i in range(num):
            nome, ok = QInputDialog.getText(self, "👤 Nome", f"Nome Giocatore {i+1}:")
            nome_p = nome.strip() if ok and nome.strip() else f"Giocatore {i+1}"
            generi = ["Maschio 👨", "Femmina 👩"]
            genere, ok = QInputDialog.getItem(self, "🚻 Genere", f"Seleziona genere per {nome_p}:", generi, 0, False)
            g_icon = "M" if "Maschio" in genere else "F"
            self.giocatori.append({"nome": nome_p, "genere": g_icon})
            self.portafogli_round.append(0); self.montepremi_totale.append(0); self.jolly.append(0)

        rd, ok = QInputDialog.getInt(self, "🏁 Round", "Quanti round volete giocare?", 3, 1, 10)
        if ok: self.totale_round = rd

    def nuovo_round(self):
        self.categoria = random.choice(list(self.dati_gioco.keys()))
        self.soluzione = random.choice(self.dati_gioco[self.categoria]).strip().upper()
        self.lettere_indovinate = []
        for i in range(len(self.giocatori)): self.portafogli_round[i] = 0
        if hasattr(self, 'label_cat'):
            self.label_cat.setText(f"🔔 ROUND {self.round_attuale}/{self.totale_round} - {self.categoria}")
            self.update_tabellone(); self.update_status()

    def load_sounds(self):
        sound_dir = Path(__file__).parent / "sound"
        sound_files = {"spin": "spin.wav", "correct": "correct.wav", "bad": "bad.wav"}
        for key, filename in sound_files.items():
            path = sound_dir / filename
            if path.exists():
                player = QMediaPlayer(self)
                player.setMedia(QMediaContent(QUrl.fromLocalFile(str(path.absolute()))))
                self.sounds[key] = player

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].stop(); self.sounds[name].play()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.label_cat = QLabel()
        self.label_cat.setStyleSheet("font: bold 24px sans-serif; color: #ffa502; background: #2f3542; padding: 10px; border-radius: 10px;")
        self.label_cat.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label_cat)
        self.label_tabellone = QLabel()
        self.label_tabellone.setAlignment(Qt.AlignCenter)
        self.label_tabellone.setWordWrap(True)
        self.label_tabellone.setStyleSheet("font: bold 38pt 'Courier New'; background: #10ac84; border: 4px solid white; border-radius: 15px; min-height: 200px;")
        main_layout.addWidget(self.label_tabellone)
        bottom_area = QHBoxLayout()
        game_controls = QVBoxLayout()
        self.label_turno = QLabel()
        self.label_turno.setStyleSheet("font: bold 22px sans-serif; color: #3498db;")
        self.label_turno.setAlignment(Qt.AlignCenter)
        self.slot = PrizeSlot(self)
        self.btn_spin = QPushButton("🎡 GIRA LA RUOTA")
        self.btn_vowel = QPushButton("🅰️ VOCALE (500€)")
        self.btn_solve = QPushButton("💡 RISOLVI")
        self.btn_cheat = QPushButton("🕵️ Cheat")
        self.btn_cheat.setFixedWidth(100)
        self.btn_cheat.setStyleSheet("background: #485460; color: #d2dae2; font: bold 12px sans-serif; border-radius: 5px; border: none; padding: 3px;")
        btn_style = "QPushButton { background: #ffa502; color: #1e272e; font: bold 18px sans-serif; border-radius: 10px; padding: 12px; } QPushButton:hover { background: #ffbc40; } QPushButton:disabled { background: #57606f; }"
        for b in [self.btn_spin, self.btn_vowel, self.btn_solve]:
            b.setStyleSheet(btn_style); b.setFocusPolicy(Qt.NoFocus)
        game_controls.addWidget(self.label_turno); game_controls.addWidget(self.slot); game_controls.addWidget(self.btn_spin)
        h_btns = QHBoxLayout(); h_btns.addWidget(self.btn_vowel); h_btns.addWidget(self.btn_solve)
        game_controls.addLayout(h_btns); game_controls.addWidget(self.btn_cheat, 0, Qt.AlignLeft)
        bottom_area.addLayout(game_controls, 3)
        self.lista_ui = QListWidget()
        self.lista_ui.setFixedWidth(380); self.lista_ui.setSpacing(10)
        self.lista_ui.setStyleSheet("QListWidget { background: #2f3542; border-radius: 10px; border: 2px solid #3498db; outline: none; padding: 10px; }")
        bottom_area.addWidget(self.lista_ui, 1)
        main_layout.addLayout(bottom_area)
        self.btn_spin.clicked.connect(self.spin_now); self.btn_vowel.clicked.connect(self.buy_vowel)
        self.btn_solve.clicked.connect(self.solve_phrase); self.btn_cheat.clicked.connect(self.show_cheat)

    def update_tabellone(self):
        display = ""
        for char in self.soluzione:
            if char == " ": display += "  "
            elif char in self.lettere_indovinate or char in "'’": display += char
            else: display += "_"
        self.label_tabellone.setText(" ".join(list(display)))

    def update_status(self):
        self.lista_ui.clear()
        for i, (g, p, m, j) in enumerate(zip(self.giocatori, self.portafogli_round, self.montepremi_totale, self.jolly)):
            avatar = "👩" if g["genere"] == "F" else "👨"
            turno = "⚡" if i == self.turno_attuale else ""
            riga_1 = f"{turno} {avatar} {g['nome']} {'🍀' * j}"
            riga_2 = f"💰 {p}€ | 🏆 {m}€"
            item = QListWidgetItem(f"{riga_1}\n{riga_2}")
            item.setFont(QFont("sans-serif", 11 if i != self.turno_attuale else 13, QFont.Bold))
            if i == self.turno_attuale:
                item.setForeground(QColor("#3498db")); item.setBackground(QColor("#34495e"))
            else:
                item.setForeground(QColor("white"))
            self.lista_ui.addItem(item)
        self.label_turno.setText(f"⭐ TURNO DI: {self.giocatori[self.turno_attuale]['nome'].upper()}")

    def spin_now(self):
        self.toggle_btns(False); self.slot.start_flash(random.choice(self.slot.premi))

    def toggle_btns(self, s):
        self.btn_spin.setEnabled(s); self.btn_vowel.setEnabled(s); self.btn_solve.setEnabled(s)

    def handle_wheel_result(self, res):
        idx = self.turno_attuale
        if res in ["BANCO", "PASSA", "PERDE"]:
            if self.jolly[idx] > 0:
                if QMessageBox.question(self, "🍀 JOLLY", "Usa un Jolly?") == QMessageBox.Yes:
                    self.jolly[idx] -= 1; self.update_status(); self.toggle_btns(True); return
            self.play_sound("bad")
            if res == "BANCO": self.portafogli_round[idx] = 0
            QMessageBox.warning(self, "💥", f"Sfortuna: {res}!"); self.next_turn()
        else:
            self.play_sound("correct")
            self.ask_letter(500 if res == "JOLLY" else int(res), is_jolly=(res == "JOLLY"))

    def ask_letter(self, valore, is_vowel=False, is_jolly=False):
        tipo = "VOCALE" if is_vowel else "CONSONANTE"
        let, ok = QInputDialog.getText(self, tipo, f"Valore: {valore}€\nLettera:")
        if ok and let:
            let = let.upper().strip()[0]
            if let in self.lettere_indovinate:
                QMessageBox.warning(self, "!", "Già detta!"); self.toggle_btns(True); return
            count = self.soluzione.count(let)
            if count > 0:
                vincita = valore * count
                self.lettere_indovinate.append(let)
                self.portafogli_round[self.turno_attuale] += vincita
                if is_jolly: self.jolly[self.turno_attuale] += 1
                QMessageBox.information(self, "✨", f"Lettera '{let}' presente {count} volte!\nHai vinto {vincita}€!")
                self.update_tabellone(); self.play_sound("correct")
                if not self.check_win(): self.toggle_btns(True)
            else:
                self.play_sound("bad"); QMessageBox.information(self, "❌", "Non presente."); self.next_turn()
        else: self.toggle_btns(True)
        self.update_status()

    def solve_phrase(self):
        risp, ok = QInputDialog.getText(self, "🔍", "Soluzione:")
        if ok and risp.upper().strip() == self.soluzione:
            self.montepremi_totale[self.turno_attuale] += self.portafogli_round[self.turno_attuale]
            self.fine_round()
        else: QMessageBox.critical(self, "❌", "Sbagliato!"); self.next_turn()

    def fine_round(self):
        vincitore = self.giocatori[self.turno_attuale]['nome']
        QMessageBox.information(self, "🎉", f"Grande {vincitore}, round vinto!")
        if self.round_attuale < self.totale_round:
            self.round_attuale += 1; self.nuovo_round(); self.toggle_btns(True)
        else:
            cl = sorted(zip(self.giocatori, self.montepremi_totale), key=lambda x: x[1], reverse=True)
            QMessageBox.information(self, "🏆", f"VINCITORE: {cl[0][0]['nome']} con {cl[0][1]}€"); self.close()

    def buy_vowel(self):
        if self.portafogli_round[self.turno_attuale] >= 500:
            self.portafogli_round[self.turno_attuale] -= 500; self.ask_letter(0, True)
        else: QMessageBox.warning(self, "💸", "Servono 500€!")

    def next_turn(self):
        self.turno_attuale = (self.turno_attuale + 1) % len(self.giocatori)
        self.toggle_btns(True); self.update_status()

    def check_win(self):
        if not [c for c in self.soluzione if c.isalpha() and c not in self.lettere_indovinate]:
            self.montepremi_totale[self.turno_attuale] += self.portafogli_round[self.turno_attuale]
            self.fine_round(); return True
        return False

    def show_cheat(self):
        QMessageBox.information(self, "🕵️ Cheat", f"La soluzione è: {self.soluzione}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and self.btn_spin.isEnabled(): self.spin_now()
        elif event.key() == Qt.Key_Escape: self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = RuotaGioco()
    game.show()
    sys.exit(app.exec_())
