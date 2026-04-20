# Spec: Login and Logout

## Overview

Implement user authentication so registered users can log in and out of Spendly. This step transforms the existing stub `GET /login` route into a fully functional POST handler that validates credentials against the database, sets a session cookie, and redirects to a protected page. The logout route clears the session and redirects to the landing page. This enables authenticated access to user-specific features like profile management and expense tracking.

## Depends on

- Step 01 - Database setup (`users` table, `get_db()`)
- Step 02 - Registration (users exist in database with hashed passwords)

## Routes

- `GET + POST /login` - public
  - GET: render login form
  - POST: validate credentials, set session, redirect to `/profile`
  - Handled by one `@app.route('/login', methods=['GET', 'POST'])`

- `GET /logout` - public (but requires active session to be meaningful)
  - Clears session cookie
  - Flashes "Logged out successfully" message
  - Redirects to landing page `/`
  - Note: GET /logout is intentional for simplicity at this stage

## Database changes

No new tables or columns. The existing `users` table covers all requirements.

A new DB helper must be added to `database/db.py`:
- `get_user_by_email(email)` - returns user record (including password_hash) by email
  - Returns `None` if user not found
  - Used by login route to validate credentials

## Templates

**Modify**: `templates/login.html`
- Change the form `action` to `url_for('login')` with `method="post"`
- Add `name="email"` and `name="password"` attributes to inputs
- Add flash message display block for error/success messages
- Keep all existing visual design

**Modify**: `templates/base.html`
- Add conditional navigation links based on session state:
  - Use `{% if session.get('user_id') %}` to check if logged in
  - If logged in: show "Profile", "Logout" links and display `{{ session.get('user_name') }}`
  - If not logged in: show "Login", "Register" links

**Modify**: `app.py` - profile route
- Change `profile()` route to render template instead of returning plain string

**Create**: `templates/profile.html`
- Stub profile page extending `base.html`
- Display welcome message with user name from session

## Files to change

- `app.py` - upgrade `login()` to handle POST; implement `logout()`; update profile route
- `database/db.py` - add `get_user_by_email(email)` helper
- `templates/login.html` - wire up form action/method and flash message display
- `templates/base.html` - add session-aware navigation

## Files to create

- `templates/profile.html` - stub profile page extending base.html

## New dependencies

No new dependencies - use Flask's built-in `session` for authentication state and `werkzeug.security.check_password_hash` for password verification.

## Rules for implementation

- No SQLAlchemy or ORMs - use raw SQLite queries
- Parameterised queries only - never use f-strings in SQL
- Password verification uses `werkzeug.security.check_password_hash`
- Session management uses Flask's built-in `session` (requires `app.secret_key` already set)
- Session must store at minimum: `user_id` and `user_name`
- On GET: return `render_template('login.html')`
- Server-side validation:
  1. Both email and password are required (non-empty) - use `if not email.strip():`
  2. User exists with provided email
  3. Password matches stored hash
- Use same error message for both invalid email and invalid password intentionally — prevents email enumeration
- On any validation failure, re-render form with `flash('...', 'error')` - do not redirect
- On success, `flash('...', 'success')` and `redirect` to `url_for('profile')`
- Logout must clear entire session with `session.clear()`
- Security: `# TODO: session.regenerate() before setting user data (Step 0X)`
- All templates extend `base.html`
- Use CSS variables - never hardcode hex values
- Use `url_for()` for every internal link - never hardcode URLs

## Definition of done

- [ ] `GET /login` renders the login form without errors
- [ ] Submitting valid credentials (email + password) logs user in and redirects to `/profile`
  - Profile page renders template showing user's name and logout link
- [ ] After login, session contains `user_id` and `user_name`
- [ ] Submitting non-existent email shows "Invalid credentials" error, no session created
- [ ] Submitting wrong password shows "Invalid credentials" error, no session created
- [ ] Submitting with any empty field shows validation error
- [ ] Navigation in `base.html` shows user name and logout link when logged in
- [ ] Navigation shows login/register links when not logged in
- [ ] `GET /logout` clears session and redirects to `/`
- [ ] After logout, attempting to access `/profile` (future step) requires re-login
- [ ] Demo user from seed data (demo@spendly.com / demo123) can log in successfully
