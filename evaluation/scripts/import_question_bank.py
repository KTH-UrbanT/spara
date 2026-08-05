import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "data" / "evaluation_cases_imported.jsonl"


def _load_rows(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        raise ValueError("JSON question bank must contain a list of objects.")
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix in {".xlsx", ".xls"}:
        try:
            import pandas as pd  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Reading Excel files requires pandas/openpyxl.") from exc
        return pd.read_excel(path).fillna("").to_dict(orient="records")
    raise ValueError(f"Unsupported question bank format: {suffix}")


def _normalize_bool(value: Any) -> Any:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return value


def _first_present(row: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", []):
            return value
    return None


def _normalize_list(value: Any) -> List[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split("|") if part.strip()]
    return [str(value).strip()]


def _build_case(row: Dict[str, Any], index: int) -> Dict[str, Any]:
    question = _first_present(row, "question", "user_question", "prompt", "text")
    if not question:
        raise ValueError(f"Row {index + 1} does not contain a question field.")

    case_id = _first_present(row, "case_id", "id")
    if not case_id:
        case_id = f"IMPORTED_{index + 1:04d}"

    case = {
        "case_id": str(case_id),
        "question": str(question).strip(),
    }

    mappings = {
        "expected_route": ("expected_route", "route", "label"),
        "expected_agent": ("expected_agent", "agent"),
        "expected_behavior": ("expected_behavior", "behavior"),
        "expected_answer": ("expected_answer", "reference_answer", "answer"),
        "brf_name": ("brf_name", "brf", "building_name"),
        "address": ("address", "official_address"),
        "expected_building_id": ("expected_building_id", "building_id"),
        "expected_out_of_scope_type": ("expected_out_of_scope_type", "out_of_scope_type"),
        "advisor_reference_id": ("advisor_reference_id", "reference_id"),
        "case_type": ("case_type", "category"),
    }

    for output_key, input_keys in mappings.items():
        value = _first_present(row, *input_keys)
        if value not in (None, "", []):
            case[output_key] = value

    expected_fields = _normalize_list(_first_present(row, "expected_fields", "fields"))
    if expected_fields:
        case["expected_fields"] = expected_fields

    must_include = _normalize_list(_first_present(row, "must_include", "required_terms"))
    if must_include:
        case["must_include"] = must_include

    must_not_include = _normalize_list(_first_present(row, "must_not_include", "forbidden_terms"))
    if must_not_include:
        case["must_not_include"] = must_not_include

    expected_clarification = _first_present(row, "expected_clarification", "needs_clarification")
    if expected_clarification not in (None, ""):
        case["expected_clarification"] = _normalize_bool(expected_clarification)

    return case


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a question bank into SPARA evaluation case JSONL.")
    parser.add_argument("input", type=Path, help="Path to CSV, JSONL, JSON, or XLSX question bank")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    rows = _load_rows(args.input)
    cases = [_build_case(row, index) for index, row in enumerate(rows)]
    _write_jsonl(args.output, cases)
    print(f"Wrote {len(cases)} cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
