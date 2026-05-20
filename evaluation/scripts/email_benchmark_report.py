import argparse
import os
import re
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = REPO_ROOT / "evaluation" / "results" / "benchmark_report.md"
DEFAULT_SUMMARY_PATH = REPO_ROOT / "evaluation" / "results" / "metric_summary.json"
DEFAULT_RECIPIENT = "shadaab@kth.se"
RECIPIENT_SPLIT_PATTERN = re.compile(r"[,;\s]+")


def _env(name: str, fallback_name: str | None = None, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    if fallback_name:
        value = os.getenv(fallback_name)
        if value:
            return value
    return default


def _smtp_port() -> int:
    value = _env("BENCHMARK_EMAIL_SMTP_PORT", default="587")
    return int(value or "587")


def _recipient_default() -> str:
    return (
        _env("BENCHMARK_EMAIL_RECIPIENTS")
        or _env("BENCHMARK_EMAIL_RECIPIENT")
        or DEFAULT_RECIPIENT
    )


def parse_recipients(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw_recipients = value
    else:
        raw_recipients = RECIPIENT_SPLIT_PATTERN.split(value)

    recipients = []
    seen = set()
    for recipient in raw_recipients:
        normalized = recipient.strip()
        if not normalized or normalized in seen:
            continue
        recipients.append(normalized)
        seen.add(normalized)
    return recipients


def build_benchmark_email(
    *,
    report_path: Path,
    summary_path: Path,
    recipients: str | list[str],
    sender: str,
) -> EmailMessage:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report_text = report_path.read_text(encoding="utf-8")
    recipient_list = parse_recipients(recipients)
    if not recipient_list:
        raise ValueError("At least one benchmark email recipient is required.")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipient_list)
    message["Subject"] = f"SPARA benchmark report - {generated_at}"
    message.set_content(
        "Hello,\n\n"
        "The SPARA benchmark suite has completed.\n\n"
        f"Report path on server: {report_path}\n"
        f"Generated at: {generated_at}\n\n"
        "The Markdown benchmark report is attached.\n"
    )

    message.add_attachment(
        report_text,
        subtype="markdown",
        filename=report_path.name,
    )

    if summary_path.exists():
        message.add_attachment(
            summary_path.read_text(encoding="utf-8"),
            subtype="json",
            filename=summary_path.name,
        )

    return message


def send_benchmark_report(
    *,
    report_path: Path,
    summary_path: Path,
    recipients: str | list[str],
) -> bool:
    smtp_server = _env("BENCHMARK_EMAIL_SMTP_SERVER", "EXPERT_EMAIL_SMTP_SERVER")
    smtp_account = _env("BENCHMARK_EMAIL_ACCOUNT", "EXPERT_EMAIL_ACCOUNT")
    smtp_password = _env("BENCHMARK_EMAIL_PASSWORD", "EXPERT_EMAIL_PASSWORD")
    sender = _env("BENCHMARK_EMAIL_ADDRESS", "EXPERT_EMAIL_ADDRESS", smtp_account)
    recipient_list = parse_recipients(recipients)

    missing = [
        name
        for name, value in (
            ("BENCHMARK_EMAIL_SMTP_SERVER or EXPERT_EMAIL_SMTP_SERVER", smtp_server),
            ("BENCHMARK_EMAIL_ACCOUNT or EXPERT_EMAIL_ACCOUNT", smtp_account),
            ("BENCHMARK_EMAIL_PASSWORD or EXPERT_EMAIL_PASSWORD", smtp_password),
            ("BENCHMARK_EMAIL_ADDRESS or EXPERT_EMAIL_ADDRESS", sender),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Cannot email benchmark report. Missing environment variables: "
            + ", ".join(missing)
        )

    if not report_path.exists():
        raise FileNotFoundError(f"Benchmark report not found: {report_path}")

    message = build_benchmark_email(
        report_path=report_path,
        summary_path=summary_path,
        recipients=recipient_list,
        sender=sender,
    )

    smtp_session = smtplib.SMTP(smtp_server, _smtp_port())
    try:
        smtp_session.ehlo()
        smtp_session.starttls()
        smtp_session.ehlo()
        smtp_session.login(smtp_account, smtp_password)
        smtp_session.send_message(message, to_addrs=recipient_list)
        return True
    finally:
        smtp_session.quit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Email the generated SPARA benchmark report.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument(
        "--to",
        default=_recipient_default(),
        help=(
            "Email recipients. Accepts comma, semicolon, or whitespace separated "
            "addresses. Defaults to BENCHMARK_EMAIL_RECIPIENTS, then "
            "BENCHMARK_EMAIL_RECIPIENT, then shadaab@kth.se."
        ),
    )
    args = parser.parse_args()
    recipients = parse_recipients(args.to)

    send_benchmark_report(
        report_path=args.report,
        summary_path=args.summary,
        recipients=recipients,
    )
    print(f"Emailed benchmark report to {', '.join(recipients)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
