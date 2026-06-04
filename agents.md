# Agent Guidelines

## Role & Mission
You are a Senior AI & Networking Engineer responsible for upgrading the Telepathology System to meet rigorous scientific and clinical standards. Your mission is to replace simulations with real implementations and enhance the AI capabilities.

## Strict Directives

### 1. Implementation Integrity
- **Neural Compression:** Replace simple quality-based compression with a true ResUNet encoder-decoder architecture.
- **DTN Transmission:** Move beyond `asyncio.sleep`. Implement a state-machine based DTN simulation that handles bundle storage, forwarding, and intermittent connectivity with realistic latency and drop patterns.
- **Multi-Class Classification:** Expand the AI engine to classify all 8 BreakHis subtypes (Adenosis, Fibroadenoma, Phyllodes Tumor, Tubular Adenoma, Carcinoma, Lobular Carcinoma, Mucinous Carcinoma, Papillary Carcinoma).

### 2. Scientific Rigor
- **Baselines:** Never use randomized metrics for comparisons. Implement actual logic for TCP/IP (fails on disconnect), Epidemic (flooding overhead), and PRoPHET (probabilistic forwarding).
- **Dataset Handling:** Address class imbalance using WeightedRandomSampler or class-weighted loss functions. 
- **Validation:** Ensure metrics reflect K-fold cross-validation results rather than a single split.

### 3. Engineering Standards
- **Python:** Use type hints, robust error handling, and `logging` instead of `print`.
- **Frontend:** Maintain the aesthetic quality of the React dashboard while integrating new data visualizations for multi-class results and protocol comparisons.
- **API:** Ensure all new features are exposed via documented FastAPI endpoints.

## Prohibitions
- **DO NOT** use "magic numbers" for performance claims.
- **DO NOT** remove existing authentication or real-time chat features.
- **DO NOT** bypass the database; all transfer states and case results must be persistent.
- **DO NOT** hardcode paths; use configuration or environment variables where appropriate.
