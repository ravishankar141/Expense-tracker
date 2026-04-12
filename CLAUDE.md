# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the Flask application
python app.py

# Run tests
pytest
```

## Architecture

**Spendly** - A Flask-based expense tracker web application.

### Stack
- **Backend**: Flask 3.1.x with Werkzeug
- **Database**: SQLite (to be implemented in `database/db.py`)
- **Frontend**: Jinja2 templates + vanilla JS
- **Testing**: pytest with pytest-flask

### Structure
```
├── app.py              # All routes - single file, no blueprint
├── database/
│   └── db.py           # SQLite helpers: get_db(), init_db(), send_db()
├── templates/          # Jinja2 HTML templates
|    └──base.html       # all templates must extend this
|    └──*.html          # one template per page
|    
├── static/             # CSS, JS, assets
|   |
|   ├──css/
|   |   └──style.css    # global styles  
|   |   └──landing.css  # Landing-page-only styles
|   └──js/
|       └──main.js    # vanilla js only
|
└── venv/               # Python virtual environment
└──requirements.txt

```
**where things belang**
- New reutes 'app.py' only, no blumprints
- De logic database/db.py only, never inline in routes
- New pages - new '.html' file extending 'base.html'
- Page-specific styles -> new.css file, not inline '<style>' tags

--- 
# Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with 'url_for()' for every internal link never -> hardcode URLS

Route functions: one responsibility only - fetch data, render template, done

- DB queries: always use parameterized queries ('?'placeholders) - never f-strings in SQL

- Error handling: use 'abort()' for HTTP errors, not bare " return error string"

## Tech constraints

- **Flask only**no FastAPI, no Django, no other web frameworks
- **SQLite only**no PostgreSQL, no SQLAlchemy ORM, no external DB
- **Vanilla JS only** no React, no jQuery, no npm packages
- **No new pip packages** work within 'requirements.txt as-is unless
explicitly told otherwise
- Python 3.10+ assumed - f-strings and match statements are fine

---
## Commands
'''bash
# Setup
python-m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Run dev server (port 5000)
python app.py

# run all tests
pytest

# Run a specific test file
pytest test/test_foo.py

# Run a specific test by name
pytest -k " test_name"

# Run tests with output visible
pytest -s
'''

---
## Implemented vs stub routes

| Route | Status |
|---|---|
|   'GET/' Implemented - renders 'landing.html' | 
    'GET/register' | Implemented -renders 'register.html' |
    'GET/login' | Implemented - renders 'login.html' |
    'GET/logout' | Stub-Step 3 |
    'GET/profile' | Stub-Step 4
    'GET/expenses/add' |Stub-Step 7|
    'GET/expenses/<id>/edit' |Stub-Step 8|
    'GET/expenses/<id>/delete' |Stub - Step 9|


** Do not inplement a stub route unless the active task explicitly targe that stept.**

---
## Warnings and things to avoid

***Never use raw string returns for stub routes** once a step is implemented always render a template
- **Never hardcode URLs** in templates always use 'url_for()`
- **Never put DB logic in route functions** it belongs in 'database/db.py'
- **Never install new packages** mid-feature without flagging it keep requirements.txt in sync
- **Never use JS frameworks** the frontend is intentionally vanilla

**'database/db.py' is implemented** - contains get_db(), init_db(), seed_db(), close_db()

**FK enforcement is manual** SQLite foreign keys are off by default;
'get_db()' must run 'PRAGMA foreign_keys ON' on every connection 
- The app runs on sport 5001, not the Flask default 5000 - don't change this