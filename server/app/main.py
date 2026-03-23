import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.services.parser_service import parse_document


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/parse")
async def parse(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = parse_document(file.filename, content, file.content_type)

        print("\n--- PARSED RESPONSE START ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("--- PARSED RESPONSE END ---\n")

        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/")
def root():
    return {"message": "API running"}
