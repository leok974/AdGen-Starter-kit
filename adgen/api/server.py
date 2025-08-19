import os
from main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))  # Cloud Run uses 8080; we override in dev
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
