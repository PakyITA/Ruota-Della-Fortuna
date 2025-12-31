# 🎡 Ruota Della Fortuna - Game Edition v1.0.1

Benvenuti in **Ruota Della Fortuna**, un gioco interattivo ispirato al celebre show televisivo, sviluppato in Python utilizzando la libreria grafica **PyQt5**.

---

## 🚀 Caratteristiche Principali
* **Multigiocatore Locale:** Supporta fino a 3 giocatori con gestione dei nomi personalizzata.
* **Sistema di Aggiornamento:** Controllo automatico della versione tramite GitHub API all'avvio.
* **Database Dinamico:** Gestione delle frasi (Aggiunta/Rimozione/Modifica) direttamente dall'interfaccia di gioco.
* **Esperienza Multimediale:** Include sigla originale, musica di sottofondo ed effetti sonori.
* **Gestione Jolly:** Sistema di bonus 🍀 per proteggere il portafoglio dalla "Bancarotta".

---

## 📦 Come Scaricare e Giocare (Utenti Windows)

Segui questi semplici passaggi per avviare il gioco sul tuo PC senza installare nulla:

1.  **Vai alla sezione Release:** Clicca su [Releases](https://github.com/PakyITA/Ruota-Della-Fortuna/releases) nella colonna a destra di questa pagina.
2.  **Scarica l'eseguibile:** Cerca l'ultimo aggiornamento (v1.0.1) e scarica il file chiamato `GiraLaRuota_v1.0.1.exe`.
3.  **Avvio:** Fai doppio clic sul file scaricato.
    * *Nota:* Se Windows mostra l'avviso "PC protetto da Windows", clicca su **Ulteriori informazioni** e poi su **Esegui comunque**.
4.  **Divertiti:** Il gioco creerà automaticamente un file `frasi_gira_la_ruota.json` nella tua cartella *Documenti* per salvare le tue frasi personalizzate.

---

## 🛠 Fasi Successive e Automazione

Questo repository utilizza le **GitHub Actions** per gestire il ciclo di vita del software in modo professionale:

### 1. Sviluppo e Push
Ogni volta che il codice viene aggiornato e caricato sul ramo `main`, il repository viene aggiornato.

### 2. Creazione del Tag di Versione
Quando viene rilasciata una nuova versione (es. `v1.0.2`), il sistema rileva automaticamente il nuovo "Tag".

### 3. Build Automatica (CI/CD)
GitHub avvia una macchina virtuale Windows temporanea che:
* Installa Python e le dipendenze (`PyQt5`, `requests`).
* Compila il codice sorgente usando `PyInstaller`.
* Allega l'eseguibile creato direttamente nella pagina delle Release.

### 4. Notifica Update
Grazie alla funzione `check_for_updates()`, tutti gli utenti che hanno una versione precedente riceveranno un avviso pop-up all'interno del gioco che li invita a scaricare la nuova versione da GitHub.

---

## ⌨️ Comandi Rapidi
* **SPAZIO**: Gira la Ruota.
* **ESC**: Chiudi il gioco.
* **ENTER**: Salta l'introduzione.

---

## 👤 Autore
* **PakyITA** - [Profilo GitHub](https://github.com/PakyITA)

---
*Progetto creato a scopo didattico e ricreativo.*
