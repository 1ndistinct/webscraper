"""
A mock site used to test web scraping
"""

import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


app = FastAPI(
    title="Mock Website",
    description="Mock website for webscraper testing",
    version="1.0",
)
current_dir = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=f"{current_dir}/templates")


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    """
    Website homepage
    """
    return templates.TemplateResponse(request, "homepage.html")


@app.get("/about", response_class=HTMLResponse)
@app.get("/blog", response_class=HTMLResponse)
@app.get("/contact", response_class=HTMLResponse)
def nextpage(request: Request):
    """
    Website other routes
    """
    return templates.TemplateResponse(request, "nextpage.html")


@app.get("/payments", response_class=HTMLResponse)
def finalpage(request: Request):
    """
    Website final page
    """
    return templates.TemplateResponse(request, "finalpage.html")
