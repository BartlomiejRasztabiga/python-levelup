from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

app.counter = 0
app.next_patient_id = 0


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


class PatientResponse(BaseModel):
    id: int
    patient: PatientRequest


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


@app.post('/json', response_model=JsonEchoResponse)
def json_echo(req: JsonEchoRequest):
    return JsonEchoResponse(key=req.key)


@app.api_route('/method', methods=['GET', 'POST', 'PUT', 'DELETE'])
def return_method(request: Request):
    return HttpMethodResponse(method=request.method)


@app.post('/patient', response_model=PatientResponse)
def create_patient(req: PatientRequest):
    app.next_patient_id += 1
    return PatientResponse(id=app.next_patient_id, patient=PatientRequest(name=req.name, surename=req.surename))
