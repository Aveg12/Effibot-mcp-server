from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import json
from pathlib import Path
from urllib.parse import urlencode

app = FastAPI()

# Serve the dashboard from the public folder
app.mount("/dashboard", StaticFiles(directory="public", html=True), name="dashboard")

# Token storage
TOKEN_FILE = Path("token.json")

def save_token_to_file(token: str):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token}, f)

def load_token_from_file() -> str | None:
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("token")
    return None

# Schema for token request
class APIKeyInput(BaseModel):
    api_key: str

@app.post("/auth/token")
async def get_token(data: APIKeyInput):
    url = "https://iam.test.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": data.api_key,
    })

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid API key")
            token_data = response.json()
            token = token_data.get("access_token")
            if not token:
                raise HTTPException(status_code=500, detail="Token not found in response")
            save_token_to_file(token)
            return {"message": "Token saved", "token": token}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Backend error: {str(e)}")

@app.get("/auth/check")
def check_token():
    token = load_token_from_file()
    return {"authenticated": bool(token)}

# Tool: Volumes (example)
@app.post("/call/volumes")
async def volumes_tool():
    token = load_token_from_file()
    if not token:
        raise HTTPException(status_code=401, detail="You must authenticate first")
    
    url = "https://c-01.private.eu-de.link.satellite.cloud.ibm.com:33233/v1/volumes"
    params = {
        "instance_crn": "crn:v1:staging:public:software-defined-storage:satloc_dal_cs4d3u52003pfi9feq00:a/3faf73b8d12b47fa6ce87494f8ae7686:7d61cc2f-e772-4c46-bd5f-de44fd67bf77::"
    }

    headers = {
        "Authorization": token, 
        "IBM-API-Version": "2025-02-01",
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            print('test', response)
            if response.status_code != 200:
                return {"error": f"Failed to fetch volumes: {response.status_code}"}
            return {"volumes": response.json()}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error calling backend: {str(e)}")
