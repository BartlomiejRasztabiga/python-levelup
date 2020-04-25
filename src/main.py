import uuid
import base64

from functools import wraps

from fastapi.security import HTTPBasic

from typing import Optional

from pydantic import BaseModel

from fastapi import Depends, FastAPI, HTTPException, Cookie

from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param

from starlette import status
from starlette.responses import RedirectResponse, Response
from starlette.requests import Request

from fastapi.templating import Jinja2Templates

app = FastAPI()
security = HTTPBasic()
app.sessions = {}

app.next_patient_id = 0
app.patients = {}


class PatientRequest(BaseModel):
    name: str
    surname: str


class PatientResponse(BaseModel):
    name: str
    surname: str


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
                    status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return param


basic_auth = BasicAuth(auto_error=False)
fake_users_db = {'trudnY': 'PaC13Nt'}
templates = Jinja2Templates(directory="templates")


def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        session_id = kwargs['SESSIONID']

        if session_id is not None and session_id in app.sessions:
            return f(*args, **kwargs)
        else:
            response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
            return response

    return wrapper


def authenticate_user(users_db, username, password):
    if username in users_db and users_db[username] == password:
        return username
    return None


@app.get('/welcome')
@authenticate
def welcome(request: Request, SESSIONID: str = Cookie(None)):
    user = app.sessions[SESSIONID]
    username = user['username']

    return templates.TemplateResponse("welcome.html", {'request': request, 'username': username})


@app.post('/login')
def login(auth: BasicAuth = Depends(basic_auth)):
    if not auth:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=403)
        return response

    try:
        decoded = base64.b64decode(auth).decode("ascii")
        username, _, password = decoded.partition(":")
        user = authenticate_user(fake_users_db, username, password)
        if user is None:
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        session_id = str(uuid.uuid4())
        app.sessions[session_id] = {'username': user}

        response = RedirectResponse(url='/welcome', status_code=status.HTTP_302_FOUND)
        response.set_cookie('SESSIONID', value=str(session_id), httponly=True, max_age=1800, expires=1800)
        return response

    except Exception:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        return response


@app.post('/logout')
def logout(SESSIONID: str = Cookie(None)):
    if SESSIONID is not None and SESSIONID in app.sessions:
        app.sessions.pop(SESSIONID)
        response = RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)
        return response
    else:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        response.set_cookie('SESSIONID', value='', httponly=True, max_age=0, expires=0)
        return response


@app.get('/patient')
@authenticate
def get_patients(SESSIONID: str = Cookie(None)):
    return app.patients


@app.post('/patient')
@authenticate
def create_patient(req: PatientRequest, SESSIONID: str = Cookie(None)):
    patient = req
    app.next_patient_id += 1
    app.patients[app.next_patient_id] = patient
    response = RedirectResponse(url='/patient/{}'.format(app.next_patient_id), status_code=status.HTTP_302_FOUND)
    return response


@app.get('/patient/{patient_id}', response_model=PatientResponse)
@authenticate
def get_patient(patient_id: int, SESSIONID: str = Cookie(None)):
    if patient_id not in app.patients:
        raise HTTPException(status_code=204)
    else:
        return app.patients[patient_id]


@app.delete('/patient/{patient_id}')
@authenticate
def delete_patient(patient_id: int, SESSIONID: str = Cookie(None)):
    if patient_id not in app.patients:
        raise HTTPException(status_code=200)
    else:
        del app.patients[patient_id]
        return Response(status_code=200)
