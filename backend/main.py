from fastapi import FastAPI, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, Request, Header, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import users, cases, transfers, logs, messages
from auth import get_password_hash, verify_password, create_access_token
from ai_engine import analyze_image, compress_image, reconstruct_image
from transfer_manager import dtn_transfer_worker, NETWORK_CONFIG
import uuid, os, time
from datetime import datetime

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "Telepathology API is running successfully!", "status": "Healthy"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/uploads/{filename}")
async def get_image(filename: str):
    file_path = f"uploads/{filename}"
    if not os.path.exists(file_path): return FileResponse("uploads/placeholder.jpg")
    return FileResponse(file_path, media_type="image/jpeg")

@app.get("/hospitals")
async def get_hospitals():
    cursor = users.find({"role": "hospital"}, {"username": 1, "_id": 0})
    hospital_list = await cursor.to_list(length=100)
    return [h['username'] for h in hospital_list]

class ConnectionManager:
    def __init__(self): self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket): await websocket.accept(); self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket): 
        if websocket in self.active_connections: self.active_connections.remove(websocket)
    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            try: await connection.send_json(message)
            except: self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/chat/{case_id}")
async def chat_endpoint(websocket: WebSocket, case_id: str):
    await manager.connect(websocket)
    try:
        history = await messages.find({"case_id": case_id}).sort("timestamp", 1).to_list(100)
        for msg in history: await websocket.send_json({"user": msg.get("user"), "text": msg.get("text")})
        while True:
            data = await websocket.receive_json()
            await messages.insert_one({"case_id": case_id, "user": data['user'], "text": data['text'], "timestamp": datetime.now()})
            await manager.broadcast(data)
    except: manager.disconnect(websocket)

class UserAuth(BaseModel): 
    username: str
    password: str
    role: str = "rural"
    hospital_name: str = "General Clinic"

@app.post("/auth/signup")
async def signup(user: UserAuth):
    if await users.find_one({"username": user.username}): raise HTTPException(400, "User exists")
    await users.insert_one({"username": user.username, "password": get_password_hash(user.password), "role": user.role, "hospital_name": user.hospital_name})
    return {"msg": "Created"}

@app.post("/auth/login")
async def login(user: UserAuth):
    db_user = await users.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user['password']): raise HTTPException(401, "Invalid")
    token = create_access_token({"sub": user.username, "role": db_user['role']})
    return {"access_token": token, "role": db_user['role'], "username": db_user['username'], "hospital_name": db_user.get("hospital_name", "")}

@app.post("/upload")
async def upload(
    bg: BackgroundTasks, 
    files: List[UploadFile] = File(...),
    sender: str = Form(...),      
    receiver: str = Form(...),    
    x_upload_start: Optional[str] = Header(None)
):
    processed_batch = []
    os.makedirs("uploads", exist_ok=True)

    real_speed_bps = 5 * 1024 * 1024 
    if x_upload_start:
        try:
            client_start_ms = float(x_upload_start)
            duration_seconds = (time.time() * 1000 - client_start_ms) / 1000
            if duration_seconds < 0.1: duration_seconds = 0.1
            total_batch_size = sum([file.size for file in files]) # approximate
            real_speed_bps = total_batch_size / duration_seconds
        except: pass

    for file in files:
        content = await file.read()
        
        # 1. Pipeline Step 3: Triage (CancerNet)
        diagnosis = analyze_image(content)
        priority = "High" if diagnosis == "Malignant" else "Normal"
        quality = 95 if priority == "High" else 15
        
        # 2. Pipeline Step 2: Compression
        compressed_content = compress_image(content, quality)
        
        # 3. Pipeline Step 6: Reconstruction (ResUNet)
        # We pass the compressed bytes through your AI to restore them
        restored_content = reconstruct_image(compressed_content)
        
        case_id = uuid.uuid4().hex[:6].upper()
        
        with open(f"uploads/{case_id}_original.jpg", "wb") as f: f.write(content)
        with open(f"uploads/{case_id}_compressed.jpg", "wb") as f: f.write(compressed_content)
        
        # Save the AI-Restored version for the Hospital!
        with open(f"uploads/{case_id}_restored.jpg", "wb") as f: f.write(restored_content) 

        processed_batch.append({
            "case_id": case_id, "diagnosis": diagnosis, "priority": priority, 
            "file_size": len(compressed_content), "original_size": len(content),
            "network_speed": real_speed_bps, "sender": sender, "receiver": receiver
        })

    processed_batch.sort(key=lambda x: 0 if x['priority'] == 'High' else 1)

    for case in processed_batch:
        await cases.insert_one({
            "case_id": case['case_id'], "diagnosis": case['diagnosis'], "priority": case['priority'], 
            "timestamp": datetime.now(), "original_size": case['original_size'], "compressed_size": case['file_size'],
            "sender": case['sender'], "receiver": case['receiver']
        })
        await transfers.insert_one({
            "case_id": case['case_id'], "status": "Queued", "progress": 0, "speed": "0 KB/s", 
            "total_chunks": 100, "current_chunk": 0, "stats": {"avg": "0 KB/s", "max": "0 KB/s", "min": "0 KB/s"}
        })
        # PASS SENDER/RECEIVER TO WORKER
        bg.add_task(dtn_transfer_worker, case['case_id'], case['file_size'], case['priority'], case['network_speed'], case['sender'], case['receiver'])
    
    return {"msg": "Batch Processed"}

@app.get("/data")
async def get_data(username: str, role: str):
    if role == "rural": query = {"sender": username}
    else: query = {"receiver": username}  
    
    # FIX: Removed the .limit(20) and increased .to_list() to 1000 so all older cases load
    all_cases = await cases.find(query).sort("timestamp", -1).to_list(1000)
    data = []
    for c in all_cases:
        c["_id"] = str(c["_id"])
        transfer = await transfers.find_one({"case_id": c["case_id"]})
        if transfer:
            transfer["_id"] = str(transfer["_id"])
            c["transfer"] = transfer
        data.append(c)
    return data

# --- UPDATED LOGS ENDPOINT (FILTERED) ---
@app.get("/logs")
async def get_logs(username: str, role: str):
    # Filter logs where:
    # 1. You are the Sender (Rural)
    # 2. You are the Receiver (Hospital)
    query = { 
        "$or": [
            {"sender": username}, 
            {"receiver": username}
        ] 
    }
    
    # FIX: Increased limit from 50 to 1000 to ensure old logs aren't hidden
    l = await logs.find(query).sort("timestamp", -1).to_list(1000)
    for x in l: x["_id"] = str(x["_id"])
    return l

@app.post("/network")
async def set_net(condition: str):
    NETWORK_CONFIG["condition"] = condition
    return {"status": condition}