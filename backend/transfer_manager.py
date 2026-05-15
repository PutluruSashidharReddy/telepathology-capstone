import asyncio
import time
import random
from datetime import datetime
from database import transfers, logs
import torch
from ai_engine import LinkQualityLSTM, DEVICE

NETWORK_CONFIG = { "condition": "Real-Time", "active_high_priority": False, "paused_cases": set() }

# Initialize the predictive model
predictive_model = LinkQualityLSTM().to(DEVICE)
predictive_model.eval()

def get_dynamic_compression_ratio(recent_network_history=None):
    """
    Predicts network drops to adjust compression.
    Failsafes to STANDARD_COMPRESSION if data is missing or model fails.
    """
    try:
        if recent_network_history is None:
            return "STANDARD_COMPRESSION"

        with torch.no_grad():
            predicted_bandwidth = predictive_model(recent_network_history.to(DEVICE))
            
        # If predicted bandwidth drops below 100 KB/s, aggressively compress
        if predicted_bandwidth.item() < 100.0: 
            return "HIGH_COMPRESSION"
        else:
            return "STANDARD_COMPRESSION"
            
    except Exception as e:
        print(f"LSTM Prediction failed, defaulting to standard: {e}")
        return "STANDARD_COMPRESSION"


# 1. UPDATE LOG FUNCTION TO ACCEPT USER INFO
async def log_event(msg, type="info", sender=None, receiver=None):
    await logs.insert_one({
        "message": msg, 
        "type": type, 
        "timestamp": datetime.now(),
        "sender": sender,      # Save who sent it
        "receiver": receiver   # Save who it's for
    })

# 2. THE NEW DTN STORE-AND-FORWARD WORKER
async def dtn_transfer_worker(case_id, total_size, priority, real_network_speed, sender, receiver):
    chunk_size = 1024 * 50 
    total_chunks = (total_size // chunk_size) + 1
    current_chunk = 0
    speed_readings = []
    connection_drops = 0
    
    seconds_per_chunk = chunk_size / real_network_speed
    if priority == "High": seconds_per_chunk /= 1.5 

    await log_event(f"🚀 Started DTN Transfer: Case {case_id} -> {receiver}", "start", sender, receiver)

    # THE DTN LOOP
    while current_chunk < total_chunks:
        # 1. Simulate Rural Network Reliability based on your React UI settings
        reliability = 0.95 if NETWORK_CONFIG.get("condition") == "Real-Time" else 0.60
        is_connected = random.random() <= reliability

        # 2. Simulate the Drop and Store-and-Forward Queue
        if not is_connected:
            connection_drops += 1
            await log_event(f"⚠️ Network Drop! DTN Storing chunk {current_chunk + 1} locally.", "warning", sender, receiver)
            
            # Update UI to show the drop
            await transfers.update_one({"case_id": case_id}, {
                "$set": { "status": "Network Dropped - Stored 📦", "speed": "0 KB/s" }
            })
            
            # Wait for connection to return
            await asyncio.sleep(random.uniform(1.0, 3.0)) 
            
            await log_event(f"🔄 Connection Restored! Forwarding chunk {current_chunk + 1}...", "info", sender, receiver)
            continue # Retry sending the exact same chunk (Store-and-Forward)

        # 3. Network is Up - Send Chunk
        start_time = time.perf_counter()
        await asyncio.sleep(seconds_per_chunk)
        
        duration = time.perf_counter() - start_time
        if duration <= 0: duration = 0.001
        inst_speed = (chunk_size / 1024) / duration 
        speed_readings.append(inst_speed)
        
        current_chunk += 1
        pct = int((current_chunk / total_chunks) * 100)
        
        # Update MongoDB for the React UI to read
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
    await log_event(f"✅ Finished: Case {case_id} (Handled {connection_drops} drops)", "success", sender, receiver)