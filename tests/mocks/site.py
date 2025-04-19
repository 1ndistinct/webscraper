"""
A mock site used to test web scraping
"""

from fastapi import FastAPI


app = FastAPI(
    title="Mock Website",
    description="Mock website for webscraper testing",
    version="1.0",
)


@app.get("/")
def homepage():
    """
    Website homepage
    """
    return {"success": "home"}


@app.get("/next")
def nextpage():
    """
    Website nextpage
    """
    return {"success": "next"}
