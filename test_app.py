import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_utc_33(client):
    lat=48.647428
    long=15.598633
    response = client.get(f'/convert_coordinates?latitude={lat}&longitude={long}')
    assert response.status_code == 500

def test_utc_34(client):
    lat=48.647428
    long=23.598633
    response = client.get(f'/convert_coordinates?latitude={lat}&longitude={long}')
    assert response.status_code == 200
    assert response.json["converted_x"] == 4691599
    assert response.json["converted_y"] == 5393806

def test_utc_35(client):
    lat=50.999929
    long=27.872314
    response = client.get(f'/convert_coordinates?latitude={lat}&longitude={long}')
    assert response.status_code == 200
    assert response.json["converted_x"] == 5561353
    assert response.json["converted_y"] == 5652558

def test_utc_36(client):
    lat=48.582058
    long=30.003662
    response = client.get(f'/convert_coordinates?latitude={lat}&longitude={long}')
    assert response.status_code == 200
    assert response.json["converted_x"] == 6279050
    assert response.json["converted_y"] == 5387594

def test_utc_37(client):
    lat=49.403825
    long=34.024658
    response = client.get(f'/convert_coordinates?latitude={lat}&longitude={long}')
    assert response.status_code == 200
    assert response.json["converted_x"] == 6574482
    assert response.json["converted_y"] == 5475151

def test_utc_38(client):
    lat=48.202710
    long=43.18
    response = client.get(f'/convert_coordinates?latitude={lat}&longitude={long}')
    assert response.status_code == 500