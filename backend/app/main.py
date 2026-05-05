from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .runtime import llm_gateway
from .settings_bridge import apply_structured_settings, normalize_structured_settings
from .store import store
from .harness.routes import router as harness_router


app = FastAPI(
    title="Agent Playground API",
    description="Backend service for agent/workflow/trace playground demos.",
    version="0.1.0",
)

_default_origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "null",
]
# 部署时用 EXTRA_CORS_ORIGINS=https://your-domain.com,https://other.com 追加
import os as _os
_extra = [o.strip() for o in _os.environ.get("EXTRA_CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra,
    # 自动放行所有 *.vercel.app preview / production 域名
    allow_origin_regex=r"^https?://([a-z0-9-]+\.)*vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    store.seed_defaults()
    stored_settings = store.get_app_settings_payload()
    if stored_settings:
        normalized = normalize_structured_settings(stored_settings)
        apply_structured_settings(stored_settings, normalized)
        llm_gateway.refresh_client()


app.include_router(router)
app.include_router(harness_router)
