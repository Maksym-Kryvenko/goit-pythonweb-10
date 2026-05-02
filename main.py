from fastapi import FastAPI

from src.api import contacts, utils

app = FastAPI(title="Contacts API", version="1.0")

app.include_router(utils.router)
app.include_router(contacts.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)