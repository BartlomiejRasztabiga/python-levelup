import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_hello_world():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello World during the coronavirus pandemic!'}


@pytest.mark.parametrize("name", ['Adam', 'Kuba', 'BardzoDlugieImie'])
def test_hello_name(name):
    response = client.get(f'/hello/{name}')
    assert response.status_code == 200
    assert response.json() == {'message': f'Hello {name}!'}


def test_counter():
    # 1st request to increment counter
    response = client.get('/counter')
    assert response.status_code == 200
    assert response.json() == {'counter': 1}

    # 2nd request to increment counter
    response = client.get('/counter')
    assert response.json() == {'counter': 2}


def test_json_echo():
    json_body = {'key': 'value'}
    response = client.post('/json', json=json_body)

    assert response.status_code == 200
    assert response.json() == json_body


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_return_method(method: str):
    response = client.request(method, '/method')

    assert response.status_code == 200
    assert response.json() == {'method': method}
