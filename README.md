# Sortify - Email Management Tool

Automated email categorization and management system with AI-powered summaries.

## Features

- Gmail API integration for email fetching
- Automatic email categorization with customizable rules
- AI-powered email summaries (Gemini/Perplexity)
- Attachment verification and security scanning
- Hungarian-localized interface
- Offline storage (CSV-based)
- Test mode for development
- HTML email rendering

## Tech Stack

- Python 3.10+
- Tkinter (GUI)
- Gmail API
- Google Gemini AI / Perplexity AI
- tkhtmlview (HTML rendering)

## Installation

### Prerequisites

- Python 3.10 or higher
- Gmail API credentials
- AI API key (Gemini or Perplexity)

### Setup

1. Clone repository

git clone https://github.com/yourusername/sortify.git
cd sortify


2. Create virtual environment

python -m venv .venv
.venv\Scripts\activate # Windows
source .venv/bin/activate # Linux/Mac


3. Install dependencies

pip install -r requirements.txt


4. Configure API credentials

Create the following files in `resource/` directory:

- `credentials.json` - Gmail OAuth credentials
- `gemini_api_key.txt` - Gemini API key OR
- `perp_api_key.txt` - Perplexity API key

5. Configure rules

Edit `config/settings.ini` to customize email categorization rules.

## Usage

### Run Application

python main.py


### First Run

1. Click "Bejelentkezés" (Login) to authenticate with Gmail
2. Click "Letöltés / Frissítés" (Download/Refresh) to fetch emails
3. Emails are automatically categorized based on rules
4. Select an email to view details and AI summary

### Test Mode

Place `emails_mod.csv` in `data/` directory to enable test mode. The application will use test data instead of fetching from Gmail.

## Project Structure

```
sortify/
├── main.py                      # Application entry point
├── sortifyui.py                 # Main UI
├── settings_ui.py               # Settings window
├── gmailcimke.py                # Gmail label operations (future)
│
├── utils/                       # Utility functions
│   ├── __init__.py
│   ├── date_utils.py
│   ├── html_utils.py
│   └── path_utils.py
│
├── models/                      # Data models
│   ├── __init__.py
│   ├── app_state.py
│   └── email_model.py
│
├── services/                    # External services
│   ├── __init__.py
│   ├── storage_service.py
│   ├── gmail_service.py
│   ├── gemini_service.py
│   ├── perplexity_service.py
│   ├── ai_service_factory.py
│   └── verification_service.py
│
├── business/                    # Business logic
│   ├── __init__.py
│   └── rules_engine.py
│
├── controllers/                 # UI controllers
│   ├── __init__.py
│   ├── email_controller.py
│   ├── ai_controller.py
│   └── auth_controller.py
│
├── config/                      # Configuration
│   └── settings.ini
│
├── data/                        # Data storage
│   └── emails.csv
│
└── resource/                    # API keys and credentials
    ├── credentials.json
    ├── token.json
    ├── gemini_api_key.txt
    └── perp_api_key.txt
```

## Architecture

Sortify uses a 5-layer modular architecture for maintainability and testability.

### Layers

**1. Utils Layer** - Pure utility functions (date formatting, HTML cleaning)

**2. Models Layer** - Data structures and application state management

**3. Services Layer** - External API integrations (Gmail, AI providers, Storage)

**4. Business Layer** - Business logic (email categorization rules)

**5. Controllers Layer** - Orchestration between UI and services

### Architecture Flow

UI Layer (sortifyui.py)
↓
Controllers Layer (email, ai, auth)
↓
Services + Business Layer
↓
Models + Utils Layer


### Key Principles

- Dependency Injection - Controllers injected via main.py
- Single Responsibility - One purpose per module
- Separation of Concerns - UI, business logic, and services separated
- Testability - Pure functions and clear interfaces
- Maintainability - Easy to understand and modify

## Configuration

### Email Categorization Rules

Edit `config/settings.ini` to customize categorization:

[rules.leadership]
emails = boss@university.hu,dean@university.hu

[rules.department]
emails = colleague1@university.hu,colleague2@university.hu

[rules.neptun]
emails = neptun@university.hu

[rules.moodle]
emails = moodle@university.hu

[rules.milton]
emails = milton@university.hu


### AI Provider

Set AI provider in code or via environment:

In main.py
ai_controller = AIController(storage_service, ai_provider="perplexity")

or ai_provider="gemini"


## Features in Detail

### Email Categorization

Emails are automatically categorized into:

- Vezetoseg (Leadership)
- Tanszek (Department)
- Neptun (Student system)
- Moodle (Learning platform)
- Milt-On (University platform)
- Hianyos (Incomplete/Missing info)

### AI Summary

Generate AI-powered summaries for individual emails:

1. Select an email
2. Click the sparkle button in details panel
3. AI summary appears in yellow box

### Attachment Verification

Verify email attachments for security:

1. Select an email with attachments
2. Click "Csatolmányok ellenőrzése" button
3. View verification results

Checks for:
- Suspicious file extensions (.exe, .scr, .bat, etc.)
- Double extensions (.pdf.exe)
- Mismatched MIME types

### Filtering

Filter emails by:

- Tag/Category (click category buttons)
- Attachments (click attachment count button)
- Clear filters with Escape key

### Keyboard Shortcuts

- Ctrl+R - Refresh emails from Gmail
- Escape - Clear active filters

## Version History

### v0.4.1 - Cleanup (Current)

- Removed backward compatibility
- Removed obsolete prototype files
- Enforced main.py entry point
- Simplified documentation

### v0.4.0 - Modular Architecture

Complete refactoring to 5-layer modular architecture.

- 23 new modular files organized in 5 layers
- main.py entry point with dependency injection
- Controllers pattern for UI orchestration
- 33% code reduction in UI layer
- Better separation of concerns

### v0.3.0 - Feature Complete

- Added AI summary (Perplexity/Gemini)
- Added attachment verification
- Added email categorization rules
- HTML email rendering
- Details panel

### v0.2.0 - MVP

- Basic email fetching from Gmail
- CSV storage
- Simple categorization
- Tkinter UI

## Development

### Running Tests

Test mode with sample data:

Place emails_mod.csv in data/ directory
python main.py


### Adding New Categorization Rules

1. Edit `config/settings.ini`
2. Add new section: `[rules.your_category]`
3. Add emails: `emails = email1@domain.com,email2@domain.com`
4. Restart application

### Extending Services

Add new service in `services/` directory:

services/your_service.py
class YourService:
def init(self):
pass

text
def your_method(self):
    pass

Import in `services/__init__.py`:

from .your_service import YourService

## Troubleshooting

### Gmail Authentication Failed

- Check `resource/credentials.json` exists
- Delete `resource/token.json` and re-authenticate
- Verify Gmail API is enabled in Google Cloud Console

### AI Summary Not Working

- Check API key file exists (gemini_api_key.txt or perp_api_key.txt)
- Verify API key is valid
- Check internet connection

### Emails Not Loading

- Verify Gmail authentication
- Check internet connection
- Review console output for errors

## Contributing

This is a university project. Contributions are welcome via pull requests.

## License

Educational project for Hungarian University of Economics.

## Authors

University student project - Business Economics program.

## Acknowledgments

- Gmail API documentation
- Google Gemini AI
- Perplexity AI
- tkhtmlview library