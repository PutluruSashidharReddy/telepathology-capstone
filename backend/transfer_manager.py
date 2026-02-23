import asyncio
import time
from datetime import datetime
from database import transfers, logs

NETWORK_CONFIG = { "condition": "Real-Time", "active_high_priority": False, "paused_cases": set() }

# 1. UPDATE LOG FUNCTION TO ACCEPT USER INFO
async def log_event(msg, type="info", sender=None, receiver=None):
    await logs.insert_one({
        "message": msg, 
        "type": type, 
        "timestamp": datetime.now(),
        "sender": sender,      # Save who sent it
        "receiver": receiver   # Save who it's for
    })

# 2. UPDATE WORKER SIGNATURE
async def dtn_transfer_worker(case_id, total_size, priority, real_network_speed, sender, receiver):
    chunk_size = 1024 * 50 
    total_chunks = (total_size // chunk_size) + 1
    current_chunk = 0
    speed_readings = []
    
    seconds_per_chunk = chunk_size / real_network_speed
    if priority == "High": seconds_per_chunk /= 1.5 

    # PASS SENDER/RECEIVER TO LOGS
    await log_event(f"🚀 Started: Case {case_id} -> {receiver}", "start", sender, receiver)

    while current_chunk < total_chunks:
        start_time = time.perf_counter()
        await asyncio.sleep(seconds_per_chunk)
        
        duration = time.perf_counter() - start_time
        if duration <= 0: duration = 0.001
        inst_speed = (chunk_size / 1024) / duration 
        speed_readings.append(inst_speed)
        
        current_chunk += 1
        pct = int((current_chunk / total_chunks) * 100)
        
        if current_chunk % 5 == 0 or current_chunk == total_chunks:
            await transfers.update_one({"case_id": case_id}, {
                "$set": { 
                    "current_chunk": current_chunk, "total_chunks": total_chunks, 
                    "status": "Sending 📡", "speed": f"{int(inst_speed)} KB/s", "progress": pct 
                }
            })

    # FINAL LOG
    avg_spd = sum(speed_readings) / len(speed_readings) if speed_readings else 0
    
    await transfers.update_one({"case_id": case_id}, {
        "$set": { 
            "status": "Completed ✅", "progress": 100, "speed": "0 KB/s",
            "stats": { "avg": f"{int(avg_spd)} KB/s", "max": "0 KB/s", "min": "0 KB/s" }
        }
    })
    await log_event(f"✅ Finished: Case {case_id}", "success", sender, receiver)