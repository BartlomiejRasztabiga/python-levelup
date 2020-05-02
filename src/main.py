import json
import secrets
import sqlite3

import aiosqlite
from typing import Dict, Optional

from fastapi import Depends, FastAPI, Response, status, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyCookie, HTTPBasic, HTTPBasicCredentials
from jose import jwt
from pydantic import BaseModel
from starlette.responses import RedirectResponse


class Patient(BaseModel):
    name: str
    surname: str


class Album(BaseModel):
    title: str
    artist_id: int


class DaftAPI(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter: int = 0
        self.storage: Dict[int, Patient] = {}
        self.security = HTTPBasic(auto_error=False)
        self.secret_key = "kluczyk"
        self.API_KEY = "session"
        self.cookie_sec = APIKeyCookie(name=self.API_KEY, auto_error=False)
        self.templates = Jinja2Templates(directory="templates")


app = DaftAPI()


def is_logged(session: str = Depends(app.cookie_sec), silent: bool = False):
    try:
        payload = jwt.decode(session, app.secret_key)
        return payload.get("magic_key")
    except Exception:
        pass

    if silent:
        return False

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def authenticate(credentials: Optional[HTTPBasicCredentials] = Depends(app.security)):
    if not credentials:
        return False

    correct_username = secrets.compare_digest(credentials.username, "trudnY")
    correct_password = secrets.compare_digest(credentials.password, "PaC13Nt")

    if not (correct_username and correct_password):
        return False
    return True


@app.on_event("startup")
async def startup():
    app.db_connection = await aiosqlite.connect('chinook.db')


@app.on_event("shutdown")
async def shutdown():
    await app.db_connection.close()


@app.get("/tracks")
async def get_tracks(page: int = 0, per_page: int = 10):
    app.db_connection.row_factory = sqlite3.Row
    cursor = await app.db_connection.execute("SELECT * FROM tracks ORDER BY TrackId LIMIT :per_page OFFSET :offset ",
                                             {'per_page': per_page, 'offset': page * per_page})
    tracks = await cursor.fetchall()
    return tracks


@app.get("/tracks/composers")
async def get_tracks_by_composer(composer_name: str):
    # app.db_connection.row_factory = sqlite3.Row
    app.db_connection.row_factory = lambda cursor, x: x[0]
    cursor = await app.db_connection.execute(
        "SELECT Name FROM tracks WHERE Composer LIKE :composer_name ORDER BY Name",
        {'composer_name': '%' + composer_name + '%'})
    tracks = await cursor.fetchall()
    if len(tracks) == 0:
        error = {'detail': {'error': 'No composer {} found'.format(composer_name)}}
        response = Response(status_code=404, content=json.dumps(error))
        return response
    return tracks


@app.post("/albums")
async def create_album(album: Album):
    app.db_connection.row_factory = sqlite3.Row
    cursor = await app.db_connection.execute("SELECT ArtistId FROM artists WHERE ArtistId = :artist_id",
                                             {'artist_id': album.artist_id})
    artist = await cursor.fetchone()

    if artist is None:
        error = {'detail': {'error': 'No artist with id {} found'.format(album.artist_id)}}
        response = Response(status_code=404, content=json.dumps(error))
        return response

    cursor = await app.db_connection.execute("INSERT INTO albums (Title, ArtistId) VALUES(:title, :artist_id)",
                                             {'title': album.title, 'artist_id': album.artist_id})
    await app.db_connection.commit()
    response = Response(status_code=201, content=json.dumps({
        'AlbumId': cursor.lastrowid,
        'Title': album.title,
        'ArtistId': album.artist_id
    }))
    return response


@app.get("/albums/{album_id}")
async def get_album(album_id: int):
    app.db_connection.row_factory = sqlite3.Row
    cursor = await app.db_connection.execute("SELECT * FROM albums WHERE AlbumId = :album_id ",
                                             {'album_id': album_id})
    album = await cursor.fetchone()
    return album


@app.get("/")
def read_root():
    return {"message": "Hello World during the coronavirus pandemic!"}


@app.get("/welcome")
def welcome(request: Request, is_logged: bool = Depends(is_logged)):
    return app.templates.TemplateResponse(
        "welcome.html", {"request": request, "user": "trudnY"}
    )


@app.post("/login")
async def login_basic(auth: bool = Depends(authenticate)):
    if not auth:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        return response

    response = RedirectResponse(url="/welcome")
    token = jwt.encode({"magic_key": True}, app.secret_key)
    response.set_cookie("session", token)
    return response


@app.post("/logout")
async def logout(is_logged: bool = Depends(is_logged)):
    response = RedirectResponse(url="/")
    response.delete_cookie("session")
    return response


@app.post("/patient")
def add_patient(patient: Patient, is_logged: bool = Depends(is_logged)):
    app.storage[app.counter] = patient
    response = RedirectResponse(url=f"/patient/{app.counter}")
    app.counter += 1
    return response


@app.get("/patient")
def show_patients(is_logged: bool = Depends(is_logged)):
    return app.storage


@app.get("/patient/{pk}")
def show_patient(pk: int, is_logged: bool = Depends(is_logged)):
    if pk in app.storage:
        return app.storage.get(pk)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/patient/{pk}")
def delte_patient(pk: int, is_logged: bool = Depends(is_logged)):
    if pk in app.storage:
        del app.storage[pk]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
