# Changelog

All notable changes to Sortify will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- None

---

## [1.1.0] - 2025-12-14

### Changed
- AI‑hozzájárulási (consent) szöveg frissítve és pontosítva.
- Hibajelzések szövege átfogalmazva, érthetőbb lett a felhasználók számára.
- Dátumkijelzés egységesítve, minden nézetben azonos formátumban jelenik meg.

### Fixed
- AI által generált kategorizálás stabilitása javítva; teljes újrakategorizáláskor nem fut hibára, a régi címkéket megbízhatóan felülírja.
- Minimum ablakméret beállítása, hogy a felület elemei mindig használhatóan jelenjenek meg.

---

## [1.0.0] - 2025-12-05

### Added
- **Gmail label sync**: kézi és AI címkeváltoztatás automatikusan módosítja a megfelelő Gmail címkéket a leveleken.
- **„Egyéb” címke**: dedikált kategória a nem szakmai / hírlevél jellegű üzenetekhez.
- **AI címkézés Gmail integrációval**: az AI által beállított Sortify-tag azonnal visszaíródik Gmail labelként.
- **Label debugger**: Gmail label ID → név mapping debug log a fejlesztői hibaelhárításhoz.

### Changed
- **Címke pipeline**: a Gmailből érkező címke a golden source, a rules engine nem írhatja felül az érvényes (vezetoseg, tanszek, neptun, moodle, milt-on, hianyos, egyeb) tageket.
- **Fallback logika**: megszűnt az automatikus „Egyéb/Hiányos” ráragasztás, ahol nincs címke; címke nélküli levelek `----` státuszban maradnak.
- **Rules engine**: a „student_mail” szabály már nem kényszerít minden nem egyetemi domainre `hianyos` címkét, csak a tényleg szabály alapján illeszkedőkre.
- **GmailService**: közvetlen label-név → belső tag mappingre állt át (Vezetőség, Tanszék, Neptun, Moodle, Milton, Hiányos, Egyéb).

### Fixed
- **Gmail API 400**: javítva a „Cannot both add and remove the same label” hiba a `users.messages.modify` hívásban (add/remove label ID-k metszete megszüntetve).
- **AI címkézés**: `name 'new_tag' is not defined` kivétel megszüntetve, az AI által beállított `email_data["tag"]` kerül mentésre.
- **Gmail/CSV inkonzisztenciák**: a storage réteg a Gmailből érkező tag-et tekinti elsődlegesnek szinkronizáláskor.

---

## [0.5.1] - 2025-11-27

### Added
- Manuális címkementés CSV-be a részletező panel dropdownjából.
- Kezdőképernyőn helyes kategória-számlálók a már meglévő CSV alapján.

### Fixed
- Címkeszámlálók nem nullázták magukat újraindításkor.
- Szabálymotor nem írta felül többé a kézzel beállított tageket.

---

## [0.4.1] - 2025-11-22

### Added
- AI hozzájárulási (consent) dialógus és beállítás mentése.
- Alap AI összefoglaló mező az emailekhez.

### Changed
- Folyamatjelzők és státuszszövegek finomhangolása a jobb felhasználói visszajelzés érdekében.

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

- **v1.0.0** (2025-12-05) - Gmail label sync & AI integration
- **v0.5.1** (2025-11-27) - Manual tag persistence & startup counters
- **v0.4.1** (2025-11-22) - AI consent & minor improvements
- **v0.3.0** (2025-11-17) - Settings UI & configuration
- **v0.2.0** (2025-11-16) - Attachment verification & UI polish
- **v0.1.0** (2025-11-15) - Initial MVP release


---