# Atlassian Log Analyzer

Local desktop analyzer for Atlassian product logs on macOS Intel.

## Scope

- macOS Intel / x86_64
- Python 3.11+
- PySide6 desktop UI
- CLI support
- Fully local execution
- No backend or web server
- PyInstaller `.app` packaging
- Optional `.dmg` distribution after build

## Supported Inputs

- Files selected from Finder
- Folders
- Support zip files
- `.log`, `.txt`, `.out`, `.gz`, `.zip`

## MVP Features

- Auto-detects product: Bitbucket, Jira, Confluence, Bamboo, Crowd, Unknown
- Finds `ERROR` and `WARN` log events
- Groups Java stack traces into a single event
- Categorizes issues with YAML rules
- Filterable desktop table by category, level, and keyword
- Exports HTML, Markdown, JSON, and CSV reports

## Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Desktop App

```bash
python -m app.main
```

## Run CLI

Analyze files, folders, or zip archives:

```bash
python -m app.cli /path/to/atlassian.log /path/to/support.zip --format markdown --output report.md
```

Supported output formats:

```bash
json
csv
markdown
html
```

## Build macOS Intel .app

Run this on an Intel Mac, or from an environment capable of building x86_64 macOS binaries.

```bash
pyinstaller --name "Atlassian Log Analyzer" --windowed --target-arch x86_64 --icon assets/app_icon.icns app/main.py
```

## Verify Built App Architecture

```bash
file "dist/Atlassian Log Analyzer.app/Contents/MacOS/Atlassian Log Analyzer"
```

Expected output should include `x86_64`.

## Optional DMG

After building the `.app`, you can package it with a DMG tool such as `create-dmg`:

```bash
create-dmg "dist/Atlassian Log Analyzer.app"
```

## Project Layout

```text
app/
  main.py
  cli.py
  core/
    analyzer.py
    archive_reader.py
    categorizer.py
    models.py
    parser.py
    product_detector.py
    report_generator.py
  ui/
    main_window.py
rules/
  categories.yml
assets/
  README.md
```

## Notes

`assets/app_icon.icns` is referenced by the build command. Add a real macOS icon file before producing a distributable build.
