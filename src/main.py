from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

app.counter = 0


class HelloNameResponse(BaseModel):
    message: str


@app.get('/')
def hello_world():
    return {'message': 'Hello World during the coronavirus pandemic!'}


@app.get('/hello/{name}', response_model=HelloNameResponse)
async def hello_name(name: str):
    return HelloNameResponse(message=f'Hello {name}!')


@app.get('/counter')
def counter():
    app.counter += 1
    return {'counter': app.counter}
