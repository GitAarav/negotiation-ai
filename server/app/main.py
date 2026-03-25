import json
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from app.services.parser_service import parse_document
from app.services.twilio_flow import (
    build_twiml_response,
    get_twilio_config_status,
    handle_incoming_message,
    send_start_message,
)


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


@app.get("/twilio/config")
def twilio_config():
    return get_twilio_config_status()


@app.post("/twilio/start")
def twilio_start(to_number: str | None = Form(default=None)):
    try:
        return send_start_message(to_number=to_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/twilio/webhook")
async def twilio_webhook(
    From: str = Form(default=""),
    Body: str = Form(default=""),
):
    reply = handle_incoming_message(From, Body)
    return Response(content=build_twiml_response(reply), media_type="application/xml")


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(
    From: str = Form(default=""),
    Body: str = Form(default=""),
):
    reply = handle_incoming_message(From, Body)
    return Response(content=build_twiml_response(reply), media_type="application/xml")
