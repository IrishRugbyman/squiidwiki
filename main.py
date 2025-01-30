from backend.server import app
from backend.database.database import init_db
import uvicorn

# Initialiser la base de données
init_db(drop_existing=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)