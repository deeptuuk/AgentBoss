"""FastAPI registration website for AgentBoss."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from itsdangerous import URLSafeSerializer

from web.db import UserDB
from web.auth import register_user, verify_password, decrypt_nsec


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def create_app() -> FastAPI:
    app = FastAPI(title="AgentBoss Registration")

    db_path = os.environ.get("AGENTBOSS_WEB_DB", "agentboss_users.db")
    whitelist_path = os.environ.get("AGENTBOSS_WHITELIST", "/etc/agentboss/whitelist.txt")
    server_key = os.environ.get("AGENTBOSS_SERVER_KEY", "agentboss-default-key-change-in-prod")

    db = UserDB(db_path)
    db.init_db()

    serializer = URLSafeSerializer(server_key)

    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    if template_dir.exists():
        templates = Jinja2Templates(directory=str(template_dir))
    else:
        templates = None

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def _get_session_user(request: Request) -> dict | None:
        token = request.cookies.get("session")
        if not token:
            return None
        try:
            user_id = serializer.loads(token)
            return db.get_user_by_id(user_id)
        except Exception:
            return None

    # ── API routes ──

    @app.post("/api/register")
    def api_register(req: RegisterRequest):
        try:
            result = register_user(
                db=db,
                username=req.username,
                email=req.email,
                password=req.password,
                whitelist_path=whitelist_path,
                server_key=server_key,
            )
            return {"npub": result["npub"], "nsec": result["nsec"]}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/login")
    def api_login(req: LoginRequest, response: Response):
        user = db.get_user_by_username(req.username)
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = serializer.dumps(user["id"])
        response.set_cookie("session", token, httponly=True)
        return {"ok": True, "npub": user["npub"]}

    @app.get("/api/me")
    def api_me(request: Request):
        user = _get_session_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not logged in")
        return {
            "username": user["username"],
            "email": user["email"],
            "npub": user["npub"],
            "created_at": user["created_at"],
        }

    @app.get("/api/key")
    def api_key(request: Request):
        user = _get_session_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not logged in")
        nsec = decrypt_nsec(user["nsec_encrypted"], server_key)
        return {"nsec": nsec, "npub": user["npub"]}

    # ── HTML routes ──

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        if templates:
            return templates.TemplateResponse("register.html", {"request": request})
        return HTMLResponse("<h1>AgentBoss</h1><p>Registration website</p>")

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        user = _get_session_user(request)
        if not user:
            return HTMLResponse("<p>Please login first</p>", status_code=401)
        if templates:
            return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
        return HTMLResponse(f"<p>Welcome {user['username']}</p>")

    return app
