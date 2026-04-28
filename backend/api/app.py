from fastapi import FastAPI

app = FastAPI(title="Docs Checker API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
