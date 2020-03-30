import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_hello_world():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello World during the coronavirus pandemic!'}


def test_hello_name():
    name = 'test'
    response = client.get(f'/hello/{name}')
    assert response.status_code == 200
    assert response.json() == {'message': f'Hello {name}!'}
