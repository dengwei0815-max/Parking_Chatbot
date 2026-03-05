from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import os

app = FastAPI()

RESERVATION_FILE = "confirmed_reservations.txt"
API_KEY = os.environ.get("MCP_API_KEY", "secret123")

@app.post("/process_reservation")
async def process_reservation(request: Request):
    """
    Receives confirmed reservation and writes to file.
    Secured by API key.
    """
    if request.headers.get("x-api-key") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    name = data.get("name")
    car_number = data.get("car_number")
    period = data.get("period")
    approval_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not all([name, car_number, period]):
        raise HTTPException(status_code=400, detail="Missing reservation fields")

    entry = f"{name} | {car_number} | {period} | {approval_time}\n"
    with open(RESERVATION_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    return JSONResponse(content={"message": "Reservation processed", "entry": entry})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)