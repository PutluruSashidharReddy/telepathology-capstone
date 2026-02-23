FROM python:3.10-slim

# Create a non-root user (Required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Copy requirements securely
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force CPU-only PyTorch to prevent memory crashes on the free tier
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy the rest of the backend
COPY --chown=user . .

# Start the server on Hugging Face's default port
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
