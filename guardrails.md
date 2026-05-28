# Project Guardrails

These guardrails ensure that new changes do not break existing core functionality.

## 1. AI Engine Integrity
- **Model Compatibility:** Any changes to `CancerNet`, `ClinicalEncoder`, or `ClinicalDecoder` architectures must be verified against existing weights in the `models/` directory. If architecture changes, version the model files.
- **Normalization Consistency:** Standard normalization `[0.485, 0.456, 0.406], [0.229, 0.224, 0.225]` must be maintained for `analyze_image` to ensure diagnostic accuracy.

## 2. Transmission & Networking
- **Baseline Comparison:** The `generate_baseline_metrics` function must be called at the end of every transfer to maintain comparative data against TCP/IP, Epidemic, and PRoPHET.
- **Store-and-Forward:** The logic in `dtn_transfer_worker` that handles `is_connected = False` (network drops) must not be removed, as it is central to the DTN value proposition.

## 3. Database Schema
- **Case Tracking:** The `cases` and `transfers` collections must remain linked via `case_id`. Do not change this identifier type or name.
- **Status Updates:** The frontend relies on specific status strings like `"Network Dropped - Stored 📦"`, `"Sending 📡"`, and `"Completed ✅"`. Changing these will break the UI.

## 4. API Standards
- **CORS:** Ensure `CORSMiddleware` remains configured to allow communication with the React frontend.
- **Upload Pipeline:** The sequence: `analyze_image` -> `compress_image` -> `reconstruct_image` -> `BackgroundTasks(dtn_transfer_worker)` is the verified clinical pipeline and should be preserved.
