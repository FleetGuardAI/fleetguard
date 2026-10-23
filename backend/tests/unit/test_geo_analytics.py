import pytest
from datetime import datetime, timezone, timedelta
from utils.geo_analytics import (
    haversine_distance_meters,
    calculate_bearing,
    detect_gaps_and_stops,
    compute_bounding_box,
    downsample_gps_points,
    calculate_comprehensive_analytics,
)


def test_haversine_distance_meters():
    # Dehradun to UPES approx 10km
    d = haversine_distance_meters(30.4061, 77.9693, 30.3165, 78.0322)
    assert 10000 < d < 15000

    # Same point distance is 0
    assert haversine_distance_meters(30.0, 78.0, 30.0, 78.0) == 0.0


def test_calculate_bearing():
    # Due North: lat increases, lon constant -> bearing 0 or 360
    b_north = calculate_bearing(0.0, 0.0, 1.0, 0.0)
    assert round(b_north) == 0 or round(b_north) == 360

    # Due East: lat constant, lon increases -> bearing ~90
    b_east = calculate_bearing(0.0, 0.0, 0.0, 1.0)
    assert 89 <= b_east <= 91


def test_compute_bounding_box():
    pts = [
        {"latitude": 30.1, "longitude": 77.2},
        {"latitude": 30.5, "longitude": 77.8},
        {"latitude": 29.9, "longitude": 77.5},
    ]
    bbox = compute_bounding_box(pts)
    assert bbox == [29.9, 77.2, 30.5, 77.8]
    assert compute_bounding_box([]) is None


def test_detect_gaps_and_stops():
    t0 = datetime(2026, 9, 22, 10, 0, 0, tzinfo=timezone.utc)
    pts = [
        {"latitude": 30.0, "longitude": 77.0, "speed": 10.0, "timestamp": t0},
        {"latitude": 30.001, "longitude": 77.0, "speed": 10.0, "timestamp": t0 + timedelta(seconds=10)},
        # Gap of 30 minutes (> 15 min threshold)
        {"latitude": 30.002, "longitude": 77.0, "speed": 0.0, "timestamp": t0 + timedelta(minutes=30)},
        # Stationary stop for 10 minutes (speed 0)
        {"latitude": 30.002, "longitude": 77.0, "speed": 0.0, "timestamp": t0 + timedelta(minutes=35)},
        {"latitude": 30.002, "longitude": 77.0, "speed": 0.0, "timestamp": t0 + timedelta(minutes=40)},
    ]
    gaps, stops = detect_gaps_and_stops(pts)
    assert len(gaps) == 1
    assert gaps[0]["gap_type"] == "SIGNAL_LOSS"
    assert gaps[0]["duration_minutes"] >= 29.0

    assert len(stops) == 1
    assert stops[0]["duration_minutes"] >= 10.0


def test_downsample_gps_points():
    t0 = datetime(2026, 9, 22, 10, 0, 0, tzinfo=timezone.utc)
    pts = [
        {
            "latitude": 30.0 + i * 0.001,
            "longitude": 77.0 + i * 0.001,
            "speed": 10.0,
            "heading": (i * 10) % 360,
            "timestamp": t0 + timedelta(seconds=i * 10)
        }
        for i in range(100)
    ]
    downsampled = downsample_gps_points(pts, max_points=20)
    assert len(downsampled) <= 20
    # First and last points must be preserved
    assert downsampled[0]["latitude"] == pts[0]["latitude"]
    assert downsampled[-1]["latitude"] == pts[-1]["latitude"]


def test_calculate_comprehensive_analytics():
    t0 = datetime(2026, 9, 22, 10, 0, 0, tzinfo=timezone.utc)
    pts = [
        {"latitude": 30.0, "longitude": 77.0, "speed": 10.0, "timestamp": t0},
        {"latitude": 30.001, "longitude": 77.0, "speed": 15.0, "timestamp": t0 + timedelta(seconds=60)},
        {"latitude": 30.002, "longitude": 77.0, "speed": 12.0, "timestamp": t0 + timedelta(seconds=120)},
    ]
    analytics = calculate_comprehensive_analytics(pts, total_trips=1)
    assert analytics["total_trips"] == 1
    assert analytics["total_recorded_distance_km"] > 0
    assert analytics["average_speed_kmh"] > 0
    assert analytics["max_speed_kmh"] == round(15.0 * 3.6, 1)
    assert analytics["gps_coverage_pct"] == 100.0
