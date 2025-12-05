# Sortify - Email Management Tool

Automated email categorization and management system with AI-powered summaries and full Gmail label integration.

## Features

- Gmail API integration (fetch + **bidirectional label sync**)  
- Automatic email categorization with configurable rules  
- AI-powered email summaries és AI-alapú címkézés  
- Attachment verification and basic security checks  
- Hungarian-localized UI  
- Offline storage (CSV-based) + test mode  
- HTML email rendering a részletező panelben  

## Tech Stack

- Python 3.10+  
- Tkinter (GUI)  
- Gmail API (labels + modify scope)  
- Google Gemini AI / Perplexity AI  
- tkhtmlview (HTML rendering)  

## Installation

### Prerequisites

- Python 3.10 or higher  
- Gmail API project + OAuth credentials  
- AI API key (Gemini vagy Perplexity)  

### Setup

1. Clone repository  

   `git clone https://github.com/Kandi81/Szoftverfejleszt-si-projekt-2025.git`  
   `cd Szoftverfejleszt-si-projekt-2025`

2. Create virtual environment  

   `python -m venv .venv`  

   Windows:  
   `.venv\Scripts\activate`  

   Linux/Mac:  
   `source .venv/bin/activate`

3. Install dependencies  

   `pip install -r requirements.txt`

4. Configure API credentials  

   Hozd létre a `resource/` könyvtárban:

   - `credentials.json` – Gmail OAuth kliens  
   - `perp_api_key.txt` – Perplexity API key (jelenlegi default)  
   - (opcionális) `gemini_api_key.txt` – ha Geminit is használnál  

   Az első futáskor a Gmail OAuth böngészőben engedélyt kér, és létrejön a `resource/token.json`.

5. Configure rules  

   A kategorizálási szabályokat a `config/settings.ini` fájlban tudod testre szabni  
   (`rules.leadership`, `rules.department`, `rules.neptun`, `rules.moodle`, `rules.milton` stb.).

## Usage

### Run application

`python main.py`

### First run

1. Kattints a **„Bejelentkezés”** gombra (Gmail OAuth).  
2. Kattints a **„Letöltés / Frissítés”** gombra az emailek betöltéséhez.  
3. A levelek automatikusan kategorizálódnak:
   - Vezetoseg, Tanszek, Neptun, Moodle, Milt-On, Hianyos, Egyeb, vagy `----`.  
4. Válassz ki egy levelet:
   - részletek, HTML‑nézet és csatolmánylista a jobb oldali panelen,  
   - AI összefoglaló és AI címkézés a részletező panel gombjaival.  

### Gmail label sync (v1.0)

- A Sortify belső címkék a következő Gmail label-ekhez kötődnek:  
  - `vezetoseg` ↔ **Vezetőség**  
  - `tanszek`   ↔ **Tanszék**  
  - `neptun`    ↔ **Neptun**  
  - `moodle`    ↔ **Moodle**  
  - `milt-on`   ↔ **Milton**  
  - `hianyos`   ↔ **Hiányos**  
  - `egyeb`     ↔ **Egyéb**  
- Ha Gmailben módosítod ezeket a label-eket, a következő letöltéskor a Sortify tagek is frissülnek.  
- Ha a Sortify UI-ban a dropdownnal vagy AI‑val módosítod a taget, a program:
  - frissíti a CSV-t,  
  - és ugyanarra a levelezési címkére állítja a Gmail label-t is.  

### Test mode

Tedd a `data/` könyvtárba az `emails_mod.csv` fájlt. Ilyenkor:

- az alkalmazás nem hívja a Gmail API-t,  
- minden művelet a teszt CSV-n történik (biztonságos demó / fejlesztési mód).  

## Project structure

.
- `main.py` – Application entry point  
- `sortifyui.py` – Main UI  
- `settings_ui.py` – Settings window  

`utils/`  
- `date_utils.py`  
- `html_utils.py`  
- `path_utils.py`  

`models/`  
- `app_state.py`  
- `email_model.py`  

`services/`  
- `storage_service.py` – CSV + test mode  
- `gmail_service.py` – Gmail API + label sync  
- `gmailcimke.py` – helper a label logikához  
- `gemini_service.py`  
- `perplexity_service.py`  
- `ai_service_factory.py`  
- `verification_service.py`  

`business/`  
- `rules_engine.py` – Neptun/Moodle/Milton/vezetoseg/tanszek szabályok  

`controllers/`  
- `email_controller.py` – Gmail + storage + UI orchestráció  
- `ai_controller.py`  
- `auth_controller.py`  

`config/`  
- `settings.ini`  

`data/`  
- `emails.csv`  
- `bodies/` – HTML/body cache  

`resource/`  
- `credentials.json`  
- `token.json`  
- `gemini_api_key.txt`  
- `perp_api_key.txt`  

## Configuration

### Categorization rules

`config/settings.ini` példa:

`[rules.leadership]`  
`emails = boss@uni-milton.hu,dean@uni-milton.hu`  

`[rules.department]`  
`emails = honfi@uni-milton.hu,cser.jozsef@uni-milton.hu`  

`[rules.neptun]`  
`emails = neptun@uni-milton.hu`  
`domains = neptun`  

`[rules.moodle]`  
`emails = moodle@uni-milton.hu`  
`domains = moodle`  

`[rules.milton]`  
`emails = noreply@milt-on.hu`  
`domains = milt-on`  

A rules engine **nem írja felül** azokat a leveleket, amik már érvényes taget kaptak (Gmail/AI/kézi).

### AI provider

A `main.py` a `AIController` példányosításakor választ providert (`perplexity` az alapértelmezett).  
A Perplexity API kulcsot a `resource/perp_api_key.txt` fájlba kell tenni, egy sor – egy key.

## Advanced features

### AI summary & AI labeling

- Egy levél kijelölése után a részletező panelen:
  - **„AI összefoglaló”** gomb: rövid leírás az email tartalmáról.  
  - **„AI címkézés”** gomb: AI javaslat a kategóriára, amit a rendszer:
    - beír a `tag` mezőbe,  
    - elment a CSV-be,  
    - és szinkronizál a Gmail label-lel.  

### Attachment verification

- `Csatolmányok ellenőrzése` gomb:
  - gyanús kiterjesztések,  
  - dupla kiterjesztések,  
  - MIME type vs. kiterjesztés eltérés.  

### Filtering & shortcuts

- Tag gombok (Vezetőség, Tanszék, Neptun, Moodle, Milt-On, Hiányos, Egyéb).  
- Csatolmány-szűrő gomb (csak mellékletes levelek).  
- Ctrl+R – frissítés Gmailből.  
- Escape – szűrők törlése.  

## Version history

- **v1.0.0** (2025-12-05) – Gmail label sync & AI integration  
- **v0.5.1** – Manual tag persistence & startup counters  
- **v0.4.1** – AI consent & cleanup  
- **v0.3.0** – Settings UI & configuration  
- **v0.2.0** – Attachment verification & UI polish  
- **v0.1.0** – Initial MVP release  

## Contributing / License

Ez egy egyetemi projekt (Budapesti gazdasági informatika / üzleti informatika kontextusban).  
Pull request jöhet, de production supportot ne várj.  

License: oktatási / egyetemi felhasználás (nincs formális OSS licenc megadva – ha kell, adj hozzá MIT-et külön fájlban).