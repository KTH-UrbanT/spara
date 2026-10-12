from evaluation.scripts import generate_oden_building_cases as generator
import pytest


def test_build_cases_uses_latest_epc_record_for_same_building(monkeypatch):
    def fake_fetch_address(address, *, base_url, timeout, retries):
        return [
            {
                "byggnadsid": "01-80-SKYTTEN2-2",
                "50a_uuid": "5174853a-d8c1-4b87-8a34-d05c054e443d",
                "epc_idadr": "Artemisgatan 13",
                "epc_idpostort": "Stockholm",
                "epc_godkand": "2009-09-24",
                "epc_egiversion": "2010",
                "epc_egienergiklass2020_calc": "F",
                "epc_egienergiprestanda": 220,
                "epc_egispecifikenergianvandning_calc": 220,
            },
            {
                "byggnadsid": "01-80-SKYTTEN2-2",
                "50a_uuid": "5174853a-d8c1-4b87-8a34-d05c054e443d",
                "epc_idadr": "Artemisgatan 13",
                "epc_idpostort": "Stockholm",
                "epc_godkand": "2019-11-03",
                "epc_egiversion": "2019",
                "epc_egienergiklass2020_calc": "F",
                "epc_egienergiprestanda": 201,
                "epc_egispecifikenergianvandning": 198,
                "epc_egiprimarenergital2019": 201,
                "epc_egiprimarenergital2020_calc": 145,
            },
        ]

    monkeypatch.setattr(generator, "fetch_address", fake_fetch_address)

    cases = generator.build_cases(
        ["Artemisgatan 17"],
        base_url="https://example.invalid",
        timeout=1,
        retries=0,
        prefix="BRF_ODEN",
    )

    performance_case = next(
        case for case in cases if case["case_id"].endswith("_PERFORMANCE")
    )
    building_info = performance_case["expected_building_info"]

    assert len(cases) == 3
    assert building_info["energy_performance"] == 201
    assert building_info["specific_energy_use"] == 198
    assert building_info["primary_energy_number"] == 145
    assert "201" in performance_case["must_include"]
    assert "220" not in performance_case["must_include"]


def test_declared_energy_class_precedes_calculated_variants_and_retains_provenance():
    info = generator._extract_building_info({
        "byggnadsid": "01-80-SKYTTEN2-2", "50a_uuid": "source-uuid",
        "epc_formularid": "epc-42", "epc_godkand": "2019-11-03", "epc_egiversion": "2019",
        "epc_egienergiklass": "G", "energy_class": "D",
        "epc_egienergiklass2020_calc": "F", "epc_egienergiklass2016_calc": "E",
        "epc_egienergiprestanda": 201, "energy_performance": 999,
    })
    assert info["energy_class"] == info["declared_energy_class"] == "G"
    assert info["calculated_energy_class_2020"] == "F"
    assert info["calculated_energy_class_2016"] == "E"
    assert info["energy_class_basis"] == "declared"
    assert info["energy_class_source_field"] == "epc_egienergiklass"
    assert info["energy_performance"] == 201
    assert info["energy_performance_source_field"] == "epc_egienergiprestanda"
    assert info["source_record"] == {"building_id": "01-80-SKYTTEN2-2", "uuid": "source-uuid",
                                    "epc_record_id": "epc-42", "approved_at": "2019-11-03", "version": "2019"}
    assert info["record_selection_basis"] == "epc_godkand"


@pytest.mark.parametrize("metric", ["epc_egiprimarenergital2019", "epc_egiprimarenergital2020_calc",
                                    "epc_egispecifikenergianvandning", "epc_egispecifikenergianvandning_calc"])
def test_missing_declared_performance_is_not_filled_with_a_different_metric(metric):
    info = generator._extract_building_info({"byggnadsid": "01-80-SKYTTEN2-2", metric: 145})
    assert "energy_performance" not in info
    assert "energy_performance_source_field" not in info
    assert any(key in info for key in ("specific_energy_use", "primary_energy_number"))


def test_calculated_class_is_explicit_when_declared_class_is_absent():
    info = generator._extract_building_info({"byggnadsid": "01-80-SKYTTEN2-2", "epc_egienergiklass2020_calc": "F"})
    assert info["energy_class"] == info["calculated_energy_class_2020"] == "F"
    assert info["energy_class_basis"] == "calculated"
    assert info["energy_class_source_field"] == "epc_egienergiklass2020_calc"
    assert "declared_energy_class" not in info


def test_build_cases_retains_source_query_without_rewriting_original_data(monkeypatch):
    record = {"byggnadsid": "01-80-SKYTTEN2-2", "epc_idadr": "Artemisgatan 13",
              "epc_godkand": "2019-11-03", "epc_egienergiprestanda": 0}
    monkeypatch.setattr(generator, "fetch_address", lambda *args, **kwargs: [record])
    cases = generator.build_cases(["Artemisgatan 17"], base_url="https://example.invalid/address", timeout=1, retries=0, prefix="TEST")
    performance = next(case for case in cases if case["case_id"].endswith("_PERFORMANCE"))
    info = performance["expected_building_info"]
    assert info["source_endpoint"] == "https://example.invalid/address"
    assert info["source_query_address"] == "Artemisgatan 17"
    assert info["address"] == "Artemisgatan 13"
    assert "0" in performance["must_include"]
    assert record == {"byggnadsid": "01-80-SKYTTEN2-2", "epc_idadr": "Artemisgatan 13",
                      "epc_godkand": "2019-11-03", "epc_egienergiprestanda": 0}


def test_empty_api_record_does_not_become_a_building_from_provenance_fields(monkeypatch):
    monkeypatch.setattr(generator, "fetch_address", lambda *args, **kwargs: [{}])
    cases = generator.build_cases(["Missing 1"], base_url="https://example.invalid", timeout=1, retries=0, prefix="TEST")
    assert len(cases) == 1
    assert cases[0]["case_id"].endswith("_NOT_FOUND")
