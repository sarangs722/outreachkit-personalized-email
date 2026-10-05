import argparse
import base64
import csv
import mimetypes
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = Path(__file__).resolve().parent

SUBJECT = "Software Engineer | Backend / Platform / AI | 3 YOE"


def authenticate(credentials_file, token_file):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google API dependencies are missing. Run: pip install -r requirements.txt"
        ) from exc

    creds = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_file.exists():
                raise FileNotFoundError(
                    f"{credentials_file} not found. Create a Google OAuth Desktop "
                    "credential and save it at that path."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def load_recruiters(csv_file):
    if not csv_file.exists():
        raise FileNotFoundError(
            f"{csv_file} not found. Copy recruiters.example.csv to recruiters.csv "
            "and add your outreach list."
        )

    with csv_file.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(f"{csv_file} is empty.")

    required = {"name", "company", "email"}
    if not required.issubset(rows[0].keys()):
        raise ValueError("CSV must contain: name, company, email")

    return rows


def load_sent_emails(log_file):
    if not log_file.exists():
        return set()

    with log_file.open(newline="", encoding="utf-8") as f:
        return {
            row["email"].strip().lower()
            for row in csv.DictReader(f)
            if row.get("status") == "sent" and row.get("email")
        }


def log_sent(log_file, recruiter, message_id):
    exists = log_file.exists()

    with log_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp", "name", "company", "email", "status", "message_id"],
        )

        if not exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "name": recruiter["name"],
            "company": recruiter["company"],
            "email": recruiter["email"],
            "status": "sent",
            "message_id": message_id,
        })


def build_message(recipient, subject, body, resume_path):
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    resume_path = Path(resume_path)
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume not found: {resume_path}")

    mime_type, _ = mimetypes.guess_type(resume_path.name)
    if mime_type:
        main_type, sub_type = mime_type.split("/", 1)
    else:
        main_type, sub_type = "application", "octet-stream"

    with resume_path.open("rb") as f:
        message.add_attachment(
            f.read(),
            maintype=main_type,
            subtype=sub_type,
            filename=resume_path.name,
        )

    return message


def send_message(service, message):
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
    response = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded})
        .execute()
    )
    return response["id"]


def main():
    parser = argparse.ArgumentParser(
        description="OutreachKit: Personalized Email Outreach with Python and the Gmail API."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview emails without sending.")
    parser.add_argument("--resume", type=Path, default=BASE_DIR / "resume.pdf")
    parser.add_argument("--recruiters", type=Path, default=BASE_DIR / "recruiters.csv")
    parser.add_argument("--template", type=Path, default=BASE_DIR / "email_template.txt")
    parser.add_argument("--credentials", type=Path, default=BASE_DIR / "credentials.json")
    parser.add_argument("--token", type=Path, default=BASE_DIR / "token.json")
    parser.add_argument("--log", type=Path, default=BASE_DIR / "sent_log.csv")
    parser.add_argument("--subject", default=SUBJECT)
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip the per-email confirmation. Use only with a small reviewed list.",
    )
    args = parser.parse_args()

    try:
        recruiters = load_recruiters(args.recruiters)
        template = args.template.read_text(encoding="utf-8")
        sent_emails = load_sent_emails(args.log)
    except (OSError, ValueError) as exc:
        print(f"Setup error: {exc}", file=sys.stderr)
        return 1

    try:
        service = None if args.dry_run else authenticate(args.credentials, args.token)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Authentication error: {exc}", file=sys.stderr)
        return 1

    for recruiter in recruiters:
        name = recruiter["name"].strip()
        company = recruiter["company"].strip()
        email = recruiter["email"].strip().lower()

        if not all([name, company, email]):
            print("Skipping incomplete row:", recruiter)
            continue

        if email in sent_emails:
            print(f"SKIP: {email} (already sent)")
            continue

        body = template.format(name=name, company=company)
        try:
            message = build_message(email, args.subject, body, args.resume)
        except OSError as exc:
            print(f"Setup error: {exc}", file=sys.stderr)
            return 1

        print("\n" + "=" * 70)
        print(f"To: {email}")
        print(f"Company: {company}")
        print(f"Subject: {args.subject}")
        print("-" * 70)
        print(body.rstrip())
        print("=" * 70)

        if args.dry_run:
            print("DRY RUN: not sent.")
            continue

        if not args.no_confirm:
            answer = input("Send this email? [y/N/q]: ").strip().lower()
            if answer == "q":
                break
            if answer != "y":
                print("Skipped.")
                continue

        try:
            message_id = send_message(service, message)
            log_sent(args.log, recruiter, message_id)
            sent_emails.add(email)
            print(f"SENT: {email}")
        except Exception as exc:
            print(f"Error for {email}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
