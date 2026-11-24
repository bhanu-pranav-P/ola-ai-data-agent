"""Tests for the read-only SQL guard — the thing standing between the
LLM and the database, so it gets proper tests."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db_utils import is_safe_select  # noqa: E402


def test_plain_select_is_allowed():
    ok, _ = is_safe_select("SELECT * FROM bookings WHERE city = 'Mumbai'")
    assert ok


def test_aggregate_select_is_allowed():
    ok, _ = is_safe_select("SELECT city, SUM(fare_amount) FROM bookings GROUP BY city")
    assert ok


def test_cte_is_allowed():
    ok, _ = is_safe_select("WITH t AS (SELECT 1 AS x) SELECT * FROM t")
    assert ok


def test_delete_is_rejected():
    ok, reason = is_safe_select("DELETE FROM bookings WHERE booking_status = 'Cancelled'")
    assert not ok and reason


def test_update_is_rejected():
    ok, _ = is_safe_select("UPDATE bookings SET fare_amount = 0")
    assert not ok


def test_drop_is_rejected():
    ok, _ = is_safe_select("DROP TABLE bookings")
    assert not ok


def test_multiple_statements_rejected():
    ok, _ = is_safe_select("SELECT 1; SELECT 2")
    assert not ok


def test_sneaky_write_inside_select_rejected():
    ok, _ = is_safe_select("SELECT * FROM bookings; DELETE FROM bookings")
    assert not ok


def test_empty_query_rejected():
    ok, _ = is_safe_select("   ")
    assert not ok
