from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
	return {"message": "BinOrWin APİ is running! Hello from Raspberry Pi!"}
