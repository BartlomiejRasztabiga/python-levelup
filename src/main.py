import secrets
import uuid

from fastapi.security import HTTPBasic

from starlette import status

from typing import Optional
import base64

from pydantic import BaseModel

from fastapi import Depends, FastAPI, HTTPException

from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param

from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, Response
from starlette.requests import Request

app = FastAPI()
security = HTTPBasic()

app.counter = 0
app.next_patient_id = -1
app.patients = {}
app.sessions = {}


class HelloNameResponse(BaseModel):
    message: str


class JsonEchoRequest(BaseModel):
    key: str


class JsonEchoResponse(BaseModel):
    key: str


class HttpMethodResponse(BaseModel):
    method: str


class PatientRequest(BaseModel):
    name: str
    surename: str


class CreatePatientResponse(BaseModel):
    id: int
    patient: PatientRequest


class PatientResponse(BaseModel):
    name: str
    surename: str


class BasicAuth(SecurityBase):
    def __init__(self, scheme_name: str = None, auto_error: bool = True):
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "basic":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return param


basic_auth = BasicAuth(auto_error=False)
fake_users_db = {'trudnY': 'PaC13Nt'}


def authenticate_user(users_db, username, password):
    if username in users_db and users_db[username] == password:
        return username
    return None


@app.get('/')
def hello_world():
    return {'message': 'Hello World during the coronavirus pandemic!'}


@app.get('/welcome')
def welcome():
    return {'message': 'Welcome!'}


@app.post('/login')
def authenticate(auth: BasicAuth = Depends(basic_auth)):
    if not auth:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=403)
        return response

    try:
        decoded = base64.b64decode(auth).decode("ascii")
        username, _, password = decoded.partition(":")
        user = authenticate_user(fake_users_db, username, password)
        if user is None:
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        session_id = uuid.uuid4()
        app.sessions[session_id] = {'username': user}

        response = RedirectResponse(url='/welcome', status_code=status.HTTP_302_FOUND)
        response.set_cookie('SESSIONID', value=str(session_id), httponly=True, max_age=1800, expires=1800)
        return response

    except Exception:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        return response


@app.get('/hello/{name}', response_model=HelloNameResponse)
async def hello_name(name: str):
    return HelloNameResponse(message=f'Hello {name}!')


@app.get('/counter')
def counter():
    app.counter += 1
    return {'counter': app.counter}


@app.post('/json', response_model=JsonEchoResponse)
def json_echo(req: JsonEchoRequest):
    return JsonEchoResponse(key=req.key)


@app.api_route('/method', methods=['GET', 'POST', 'PUT', 'DELETE'])
def return_method(request: Request):
    return HttpMethodResponse(method=request.method)


@app.post('/patient', response_model=CreatePatientResponse)
def create_patient(req: PatientRequest):
    app.next_patient_id += 1
    patient = PatientRequest(name=req.name, surename=req.surename)
    app.patients[app.next_patient_id] = patient
    return CreatePatientResponse(id=app.next_patient_id, patient=patient)


@app.get('/patient/{patient_id}', response_model=PatientResponse)
def get_patient(patient_id: int):
    if patient_id not in app.patients:
        raise HTTPException(status_code=204)
    else:
        return app.patients[patient_id]
