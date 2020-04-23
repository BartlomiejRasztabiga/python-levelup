import pytest
from fastapi.testclient import TestClient
from base64 import b64encode
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


def test_create_patient():
    json_body = {'name': 'Jan', 'surename': 'Kowalski'}
    response = client.post('/patient', json=json_body)

    assert response.status_code == 200
    assert response.json() == {'id': 0, 'patient': {'name': 'Jan', 'surename': 'Kowalski'}}


def test_get_patient():
    # first insert the patient
    json_body = {'name': 'Jan', 'surename': 'Kowalski'}
    response = client.post('/patient', json=json_body)

    inserted_patient = response.json()
    patient_id = inserted_patient['id']

    # then test whether we can retrieve him
    response = client.get(f'/patient/{patient_id}')

    assert response.status_code == 200
    assert response.json() == inserted_patient['patient']

    # test error code when retrieving patient that doesnt exist
    response = client.get('/patient/999')
    assert response.status_code == 204


def test_login_wrong_password():
    auth_string_raw = "test:pass"
    auth_string_encoded = b64encode(bytes(auth_string_raw, "utf-8")).decode("ascii")
    response = client.post('/login', headers={"Authorization": "Basic %s" % auth_string_encoded})

    assert response.status_code == 401


def test_login_no_authorization_header():
    response = client.post('/login')

    assert response.status_code == 403


def test_login_correct_password():
    auth_string_raw = "trudnY:PaC13Nt"
    auth_string_encoded = b64encode(bytes(auth_string_raw, "utf-8")).decode("ascii")
    response = client.post('/login', headers={"Authorization": "Basic %s" % auth_string_encoded})

    assert response.status_code == 302  # redirected to /welcome
