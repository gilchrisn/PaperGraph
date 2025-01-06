from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import router
import os

app = FastAPI(
    title="Research Paper API",
    description="API for retrieving papers and related information.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Mount the directory with PDFs as a static file route
pdf_directory = os.path.join(os.getcwd(), "resources", "all_papers")
app.mount("/pdfs", StaticFiles(directory=pdf_directory), name="pdfs")

# Include the routes
app.include_router(router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Research Paper API!"}
