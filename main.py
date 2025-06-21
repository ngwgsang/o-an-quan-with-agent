from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Mount thư mục static để phục vụ file css
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cấu hình templates
templates = Jinja2Templates(directory="templates")

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/play", response_class=HTMLResponse)
async def read_play(request: Request):
    return templates.TemplateResponse("play.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Chuyển hướng về trang dashboard làm trang chủ
    return templates.TemplateResponse("dashboard.html", {"request": request})