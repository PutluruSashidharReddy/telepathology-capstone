import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables to get the MongoDB URL securely
load_dotenv()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

async def calculate_dtn_metrics():
    print("📊 Connecting to MongoDB to extract DTN Metrics...\n")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.telepathology_db

    # 1. Transmission Success Rate
    total_transfers = await db.transfers.count_documents({})
    completed_transfers = await db.transfers.count_documents({"status": {"$regex": "Completed"}})
    
    success_rate = (completed_transfers / total_transfers) * 100 if total_transfers > 0 else 0
    print(f"📡 1. Transmission Success Rate: {success_rate:.2f}% ({completed_transfers}/{total_transfers} successful)")

    # 2. Average Throughput
    completed_docs = await db.transfers.find({"status": {"$regex": "Completed"}}).to_list(None)
    total_throughput = 0
    valid_speeds = 0
    
    for doc in completed_docs:
        avg_speed_str = doc.get("stats", {}).get("avg", "0 KB/s")
        try:
            # Extract number from string like "125 KB/s"
            speed_val = float(avg_speed_str.replace(" KB/s", ""))
            if speed_val > 0:
                total_throughput += speed_val
                valid_speeds += 1
        except:
            pass
            
    avg_throughput = total_throughput / valid_speeds if valid_speeds > 0 else 0
    print(f"🚀 2. Average Network Throughput: {avg_throughput:.2f} KB/s")

    # 3. Overall Compression Savings
    cases_docs = await db.cases.find({}).to_list(None)
    total_original = sum([c.get("original_size", 0) for c in cases_docs if c.get("original_size")])
    total_compressed = sum([c.get("compressed_size", 0) for c in cases_docs if c.get("compressed_size")])
    
    if total_original > 0:
        savings = (1 - (total_compressed / total_original)) * 100
        print(f"🗜️ 3. Average AI Compression Savings: {savings:.2f}%")
        print(f"   - Total Original Data: {total_original / (1024*1024):.2f} MB")
        print(f"   - Total Transmitted Data: {total_compressed / (1024*1024):.2f} MB")

    # 4. Average Bundle Delay (End-to-End Latency)
    # Calculates the exact time from "Queue" to "Completed" using system logs
    start_logs = await db.system_logs.find({"type": "start"}).to_list(None)
    total_delay = 0
    delay_count = 0
    
    for start_log in start_logs:
        msg = start_log.get("message", "")
        if "Case" in msg:
            try:
                # Extract the 6-character case ID from the log message
                case_id = msg.split("Case ")[1].split(" ")[0]
                # Find matching success log for this specific case
                success_log = await db.system_logs.find_one({"type": "success", "message": {"$regex": case_id}})
                
                if success_log:
                    delay = (success_log["timestamp"] - start_log["timestamp"]).total_seconds()
                    total_delay += delay
                    delay_count += 1
            except:
                continue
                
    avg_delay = total_delay / delay_count if delay_count > 0 else 0
    print(f"⏱️ 4. Average Bundle Delay (End-to-End Latency): {avg_delay:.2f} seconds\n")

if __name__ == "__main__":
    asyncio.run(calculate_dtn_metrics())