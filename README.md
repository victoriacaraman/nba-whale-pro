# 🐋 NBA Whale Pro

App Streamlit per analisi statistiche NBA, value bet e bankroll tracking.
Utilizzabile da desktop e da smartphone come **Progressive Web App (PWA)**.

---

## 🚀 Avvio rapido (locale)

```bash
pip install -r requirements.txt
$env:API_SPORTS_KEY="la_tua_chiave_apisports"
$env:ODDS_API_KEY="la_tua_chiave_theoddsapi"
streamlit run nba_whale.py
```

---

## ☁️ Deploy gratuito su Streamlit Community Cloud

1. Vai su https://github.com e crea un nuovo repository (es. `nba-whale-pro`).
2. Carica nel repo:
   - `nba_whale.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `README.md`
   - `icon-192.png`
   - `icon-512.png`
3. Vai su https://share.streamlit.io/ e clicca **New app**.
4. Collega GitHub, seleziona il repo, branch `main`, file principale `nba_whale.py`.
5. In **Advanced settings → Secrets** incolla:
   ```toml
   API_SPORTS_KEY = "la_tua_chiave_apisports"
   ODDS_API_KEY   = "d0610cb7c6f61f3424a82d4d2e56c4e3"
   ```
6. Clicca **Deploy**. Otterrai un URL tipo `https://nba-whale-pro.streamlit.app`.

---

## 📱 Installazione come App su Smartphone (PWA)

### Android (Chrome)
1. Apri l’URL Streamlit Cloud nel browser.
2. Menu (⋮) → **Aggiungi alla schermata Home**.
3. Conferma il nome (es. `NBA Whale`).
4. Apparirà un’icona sull’home come app nativa.

### iPhone / iPad (Safari)
1. Apri l’URL nel Safari.
2. Tocca il bottone Condividi.
3. **Aggiungi a Home**.
4. Tocca Aggiungi.

L’app partirà in modalità full-screen, senza barra del browser.

---

## 🔑 Variabili d’ambiente

| Variabile        | Descrizione                                  |
|------------------|----------------------------------------------|
| `API_SPORTS_KEY` | API key di api-sports.io (NBA stats)         |
| `ODDS_API_KEY`   | API key di the-odds-api.com (player props)   |

---

## ⚠️ Disclaimer

Strumento di analisi statistica a scopo informativo. Non è consulenza finanziaria.
Il gioco d’azzardo può causare dipendenza.
