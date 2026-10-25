from _stats_spa_cases import (
    test_seed_data_is_served_and_has_no_double_commas as _test_seed_data,
    test_stats_by_identity_returns_json_even_for_new_user as _test_stats,
    test_today_hub_structure_and_consistency as _test_today_hub,
    test_unmatched_api_routes_return_404_json_not_html as _test_unknown_route,
)


def test_stats_by_identity_returns_json_even_for_new_user():
    return _test_stats()


def test_unmatched_api_routes_return_404_json_not_html():
    return _test_unknown_route()


def test_seed_data_is_served_and_has_no_double_commas():
    return _test_seed_data()


def test_today_hub_structure_and_consistency():
    return _test_today_hub()
