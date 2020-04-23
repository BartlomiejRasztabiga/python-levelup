import pytest
from fastapi.testclient import TestClient
from base64 import b64encode
from src.main import app

client = TestClient(app)


def test_hello_world():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello World during the coronavirus pandemic!'}


def test_create_patient():
    auth_string_raw = "trudnY:PaC13Nt"
    auth_string_encoded = b64encode(bytes(auth_string_raw, "utf-8")).decode("ascii")
    response = client.post('/login', headers={"Authorization": "Basic %s" % auth_string_encoded})
    assert response.status_code == 302
    print(response.cookies)

    json_body = {'name': 'Jan', 'surename': 'Kowalski'}
    response = client.post('/patient', json=json_body, cookies=response.cookies)

    assert response.status_code == 200
    assert response.json() == {'id': 0, 'patient': {'name': 'Jan', 'surename': 'Kowalski'}}


def test_get_patient():
    auth_string_raw = "trudnY:PaC13Nt"
    auth_string_encoded = b64encode(bytes(auth_string_raw, "utf-8")).decode("ascii")
    response = client.post('/login', headers={"Authorization": "Basic %s" % auth_string_encoded})
    assert response.status_code == 302

    # first insert the patient
    json_body = {'name': 'Jan', 'surename': 'Kowalski'}
    response = client.post('/patient', json=json_body, cookies=response.cookies)

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
