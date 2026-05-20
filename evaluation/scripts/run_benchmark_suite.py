import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = REPO_ROOT / "evaluation" / "scripts"
DEFAULT_CASES_PATH = REPO_ROOT / "evaluation" / "data" / "evaluation_cases.jsonl"
DEFAULT_RESULTS_PATH = REPO_ROOT / "evaluation" / "results" / "eval_results.jsonl"
DEFAULT_SUMMARY_PATH = REPO_ROOT / "evaluation" / "results" / "metric_summary.json"
DEFAULT_ADVISOR_SHEET_PATH = REPO_ROOT / "evaluation" / "results" / "advisor_reviews.csv"
DEFAULT_REPORT_PATH = REPO_ROOT / "evaluation" / "results" / "benchmark_report.md"
DEFAULT_EMAIL_RECIPIENT = "shadaab@kth.se"


def _default_email_recipients() -> str:
    return (
        os.getenv("BENCHMARK_EMAIL_RECIPIENTS")
        or os.getenv("BENCHMARK_EMAIL_RECIPIENT")
        or DEFAULT_EMAIL_RECIPIENT
    )


def _run_step(args: list[str]) -> None:
    print("Running:", " ".join(str(arg) for arg in args))
    subprocess.run(args, cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run SPARA benchmark scenarios and generate analysis artifacts."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--advisor-sheet", type=Path, default=DEFAULT_ADVISOR_SHEET_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--case-id")
    parser.add_argument("--route")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--variants",
        default="full",
        help=(
            "Comma-separated evaluation variants for run_eval_cases.py. "
            "Examples: full or full,llm_only,standard_rag,sql_only,no_vector,no_sql."
        ),
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Reuse an existing eval_results.jsonl and only regenerate summary/report artifacts.",
    )
    parser.add_argument(
        "--export-advisor-sheet",
        action="store_true",
        help="Also regenerate the blank advisor review CSV from benchmark results.",
    )
    parser.add_argument(
        "--email-report",
        action="store_true",
        help="Email benchmark_report.md after it is generated.",
    )
    parser.add_argument(
        "--email-to",
        default=_default_email_recipients(),
        help=(
            "Recipients for --email-report. Accepts comma, semicolon, or whitespace "
            "separated addresses. Defaults to BENCHMARK_EMAIL_RECIPIENTS, then "
            "BENCHMARK_EMAIL_RECIPIENT, then shadaab@kth.se."
        ),
    )
    args = parser.parse_args()

    if not args.skip_run:
        run_eval_command = [
            sys.executable,
            str(SCRIPTS_ROOT / "run_eval_cases.py"),
            "--evaluation-mode",
            "--input",
            str(args.input),
            "--output",
            str(args.results),
            "--variants",
            args.variants,
        ]
        if args.case_id:
            run_eval_command.extend(["--case-id", args.case_id])
        if args.route:
            run_eval_command.extend(["--route", args.route])
        if args.limit is not None:
            run_eval_command.extend(["--limit", str(args.limit)])
        _run_step(run_eval_command)

    _run_step(
        [
            sys.executable,
            str(SCRIPTS_ROOT / "analyze_eval_results.py"),
            "--results",
            str(args.results),
            "--reviews",
            str(args.advisor_sheet),
            "--output",
            str(args.summary),
        ]
    )
    if args.export_advisor_sheet:
        _run_step(
            [
                sys.executable,
                str(SCRIPTS_ROOT / "export_advisor_review_sheet.py"),
                "--results",
                str(args.results),
                "--output",
                str(args.advisor_sheet),
            ]
        )
    _run_step(
        [
            sys.executable,
            str(SCRIPTS_ROOT / "generate_benchmark_report.py"),
            "--results",
            str(args.results),
            "--summary",
            str(args.summary),
            "--output",
            str(args.report),
        ]
    )

    should_email = args.email_report or os.getenv("BENCHMARK_EMAIL_ENABLED", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if should_email:
        _run_step(
            [
                sys.executable,
                str(SCRIPTS_ROOT / "email_benchmark_report.py"),
                "--report",
                str(args.report),
                "--summary",
                str(args.summary),
                "--to",
                args.email_to,
            ]
        )

    print(f"Benchmark suite complete. Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
