import pytest
from fastapi import HTTPException
from backend.helpers.credentials import compare_ids


def test_compare_ids_success():
    assert compare_ids(1, 1) is None


def test_compare_ids_forbidden():
    with pytest.raises(HTTPException) as exception:
        compare_ids(current_user_id=1, selected_user_id=2)

    assert exception.value.status_code == 403
    assert exception.value.detail == "Not authorized"


@pytest.mark.parametrize(
    "id_a, id_b, expected_fail",
    [
        (10, 10, False),
        (10, 20, True),
        ("uuid-1", "uuid-1", False),
        ("uuid-1", "uuid-2", True),
    ],
)
def test_compare_ids_variants(id_a, id_b, expected_fail):
    if expected_fail:
        with pytest.raises(HTTPException):
            compare_ids(id_a, id_b)
    else:
        compare_ids(id_a, id_b)
