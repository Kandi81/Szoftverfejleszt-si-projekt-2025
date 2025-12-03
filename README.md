***

## 🏗️ Project Structure

<details>
<summary><b>Click to expand full structure</b></summary>

<pre>
sortify/
├── main.py                    # Application entry point
├── sortifyui.py               # Main UI (refactored)
├── settings_ui.py             # Settings window
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── date_utils.py          # Date formatting
│   ├── html_utils.py          # HTML cleaning
│   └── path_utils.py          # Resource paths
│
├── models/                    # Data models
│   ├── __init__.py
│   ├── app_state.py           # Application state singleton
│   └── email_model.py         # Email data structure
│
├── services/                  # External services
│   ├── __init__.py
│   ├── storage_service.py     # CSV storage
│   ├── gmail_service.py       # Gmail API client
│   ├── gemini_service.py      # Google Gemini AI
│   ├── perplexity_service.py  # Perplexity AI
│   ├── ai_service_factory.py  # AI provider factory
│   └── verification_service.py # Attachment verification
│
├── business/                  # Business logic
│   ├── __init__.py
│   └── rules_engine.py        # Email categorization rules
│
├── controllers/               # UI controllers
│   ├── __init__.py
│   ├── email_controller.py    # Email operations
│   ├── ai_controller.py       # AI operations
│   └── auth_controller.py     # Authentication
│
├── config/                    # Configuration
│   └── settings.ini           # Rules and settings
│
├── data/                      # Data storage
│   └── emails.csv             # Email database
│
└── resource/                  # Resources
    ├── credentials.json       # Gmail OAuth credentials
    ├── token.json             # Auth token (generated)
    ├── gemini_api_key.txt     # Gemini API key
    └── perp_api_key.txt       # Perplexity API key
</pre>

</details>

***

## 🏛️ Architecture

Sortify uses a **5-layer modular architecture** for maintainability and testability.

### Layers

**1. Utils Layer** - Pure utility functions (no dependencies)  
**2. Models Layer** - Data structures and application state  
**3. Services Layer** - External API integrations (Gmail, AI, Storage)  
**4. Business Layer** - Business logic (rules engine, categorization)  
**5. Controllers Layer** - Orchestration between UI and services

### Architecture Flow

UI Layer (sortifyui.py)
↓ uses
Controllers Layer (email, ai, auth)
↓ uses
Services + Business Layer (gmail, storage, AI, rules)
↓ uses
Models + Utils Layer (app_state, date/html utils)

text

### Key Principles

- ✅ **Dependency Injection** - Controllers injected into UI via `main.py`
- ✅ **Single Responsibility** - Each module has one clear purpose
- ✅ **Separation of Concerns** - UI, business logic, and services separated
- ✅ **Testability** - Pure functions and clear interfaces
- ✅ **Maintainability** - Easy to understand and modify

***

## 📝 Migration Notes (v0.3.0 → v0.4.0)

**v0.4.0** introduced a complete modular architecture refactor.

### Deprecated Modules (Removed)

Old monolithic modules were replaced with modular equivalents:

| Old Module | New Module | Location |
|------------|------------|----------|
| `gmailclient.py` | `GmailService` | `services/gmail_service.py` |
| `email_storage.py` | `StorageService` | `services/storage_service.py` |
| `rules.py` | `apply_rules` | `business/rules_engine.py` |
| `perplexity_client.py` | `PerplexityService` | `services/perplexity_service.py` |
| `geminiclient.py` | `GeminiService` | `services/gemini_service.py` |
| `attachment_verifier.py` | `verify_attachments` | `services/verification_service.py` |

### Migration Guide

If you have custom code importing old modules, update as follows:

```python
# OLD (no longer works)
import gmailclient
from email_storage import EmailStorage
from rules import apply_rules

# NEW (v0.4.0+)
from services import GmailService, StorageService
from business import apply_rules
Entry Point Changed
Old: Run python sortifyui.py directly

### Entry Point Changed

- **Old:** Run `python sortifyui.py` directly
- **New:** Run `python main.py` (recommended)

The `main.py` entry point initializes services and injects controllers into the UI.

---