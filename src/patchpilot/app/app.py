from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def greet():
    return {"message":"Hello Patch Pilot", "version":"1.0", "status":"OK", "server_status":"running !"}