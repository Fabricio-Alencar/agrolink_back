from fastapi import FastAPI

app = FastAPI(title="AgroLink API")


@app.get("/")
def root():
    return {"message": "AgroLink API funcionando!"}
