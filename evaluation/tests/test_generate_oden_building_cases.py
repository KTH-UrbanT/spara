from evaluation.scripts import generate_oden_building_cases as generator


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
