from fastapi import FastAPI

app = FastAPI()


@app.get('/')
def hello_world():
    return {'message': 'Hello World during the coronavirus pandemic!'}


@app.get('/hello/{name}')
async def hello_name(name: str):
    return {'message': f'Hello {name}!'}
