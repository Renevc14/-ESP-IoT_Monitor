"""Unit tests for the analytics export helpers."""
import uuid
from datetime import datetime, timezone

from app.routers.export import _COLUMNS, _to_dict


def test_to_dict_maps_row_to_expected_shape():
    device_id = uuid.uuid4()
    row = (7, device_id, "temperature", 27.42, "C", datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc))
    result = _to_dict(row)

    assert set(result.keys()) == set(_COLUMNS)
    assert result["id"] == 7
    assert result["device_id"] == str(device_id)
    assert result["sensor_type"] == "temperature"
    assert result["value"] == 27.42
    assert result["unit"] == "C"
    assert result["recorded_at"].startswith("2026-01-01T12:00")


def test_columns_order_is_stable():
    assert _COLUMNS == ["id", "device_id", "sensor_type", "value", "unit", "recorded_at"]
