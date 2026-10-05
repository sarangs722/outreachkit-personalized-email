# OutreachKit: Personalized Email Outreach with Python and the Gmail API

OutreachKit is a Python command-line tool for sending personalized recruiter outreach from your Gmail account.

It reads a CSV of contacts, fills an email template with each recruiter's name and company, attaches your resume, previews every email, and records successful sends so duplicate emails are skipped later.

## Features

- Sends through the Gmail API using your own Google account.
- Personalizes messages with `{name}` and `{company}` placeholders.
- Supports safe previews with `--dry-run`.
- Asks for confirmation before each send by default.
- Keeps a local `sent_log.csv` to avoid duplicate sends.
- Keeps credentials, tokens, contact lists, logs, and resumes out of git.

## Project Files

```text
send_emails.py            Main CLI script
email_template.txt        Editable message template
recruiters.example.csv    Example contact list format
requirements.txt          Python dependencies
.gitignore                Local/private files excluded from git
```

## Prerequisites

- Python 3.10+
- A Gmail account
- A Google Cloud OAuth desktop credential with Gmail API enabled

## Setup

1. Clone the repo and enter the project folder.

   ```bash
   git clone <your-repo-url> outreachkit
   cd outreachkit
   ```

2. Create and activate a virtual environment.

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Configure Google OAuth.

   - Create a Google Cloud project.
   - Enable the Gmail API.
   - Create an OAuth 2.0 Client ID with application type `Desktop app`.
   - Download the OAuth JSON file and save it as `credentials.json` in this project folder.

5. Add your resume.

   Save your resume as `resume.pdf` in the project folder, or pass a custom path with `--resume`.

6. Create your recruiter list.

   ```bash
   copy recruiters.example.csv recruiters.csv
   ```

   On macOS/Linux:

   ```bash
   cp recruiters.example.csv recruiters.csv
   ```

   Edit `recruiters.csv`:

   ```csv
   name,company,email
   Jane Doe,Example Company,jane.doe@example.com
   ```

7. Customize `email_template.txt`.

   The template supports:

   - `{name}`
   - `{company}`

## Usage

Preview generated emails without sending:

```bash
python send_emails.py --dry-run
```

Send with per-email confirmation:

```bash
python send_emails.py
```

Send with a custom subject:

```bash
python send_emails.py --subject "Software Engineer | Backend Platform"
```

Use custom file paths:

```bash
python send_emails.py --recruiters data/recruiters.csv --resume docs/resume.pdf
```

Skip confirmation for a reviewed list:

```bash
python send_emails.py --no-confirm
```

## Safety Notes

- The first real send opens a browser for Google OAuth consent and creates `token.json`.
- Successful sends are appended to `sent_log.csv`.
- Emails already present in `sent_log.csv` with status `sent` are skipped.
- `credentials.json`, `token.json`, `recruiters.csv`, `sent_log.csv`, and `resume.pdf` are intentionally ignored by git.
- Each user supplies their own OAuth credentials and authorizes their own Gmail account. Never share `token.json`.
- Store custom private files in `local/` (also ignored). Files elsewhere with custom names are not automatically excluded; add ignore rules before committing them.
- Before committing, check `git status --short` and use `git check-ignore -v credentials.json token.json` to verify the OAuth files are excluded. Ignore rules do not remove files already tracked by Git.
- If your Gmail token expires or you change scopes, delete `token.json` and run the script again.

## Resume Bullet

Built OutreachKit, a Python Gmail API outreach automation tool that personalizes recruiter emails from CSV data, attaches resumes, previews messages before sending, and tracks sent history to prevent duplicate outreach.
