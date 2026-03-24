from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import get_pipeline_service
from app.errors import PipelineError
from app.models import HealthResponse, TextProcessRequest, TranslationRequest, UserPreferenceUpdate
from app.services.pipeline import PipelineService

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.exception_handler(PipelineError)
async def pipeline_exception_handler(_: Request, exc: PipelineError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse()


@app.post(f"{settings.api_prefix}/users/{{user_id}}/preferences")
async def update_user_preferences(
    user_id: str,
    payload: UserPreferenceUpdate,
    service: PipelineService = Depends(get_pipeline_service),
) -> dict[str, str]:
    service.set_user_language(user_id, payload.preferred_language)
    return {"user_id": user_id, "preferred_language": payload.preferred_language}


@app.post(f"{settings.api_prefix}/text")
async def process_text(
    payload: TextProcessRequest,
    service: PipelineService = Depends(get_pipeline_service),
):
    return await service.process_text(
        user_id=payload.user_id,
        text=payload.text,
        channel="text",
        source_language=payload.source_language,
        preferred_output_language=payload.preferred_output_language,
        include_audio=payload.include_audio,
    )


@app.post(f"{settings.api_prefix}/speech")
async def process_speech(
    user_id: str = Form(...),
    preferred_output_language: str | None = Form(default=None),
    include_audio: bool = Form(default=False),
    audio: UploadFile = File(...),
    service: PipelineService = Depends(get_pipeline_service),
):
    return await service.process_speech(
        user_id=user_id,
        audio=audio,
        preferred_output_language=preferred_output_language,
        include_audio=include_audio,
    )


@app.post(f"{settings.api_prefix}/documents")
async def process_document(
    user_id: str = Form(...),
    preferred_output_language: str | None = Form(default=None),
    include_audio: bool = Form(default=False),
    document: UploadFile = File(...),
    service: PipelineService = Depends(get_pipeline_service),
):
    return await service.process_document(
        user_id=user_id,
        document=document,
        preferred_output_language=preferred_output_language,
        include_audio=include_audio,
    )


@app.post(f"{settings.api_prefix}/translate")
async def translate(
    payload: TranslationRequest,
    service: PipelineService = Depends(get_pipeline_service),
):
    return await service.translate_only(
        text=payload.text,
        source_language=payload.source_language,
        target_language=payload.target_language,
    )
