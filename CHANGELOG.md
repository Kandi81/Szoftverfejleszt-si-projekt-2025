# Changelog

All notable changes to Sortify will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Student email pre-triage with heuristics
- Gemini LLM integration for intelligent email analysis
- Gmail label auto-application based on categories
- Export/report generation features

---

## [0.3.0] - 2025-11-17

### Added
- **Settings UI**: Graphical settings editor with tabbed interface (Rules & General)
- **INI Configuration**: Rules loaded from `config/settings.ini` with fallback to defaults
- **Settings Dialog**: Add/edit/remove emails with validation, domain configuration
- **Working Categorization**: "Kategorizálás" button now fully functional
- **Dynamic Test Mode**: Automatic detection of `data/emails_mod.csv` before operations
- CSV delimiter flexibility: Support for both semicolon (`;`) and pipe (`|`) separators
- Settings button with gear icon (⚙) in toolbar
- `save_emails()` method in `email_storage.py`
- Version info file (`version_info.txt`) for Windows executable metadata

### Fixed
- Variable shadowing warnings in `rules.py`
- Settings button overlap with filter status label
- Test mode detection not working after file creation
- CSV parsing errors with misaligned columns
- "Mind" checkbox disabled state in test mode
- Attachment verification button not disabling when filtering by tags

### Changed
- Rules now loaded from INI file instead of hardcoded values
- Test mode checking happens dynamically before each operation
- Improved error handling with full tracebacks in CSV parsing
- Updated PyInstaller spec to include `config/` folder
- Application title updated to "Sortify v0.3.0"

### Technical
- New file: `settings_ui.py` - Complete settings dialog implementation
- New file: `config/settings.ini` - User-editable configuration
- Modified: `sortifyui.py` - Added settings integration and categorization logic
- Modified: `email_storage.py` - Enhanced test mode detection and save functionality
- Modified: `rules.py` - INI-based rule loading and code quality improvements

---

## [0.2.0] - 2025-11-16

### Added
- Sortable TreeView columns with ascending/descending indicators (▲/▼)
- Filter status label showing active filters
- Keyboard shortcuts: Ctrl+R (refresh), Escape (clear filters)
- Real-time progress bar with pastel green color
- Attachment verification system (`attachment_verifier.py`)
- "Csatolmányok ellenőrzése" button with detailed warning dialogs
- MIME type extraction and comparison with file extensions
- Test data mode support (`emails_mod.csv`)
- Automatic categorization rules with priority system
- CSV-based email storage with sync functionality

### Fixed
- Progress bar positioning and visibility
- TreeView column sorting stability
- Filter button state management
- Date formatting in Hungarian style (YYYY.MM.DD HH:MM)

### Changed
- Improved CSV schema with `mime_types` field
- Enhanced `gmailclient.py` with `_parse_date_hungarian()` method
- Better recursive MIME type extraction from nested parts

---

## [0.1.0] - 2025-11-15

### Added
- Initial release
- Gmail API integration
- Basic email fetching and display
- TreeView with columns: Sender, Subject, Tag, Attachments, Date
- Login/Logout functionality
- Tag filter buttons (Vezetőség, Tanszék, Neptun, Moodle, Milt-On, Hiányos)
- Select-all checkbox
- Basic UI framework with tkinter

### Known Issues
- Categorization button placeholder (non-functional)
- No settings UI
- Rules hardcoded in source

---

## Version History

- **v0.3.0** (2025-11-17) - Settings UI & Configuration Management - 80% complete
- **v0.2.0** (2025-11-16) - Attachment Verification & UI Polish - 70% complete
- **v0.1.0** (2025-11-15) - Initial MVP Release - 50% complete

---