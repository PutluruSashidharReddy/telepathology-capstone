# Project Rules for Agents

This project is a Telepathology Capstone involving AI-driven image compression, cancer diagnosis, and Delay-Tolerant Networking (DTN).

## DOs
1. **Use Neural Compression:** Always use the `ClinicalEncoder` and `ClinicalDecoder` from `ai_engine.py` for image processing. Do not fallback to standard JPEG/PNG unless explicitly for UI proxying.
2. **Asynchronous Database Operations:** All MongoDB operations must use `motor.motor_asyncio` and be `await`ed. Use the collections defined in `database.py`.
3. **DTN Simulation:** Any file transfer must be routed through the `dtn_transfer_worker` in `transfer_manager.py` to simulate real-world intermittent connectivity.
4. **Hardware Agnostic Loading:** When loading PyTorch models, always use `map_location=DEVICE` where `DEVICE` is defined in `ai_engine.py`.
5. **System Logging:** Log significant events (start of transfer, errors, completion) using the `log_event` function in `transfer_manager.py`.

## DON'Ts
1. **No Synchronous IO in FastAPI:** Avoid using `open()` or `time.sleep()` inside async endpoints. Use `BackgroundTasks` for long-running processes like transfers.
2. **Do Not Hardcode URLs:** Use environment variables (via `.env` and `load_dotenv`) for MongoDB URLs and other configurations.
3. **No Simple Timers for Networking:** Do not simulate networking with just `time.sleep()`. The simulation must account for `NETWORK_CONFIG` and connectivity reliability.
4. **Avoid Global State for Transfers:** Use the `transfers` collection in the database to track the state of ongoing transfers instead of in-memory variables.
