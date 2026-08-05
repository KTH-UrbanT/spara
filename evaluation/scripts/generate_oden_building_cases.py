import argparse
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = REPO_ROOT / "evaluation" / "data" / "oden_building_specific_cases.jsonl"
DEFAULT_EVAL_CASES_PATH = REPO_ROOT / "evaluation" / "data" / "evaluation_cases.jsonl"
DEFAULT_ODEN_URL = "https://oden.abe.kth.se/api/v1/buildings/address"
DEFAULT_ADDRESSES = [
    "Tulegatan 5a",
    "Professorsslingan 51",
    "Teknikringen 10b",
    "Drottning Kristinas väg 43A",
    "Artemisgatan 17",
    "Teknikringen 78B",
    "Teknikringen 37A",
    "Professorsslingan 49",
    "Professorsslingan 53",
    "Rådmansgatan 31",
]


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _first_present(row: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if _present(value):
            return value
    return None


def _parse_epc_version_date(value: Any) -> tuple[int, int, int] | None:
    if not _present(value):
        return None
    if isinstance(value, int):
        return (value, 0, 0) if 1900 <= value <= 2199 else None
    if isinstance(value, float):
        as_int = int(value)
        return (as_int, 0, 0) if value.is_integer() and 1900 <= as_int <= 2199 else None

    text = str(value).strip()
    date_match = re.search(r"\b(19\d{2}|20\d{2}|21\d{2})[-/.]?(\d{2})[-/.]?(\d{2})\b", text)
    if date_match:
        year, month, day = (int(part) for part in date_match.groups())
        if 1 <= month <= 12 and 1 <= day <= 31:
            return (year, month, day)

    year_match = re.search(r"\b(19\d{2}|20\d{2}|21\d{2})\b", text)
    if year_match:
        return (int(year_match.group(1)), 0, 0)

    return None


def _record_identity_key(row: Dict[str, Any]) -> str:
    return str(
        _first_present(row, "byggnadsid", "building_id", "50a_uuid", "01a_fnr")
        or json.dumps(row, sort_keys=True, ensure_ascii=False)
    )


def _record_version_key(row: Dict[str, Any]) -> tuple[int, int, int] | None:
    return _parse_epc_version_date(
        _first_present(
            row,
            "epc_godkand",
            "epc_egiversion",
            "epc_egiversion_calc",
            "energy_declaration_year",
        )
    )


def _ascii_slug(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", folded).strip("_").upper()
    return slug or "ADDRESS"


def _normalize_heating_system(value: Any) -> str | None:
    if not _present(value):
        return None
    raw = str(value).strip()
    folded = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii").lower()
    folded = re.sub(r"[^a-z0-9]+", "", folded)
    mappings = [
        (("fjarrvarme", "districtheating"), "district heating"),
        (("pumpluftvatten", "airtowaterheatpump"), "air-to-water heat pump"),
        (("pumpluftluft", "airtoairheatpump"), "air-to-air heat pump"),
        (("pumpmark", "bergvarme", "groundsourceheatpump"), "ground source heat pump"),
        (("pumpfranluft", "franluft", "exhaustairheatpump"), "exhaust air heat pump"),
        (("eldirekt", "directelectric"), "direct electric heating"),
        (("elvatten",), "electric water-based heating"),
        (("olja", "oil"), "oil heating"),
        (("gas",), "gas heating"),
        (("ved", "wood"), "wood heating"),
        (("flis", "pellet", "bio"), "biofuel heating"),
    ]
    for needles, label in mappings:
        if any(needle in folded for needle in needles):
            return label
    return raw


def _heating_terms(heating_system: str | None) -> List[str]:
    if not heating_system:
        return []
    lowered = heating_system.lower()
    if "district heating" in lowered:
        return ["district heating"]
    if "heat pump" in lowered:
        return ["heat pump"]
    if "electric" in lowered:
        return ["electric"]
    if "oil" in lowered:
        return ["oil"]
    if "gas" in lowered:
        return ["gas"]
    if "wood" in lowered:
        return ["wood"]
    return [heating_system]


def _yes(value: Any) -> bool:
    return str(value or "").strip().lower() in {"ja", "yes", "true", "1"}


def _ventilation_type(row: Dict[str, Any]) -> str | None:
    if _yes(row.get("epc_venttypftx")):
        return "balanced ventilation with heat recovery (FTX)"
    if _yes(row.get("epc_venttypft")):
        return "mechanical supply and exhaust ventilation"
    if _yes(row.get("epc_venttypf")):
        return "mechanical exhaust ventilation"
    if _yes(row.get("epc_venttypsjalvdrag")):
        return "natural ventilation"
    return None


def _extract_building_info(row: Dict[str, Any]) -> Dict[str, Any]:
    heating_system = _normalize_heating_system(
        _first_present(
            row,
            "heating_system",
            "epc_huvudsakliguppvarmning_calc",
            "epc_egigruppfjarrvarme",
        )
    )
    info = {
        "address": _first_present(row, "address", "epc_idadr"),
        "city": _first_present(row, "epc_idpostort", "epc_idkommun"),
        "building_id": _first_present(row, "byggnadsid", "building_id"),
        "50a_uuid": _first_present(row, "50a_uuid"),
        "energy_class": _first_present(
            row,
            "energy_class",
            "epc_egienergiklass2020_calc",
            "epc_egienergiklass2016_calc",
            "epc_egienergiklass",
        ),
        "energy_performance": _first_present(
            row,
            "energy_performance",
            "epc_egienergiprestanda",
            "epc_egiprimarenergital2019",
            "epc_egiprimarenergital2020_calc",
            "epc_egiprimarenergital2020",
            "epc_egispecifikenergianvandning",
            "epc_egispecifikenergianvandning_calc",
        ),
        "specific_energy_use": _first_present(
            row,
            "specific_energy_use",
            "epc_egispecifikenergianvandning",
            "epc_egispecifikenergianvandning_calc",
            "epc_egispecifikenergianvandning_eindex_calc",
        ),
        "primary_energy_number": _first_present(
            row,
            "primary_energy_number",
            "primary_energy",
            "epc_egiprimarenergital2020_calc",
            "epc_egiprimarenergital2020",
            "epc_egiprimarenergital2019",
            "epc_egiprimarenergital",
        ),
        "heating_system": heating_system,
        "ventilation_type": _ventilation_type(row),
        "atemp": _first_present(row, "epc_egenatemp"),
        "building_type": _first_present(row, "epc_egenbyggnadskat", "epc_egentypkod_typ"),
        "construction_year": _first_present(row, "epc_egennybyggar"),
    }
    return {key: value for key, value in info.items() if _present(value)}


def _display_address(address: str, info: Dict[str, Any]) -> str:
    if info.get("city"):
        return f"{address}, {info['city']}"
    return address


def _case_building_info(address: str, info: Dict[str, Any]) -> Dict[str, Any]:
    enriched = {"input_address": address, **info}
    return {key: value for key, value in enriched.items() if _present(value)}


def _unique_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique = []
    seen = set()
    for row in records:
        key = (
            _record_identity_key(row),
            _first_present(
                row,
                "epc_formularid",
                "epc_godkand",
                "epc_egiversion",
                "epc_version",
            ),
            _first_present(row, "epc_idadr", "address"),
        )
        if key in seen:
            continue
        unique.append(row)
        seen.add(key)
    return unique


def _select_latest_epc_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    order: List[str] = []
    for row in records or []:
        key = _record_identity_key(row)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(row)

    selected: List[Dict[str, Any]] = []
    for key in order:
        rows = grouped[key]
        keyed_rows = [(row, _record_version_key(row)) for row in rows]
        available_keys = [version for _, version in keyed_rows if version is not None]
        if not available_keys:
            selected.extend(rows)
            continue
        latest = max(available_keys)
        selected.extend(row for row, version in keyed_rows if version == latest)
    return selected


def fetch_address(address: str, *, base_url: str, timeout: float, retries: int) -> List[Dict[str, Any]]:
    query = urllib.parse.urlencode({"address": address, "case_sensitive": "false"})
    url = f"{base_url}?{query}"
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, list):
                return [row for row in payload if isinstance(row, dict)]
            if isinstance(payload, dict):
                for key in ("data", "results", "buildings"):
                    nested = payload.get(key)
                    if isinstance(nested, list):
                        return [row for row in nested if isinstance(row, dict)]
                return [payload]
            return []
        except Exception as exc:  # pragma: no cover - network best effort
            last_error = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {address!r}: {last_error}")


def _heating_case(prefix: str, index: int, address: str, info: Dict[str, Any]) -> Dict[str, Any]:
    heating = info.get("heating_system")
    display_address = _display_address(address, info)
    return {
        "case_id": f"{prefix}_{index:03d}_HEATING",
        "question": "What is the heating system in my building?",
        "address": address,
        "registered_address": info.get("address"),
        "city": info.get("city"),
        "byggnadsid": info.get("building_id"),
        "50a_uuid": info.get("50a_uuid"),
        "expected_route": "building_specific",
        "expected_agent": "BuildingAgent",
        "expected_building_id": info.get("building_id"),
        "expected_fields": ["heating_system"],
        "expected_answer": (
            f"The answer should use ODEN building data for {display_address} "
            f"and state that the heating system is {heating}."
            if heating
            else f"The answer should use ODEN building data for {display_address} and say if the heating system is unavailable."
        ),
        "must_include": _heating_terms(heating),
        "must_not_include": ["I need the full building address", "not enough building data"],
        "expected_building_info": _case_building_info(address, info),
        "case_type": "building_specific_factual",
        "source": "ODEN API",
    }


def _performance_case(prefix: str, index: int, address: str, info: Dict[str, Any]) -> Dict[str, Any]:
    display_address = _display_address(address, info)
    energy_class = info.get("energy_class")
    energy_performance = info.get("energy_performance")
    must_include = []
    if energy_class:
        must_include.append(str(energy_class))
    if energy_performance:
        must_include.append(str(energy_performance))
    return {
        "case_id": f"{prefix}_{index:03d}_PERFORMANCE",
        "question": "What is the energy performance of my building?",
        "address": address,
        "registered_address": info.get("address"),
        "city": info.get("city"),
        "byggnadsid": info.get("building_id"),
        "50a_uuid": info.get("50a_uuid"),
        "expected_route": "building_specific",
        "expected_agent": "BuildingAgent",
        "expected_building_id": info.get("building_id"),
        "expected_fields": ["energy_performance", "energy_class"],
        "expected_answer": (
            f"The answer should use ODEN building data for {display_address}. "
            f"Expected energy class: {energy_class}; expected energy performance: {energy_performance}."
        ),
        "must_include": must_include,
        "must_not_include": ["I need the full building address", "not enough building data"],
        "expected_building_info": _case_building_info(address, info),
        "case_type": "building_specific_factual",
        "source": "ODEN API",
    }


def _advice_case(prefix: str, index: int, address: str, info: Dict[str, Any]) -> Dict[str, Any]:
    display_address = _display_address(address, info)
    return {
        "case_id": f"{prefix}_{index:03d}_ADVICE",
        "question": "What should my building prioritize to improve energy efficiency?",
        "address": address,
        "registered_address": info.get("address"),
        "city": info.get("city"),
        "byggnadsid": info.get("building_id"),
        "50a_uuid": info.get("50a_uuid"),
        "expected_route": "combined",
        "expected_agent": "BuildingAgent",
        "expected_building_id": info.get("building_id"),
        "expected_fields": ["heating_system", "energy_performance", "energy_class"],
        "expected_answer": (
            f"The answer should combine ODEN data for {display_address} with general advisory guidance. "
            "It should mention relevant building facts, explain assumptions, and avoid guaranteed savings."
        ),
        "must_include": [],
        "must_not_include": ["guaranteed savings", "I need the full building address"],
        "expected_building_info": _case_building_info(address, info),
        "case_type": "combined_building_specific_advice",
        "source": "ODEN API",
    }


def _ambiguous_case(prefix: str, index: int, address: str, infos: List[Dict[str, Any]]) -> Dict[str, Any]:
    cities = sorted({str(info.get("city")) for info in infos if info.get("city")})
    return {
        "case_id": f"{prefix}_{index:03d}_AMBIGUOUS",
        "question": f"What is the heating system in my building? My address is {address}.",
        "address": address,
        "expected_route": "clarification",
        "expected_agent": "BuildingAgent",
        "expected_answer": (
            "The answer should not choose one building. It should ask for a city, municipality, "
            "building ID, or another identifier before using building-specific data."
        ),
        "must_include": [],
        "must_not_include": ["guaranteed savings"],
        "candidate_buildings": infos,
        "case_type": "ambiguous_building_address",
        "source": "ODEN API",
        "candidate_cities": cities,
    }


def build_cases(addresses: List[str], *, base_url: str, timeout: float, retries: int, prefix: str) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for address_index, address in enumerate(addresses, start=1):
        records = _select_latest_epc_records(
            _unique_records(fetch_address(address, base_url=base_url, timeout=timeout, retries=retries))
        )
        infos = [_extract_building_info(row) for row in records]
        infos = [info for info in infos if info]
        case_prefix = f"{prefix}_{address_index:02d}_{_ascii_slug(address)}"
        if not infos:
            cases.append(
                {
                    "case_id": f"{case_prefix}_NOT_FOUND",
                    "question": f"What is the heating system in my building? My address is {address}.",
                    "address": address,
                    "expected_route": "clarification",
                    "expected_agent": "BuildingAgent",
                    "expected_answer": "The answer should say that no reliable building data was found and ask for a corrected full address.",
                    "must_include": [],
                    "must_not_include": ["guaranteed savings"],
                    "case_type": "unknown_or_invalid_building",
                    "source": "ODEN API",
                }
            )
            continue

        if len(infos) > 1:
            cases.append(_ambiguous_case(case_prefix, 1, address, infos))
            for record_index, info in enumerate(infos, start=1):
                cases.append(_heating_case(case_prefix, record_index, address, info))
                cases.append(_performance_case(case_prefix, record_index, address, info))
            continue

        info = infos[0]
        cases.append(_heating_case(case_prefix, 1, address, info))
        cases.append(_performance_case(case_prefix, 1, address, info))
        cases.append(_advice_case(case_prefix, 1, address, info))
    return cases


def merge_cases(existing: List[Dict[str, Any]], generated: List[Dict[str, Any]], *, prefix: str) -> List[Dict[str, Any]]:
    filtered = [
        row
        for row in existing
        if not str(row.get("case_id") or "").startswith(prefix)
    ]
    return filtered + generated


def _addresses_from_args(raw_addresses: List[str] | None, address_file: Path | None) -> List[str]:
    addresses = list(raw_addresses or [])
    if address_file:
        for line in address_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                addresses.append(stripped)
    return addresses or DEFAULT_ADDRESSES


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate building-specific SPARA evaluation cases from ODEN address lookups.")
    parser.add_argument("--address", action="append", dest="addresses", help="Address to fetch. Can be repeated.")
    parser.add_argument("--address-file", type=Path, help="Optional newline-separated address file.")
    parser.add_argument("--base-url", default=DEFAULT_ODEN_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--merge-into", type=Path, help="Optionally merge generated cases into evaluation_cases.jsonl.")
    parser.add_argument("--prefix", default="BRF_ODEN")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=1)
    args = parser.parse_args()

    addresses = _addresses_from_args(args.addresses, args.address_file)
    cases = build_cases(
        addresses,
        base_url=args.base_url,
        timeout=args.timeout,
        retries=args.retries,
        prefix=args.prefix,
    )
    _write_jsonl(args.output, cases)
    print(f"Wrote {len(cases)} generated ODEN cases to {args.output}")

    if args.merge_into:
        merged = merge_cases(_load_jsonl(args.merge_into), cases, prefix=args.prefix)
        _write_jsonl(args.merge_into, merged)
        print(f"Merged generated cases into {args.merge_into}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
