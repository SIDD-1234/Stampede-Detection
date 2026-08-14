uvicorn[standard] pulls in websockets/uvloop for perf — you can drop the standalone websockets if you don't need it outside FastAPI.
python-multipart needed for file uploads (video upload endpoint later).
pydantic-settings for the shared config file in step 5.
Put requirements.txt inside ai_pipeline/ (or root, your call) and .gitignore the venv/ folder.
