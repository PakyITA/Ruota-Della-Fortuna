import sys
import os
import random
import math
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QHBoxLayout, QLabel, QMessageBox, QInputDialog,
                             QListWidget)
from PyQt5.QtCore import Qt, QTimer, QPoint, QUrl
from PyQt5.QtGui import QPainter, QPixmap, QColor, QFont, QPolygon, QPen, QFontMetrics
from PyQt5.QtMultimedia import QSoundEffect

# --- DATABASE DI GIOCO ---
DATI_GIOCO = {
    "PROVERBI": [
        "A CAVAL DONATO NON SI GUARDA IN BOCCA",
        "IL LUPO PERDE IL PELO MA NON IL VIZIO",
        "CHI DORME NON PIGLIA PESCI"
    ],
    "CINEMA": [
        "LA VITA E BELLA",
        "IL GLADIATORE",
        "RITORNO AL FUTURO",
        "IL PADRINO"
    ],
    "GEOGRAFIA": [
        "STATI D'AMERICA",
        "MAR MEDITERRANEO",
        "GRAN BRETAGNA"
    ],
    "CUCINA": [
        "PIZZA MARGHERITA",
        "SPAGHETTI ALLA CARBONARA",
        "LASAGNE AL FORNO"
    ]
}

# --- WHEEL ---
class WheelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(450, 450)
        self.num_spicchi = 24
        self.premi = [
            "1000", "500", "300", "BANCO", "400", "200",
            "600", "JOLLY", "150", "450", "PASSA", "250",
            "800", "350", "100", "PERDE", "200", "400",
            "700", "JOLLY", "300", "2000", "150", "BANCO"
        ]
        self.angle = 0
        self.speed = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.spin_step)
        self.parent = parent
        self._wheel_pixmap = None
        self._last_size = 0
        self.spinning = False

    def create_wheel_pixmap(self, size):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = size // 2, size // 2
        r = size // 2 - 25
        step_deg = 360 / self.num_spicchi
        colors = [QColor("#e6194b"), QColor("#3cb44b"), QColor("#ffe119"), QColor("#4363d8"),
                  QColor("#f58231"), QColor("#911eb4"), QColor("#46f0f0"), QColor("#f032e6")]
        font = QFont("Courier New", max(9, int(size // 42)), QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)

        for i in range(self.num_spicchi):
            start_angle = 90 - (i * step_deg) - (step_deg / 2)
            painter.setBrush(colors[i % len(colors)])
            painter.setPen(QPen(Qt.black, 1))
            painter.drawPie(cx - r, cy - r, 2*r, 2*r, int(start_angle * 16), int(-step_deg * 16))

            angolo_mid = math.radians(start_angle - step_deg / 2)
            tx = cx + (r * 0.75) * math.cos(angolo_mid)
            ty = cy - (r * 0.75) * math.sin(angolo_mid)
            testo = self.premi[i]
            tw, th = fm.horizontalAdvance(testo), fm.height()
            painter.setPen(Qt.black)
            painter.drawText(int(tx - tw/2), int(ty + th/4), testo)
        painter.end()
        return pix

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = min(self.width(), self.height())
        if size <= 0: return
        if self._wheel_pixmap is None or self._last_size != size:
            self._wheel_pixmap = self.create_wheel_pixmap(size)
            self._last_size = size
        cx, cy = self.width() // 2, self.height() // 2
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        painter.drawPixmap(-size//2, -size//2, self._wheel_pixmap)
        painter.restore()

        painter.setBrush(QColor("#ff3f34"))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawPolygon(QPolygon([QPoint(cx-25, 5), QPoint(cx+25, 5), QPoint(cx, 50)]))

    def spin_step(self):
        if self.speed > 0.1:
            self.angle = (self.angle + self.speed) % 360
            self.speed *= 0.985
            self.update()
        else:
            self.timer.stop()
            if self.spinning:
                self.parent.sounds["spin"].stop()
                self.spinning = False
            self.parent.toggle_buttons(True)
            self.process_result()

    def process_result(self):
        step = 360 / self.num_spicchi
        indice = int(math.floor((360 - (self.angle % 360) + step/2) / step)) % self.num_spicchi
        res = self.premi[indice]
        self.parent.handle_wheel_result(res)

# --- GIOCO ---
class RuotaGioco(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("La Ruota della Fortuna")
        self.setMinimumSize(1100, 850)
        self.setStyleSheet("background-color: #1e272e; color: white;")

        self.giocatori, self.portafogli, self.turno_attuale = [], [], 0
        self.round_attuale = 1
        self.sound_folder = "sound"
        self.load_sounds()
        self.setup_players()
        self.nuovo_round()
        self.init_ui()

    # --- SUONI ---
    def load_sounds(self):
        self.sounds = {}
        for name in ["spin", "correct", "bad"]:
            effect = QSoundEffect()
            file_path = os.path.join(self.sound_folder, f"{name}.wav")
            if not os.path.exists(file_path):
                print(f"Attenzione: il file {file_path} non esiste!")
                continue
            effect.setSource(QUrl.fromLocalFile(file_path))
            effect.setVolume(0.5)
            self.sounds[name] = effect

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].stop()
            self.sounds[name].play()

    # --- SETUP GIOCATORI ---
    def setup_players(self):
        num, ok = QInputDialog.getInt(self, "Setup", "Quanti giocatori?", 3, 1, 8)
        if not ok: sys.exit()
        for i in range(num):
            nome, ok = QInputDialog.getText(self, "Nomi", f"Nome Giocatore {i+1}:")
            self.giocatori.append(nome if ok and nome else f"G{i+1}")
            self.portafogli.append(0)
        self.num_round, ok = QInputDialog.getInt(self, "Setup", "Quanti round vuoi giocare?", 1, 1)
        if not ok:
            self.num_round = 1

    # --- ROUND ---
    def nuovo_round(self):
        self.categoria = random.choice(list(DATI_GIOCO.keys()))
        self.soluzione = random.choice(DATI_GIOCO[self.categoria]).strip().upper()
        self.lettere_indovinate = []

    # --- INTERFACCIA ---
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.label_cat = QLabel()
        self.label_cat.setAlignment(Qt.AlignCenter)
        self.label_cat.setStyleSheet("font: bold 28px 'Courier New'; color: #ffa502; background: #2f3542; padding: 15px; border-radius: 12px;")
        layout.addWidget(self.label_cat)

        self.label_tabellone = QLabel()
        self.label_tabellone.setAlignment(Qt.AlignCenter)
        self.label_tabellone.setStyleSheet("""
            font: bold 36px 'Courier New';
            background: #10ac84;
            border: 5px solid #ffa502;
            padding: 40px;
            border-radius: 15px;
            color: white;
        """)
        self.label_tabellone.setWordWrap(True)
        layout.addWidget(self.label_tabellone)

        middle = QHBoxLayout()
        wheel_box = QVBoxLayout()
        self.label_turno = QLabel()
        self.label_turno.setAlignment(Qt.AlignCenter)
        self.label_turno.setStyleSheet("font: bold 26px 'Courier New'; color: #3498db; padding: 10px;")

        self.ruota = WheelWidget(self)
        self.btn_spin = QPushButton("GIRA LA RUOTA")
        self.btn_vowel = QPushButton("COMPRA VOCALE (500€)")
        self.btn_solve = QPushButton("RISOLVI (FRASE COMPLETA)")
        self.btn_cheat = QPushButton("MOSTRA SOLUZIONE (CHEAT)")

        for b in [self.btn_spin, self.btn_vowel, self.btn_solve, self.btn_cheat]:
            b.setMinimumHeight(55)
            b.setStyleSheet("""
                background: #ffa502;
                color: #1e272e;
                font: bold 20px 'Courier New';
                border-radius: 25px;
            """)
        self.btn_cheat.setStyleSheet("background: #eb4d4b; color: white; font: bold 20px; border-radius: 25px; border: 2px solid white;")
        self.btn_cheat.clicked.connect(self.show_solution)

        self.btn_spin.clicked.connect(self.spin_now)
        self.btn_vowel.clicked.connect(self.buy_vowel)
        self.btn_solve.clicked.connect(self.solve_phrase)

        wheel_box.addWidget(self.label_turno)
        wheel_box.addWidget(self.ruota, 5)
        wheel_box.addWidget(self.btn_spin)
        wheel_box.addWidget(self.btn_vowel)
        wheel_box.addWidget(self.btn_solve)
        wheel_box.addWidget(self.btn_cheat)

        self.lista_ui = QListWidget()
        self.lista_ui.setStyleSheet("font: bold 18px 'Courier New'; background: #2f3542; border-radius: 10px; color: white;")

        middle.addLayout(wheel_box, 3)
        middle.addWidget(self.lista_ui, 1)
        layout.addLayout(middle)
        self.setLayout(layout)
        self.update_ui()

    def update_ui(self):
        self.label_cat.setText(f"CATEGORIA: {self.categoria}")
        self.update_tabellone()
        self.update_status()

    def show_solution(self):
        QMessageBox.information(self, "SOLUZIONE SEGRETA", f"La frase da indovinare è:\n\n{self.soluzione}")

    # --- TABELLONE CON A CAPO E GESTIONE APOSTROFI ---
    def update_tabellone(self):
        display = ""
        max_len = 24  # numero massimo di caratteri per riga
        current_len = 0
        i = 0
        while i < len(self.soluzione):
            char = self.soluzione[i]
            if char in [" ", "'"]:
                display += char + " "
                current_len += 2
                i += 1
                continue

            blocco = char
            if i+1 < len(self.soluzione) and self.soluzione[i+1] == "'":
                blocco += "'"
                i += 1

            if char in self.lettere_indovinate:
                display += blocco + " "
            else:
                display += "_ " * len(blocco)
            current_len += len(blocco) + 1
            i += 1

            if current_len >= max_len:
                display += "<br>"
                current_len = 0

        self.label_tabellone.setText(f"<div style='text-align:center'>{display}</div>")

    def update_status(self):
        nome = self.giocatori[self.turno_attuale]
        self.label_turno.setText(f"⭐ TURNO DI: {nome.upper()} (Round {self.round_attuale}/{self.num_round})")
        self.lista_ui.clear()
        for i, (n, p) in enumerate(zip(self.giocatori, self.portafogli)):
            self.lista_ui.addItem(f"{'👉 ' if i == self.turno_attuale else '   '}{n}: {p}€")

    def toggle_buttons(self, state):
        self.btn_spin.setEnabled(state)
        self.btn_vowel.setEnabled(state)
        self.btn_solve.setEnabled(state)
        self.btn_cheat.setEnabled(state)

    # --- RUOTA ---
    def spin_now(self):
        self.toggle_buttons(False)
        self.ruota.speed = random.uniform(25, 45)
        self.ruota.timer.start(16)
        self.play_sound("spin")
        self.ruota.spinning = True

    def handle_wheel_result(self, res):
        if res == "BANCO":
            self.portafogli[self.turno_attuale] = 0
            QMessageBox.critical(self, "BANCAROTTA", f"Bancarotta per {self.giocatori[self.turno_attuale]}!")
            self.next_turn()
        elif res in ["PASSA", "PERDE"]:
            QMessageBox.warning(self, res, "Turno perso!")
            self.next_turn()
        else:
            valore = 500 if res == "JOLLY" else int(res)
            self.ask_letter(valore)

    # --- LETTERE ---
    def ask_letter(self, valore, is_vowel=False):
        tipo = "VOCALE" if is_vowel else "CONSONANTE"
        let, ok = QInputDialog.getText(self, tipo, f"Valore spicchio: {valore}€\nInserisci una {tipo}:")
        if ok and let:
            let = let.upper().strip()
            found = False
            for c in self.soluzione:
                if c.upper() == let and let not in self.lettere_indovinate:
                    found = True
                    break

            if found:
                self.lettere_indovinate.append(let)
                count = sum(1 for c in self.soluzione if c.upper() == let)
                guadagno = valore * count
                self.portafogli[self.turno_attuale] += guadagno
                self.update_tabellone()
                self.update_status()
                self.play_sound("correct")
                QMessageBox.information(self, "OTTIMO", f"La lettera '{let}' è presente {count} volte!\nGuadagno: {guadagno}€")
                self.check_win()
            else:
                self.play_sound("bad")
                QMessageBox.warning(self, "NO", f"Lettera '{let}' non presente. Turno al prossimo giocatore!")
                self.next_turn()
        else:
            if is_vowel:
                self.portafogli[self.turno_attuale] += 500
            self.next_turn()
        self.update_status()

    def buy_vowel(self):
        if self.portafogli[self.turno_attuale] >= 500:
            self.portafogli[self.turno_attuale] -= 500
            self.ask_letter(0, True)
        else:
            QMessageBox.warning(self, "SOLDI", "Credito insufficiente!")

    def solve_phrase(self):
        risp, ok = QInputDialog.getText(self, "RISOLVI", "Digita la soluzione completa:")
        if ok and risp.upper().strip() == self.soluzione:
            for c in self.soluzione:
                if c not in self.lettere_indovinate: self.lettere_indovinate.append(c)
            self.portafogli[self.turno_attuale] += 500
            self.update_tabellone()
            self.update_status()
            self.play_sound("correct")
            self.check_win()
        else:
            self.play_sound("bad")
            QMessageBox.warning(self, "ERRORE", "Soluzione errata! Passi il turno.")
            self.next_turn()

    def next_turn(self):
        self.turno_attuale = (self.turno_attuale + 1) % len(self.giocatori)
        self.update_status()

    # --- VITTORIA E CLASSIFICA ---
    def check_win(self):
        if all(c in self.lettere_indovinate or c in [" ", "'"] for c in self.soluzione):
            self.play_sound("correct")
            QMessageBox.information(self, "VITTORIA", f"BRAVO {self.giocatori[self.turno_attuale]}!\nHai risolto la frase!\nPortafoglio totale: {self.portafogli[self.turno_attuale]}€")
            if self.round_attuale < self.num_round:
                self.round_attuale += 1
                self.nuovo_round()
                self.update_ui()
            else:
                self.show_final_ranking()

    def show_final_ranking(self):
        classifica = sorted(zip(self.giocatori, self.portafogli), key=lambda x: x[1], reverse=True)
        testo = ""
        for i, (nome, soldi) in enumerate(classifica):
            if i == 0:
                testo += f"<b>{i+1}. {nome}: {soldi}€</b>\n"
            else:
                testo += f"{i+1}. {nome}: {soldi}€\n"
        QMessageBox.information(self, "CLASSIFICA FINALE", testo)
        self.close()

# --- AVVIO ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = RuotaGioco()
    game.show()
    sys.exit(app.exec_())
