import os
import io
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# Use GPU if available, else CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 AI Engine loading on: {DEVICE.upper()}")

# ==========================================
# 1. MODEL ARCHITECTURES
# ==========================================

# --- Classification (CancerNet) ---
class SE_Block(nn.Module):
    def __init__(self, channel, reduction=16):
        super(SE_Block, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid()
        )
    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)

class CancerNet(nn.Module):
    def __init__(self):
        super(CancerNet, self).__init__()
        self.base = models.resnet50(weights=None) 
        self.layer0 = nn.Sequential(self.base.conv1, self.base.bn1, self.base.relu, self.base.maxpool)
        self.layer1=self.base.layer1; self.layer2=self.base.layer2; self.layer3=self.base.layer3; self.layer4=self.base.layer4
        self.attention = SE_Block(2048)
        self.avgpool = self.base.avgpool
        self.fc = nn.Sequential(nn.Linear(2048, 512), nn.ReLU(), nn.Dropout(0.4), nn.Linear(512, 2))
    def forward(self, x):
        x=self.layer0(x); x=self.layer1(x); x=self.layer2(x); x=self.layer3(x); x=self.layer4(x)
        x=self.attention(x); x=self.avgpool(x); x=torch.flatten(x, 1)
        return self.fc(x)

# --- Neural Compression (Encoder) ---
class NeuralEncoder(nn.Module):
    def __init__(self):
        super(NeuralEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(32, 16, kernel_size=3, stride=2, padding=1), nn.ReLU()
        )
    def forward(self, x):
        return self.encoder(x)

# --- Neural Decompression (Decoder) ---
class NeuralDecoder(nn.Module):
    def __init__(self):
        super(NeuralDecoder, self).__init__()
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(16, 32, kernel_size=3, stride=2, padding=1, output_padding=1), nn.ReLU(),
            nn.ConvTranspose2d(32, 16, kernel_size=3, stride=2, padding=1, output_padding=1), nn.ReLU(),
            nn.ConvTranspose2d(16, 3, kernel_size=3, stride=2, padding=1, output_padding=1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.decoder(x)

# --- Predictive Link Quality (LSTM) ---
class LinkQualityLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_layer_size=50, output_size=1):
        super().__init__()
        self.hidden_layer_size = hidden_layer_size
        self.lstm = nn.LSTM(input_size, hidden_layer_size, batch_first=True)
        self.linear = nn.Linear(hidden_layer_size, output_size)

    def forward(self, input_seq):
        h_0 = torch.zeros(1, input_seq.size(0), self.hidden_layer_size).to(input_seq.device)
        c_0 = torch.zeros(1, input_seq.size(0), self.hidden_layer_size).to(input_seq.device)
        lstm_out, _ = self.lstm(input_seq, (h_0, c_0))
        predictions = self.linear(lstm_out[:, -1, :])
        return predictions

# ==========================================
# 2. LOAD TRAINED WEIGHTS
# ==========================================
cancer_model = CancerNet().to(DEVICE)
neural_encoder = NeuralEncoder().to(DEVICE)
neural_decoder = NeuralDecoder().to(DEVICE)

# Safely load weights
try:
    # Based on your ls image, ensure this name matches the 108MB file exactly
    cancer_model.load_state_dict(torch.load("models/final_cancer_model.pth", map_location=DEVICE))
    cancer_model.eval()
    print("✅ CancerNet (ResNet50+SE) Loaded.")
except Exception as e: print(f"⚠️ CancerNet Error: {e}")

try:
    neural_encoder.load_state_dict(torch.load("models/neural_encoder.pth", map_location=DEVICE))
    neural_encoder.eval()
    print("✅ Neural Encoder Loaded.")
except Exception as e: print(f"⚠️ Neural Encoder Error: {e}")

try:
    neural_decoder.load_state_dict(torch.load("models/neural_decoder.pth", map_location=DEVICE))
    neural_decoder.eval()
    print("✅ Neural Decoder Loaded.")
except Exception as e: print(f"⚠️ Neural Decoder Error: {e}")

# ==========================================
# 3. PIPELINE FUNCTIONS FOR FASTAPI
# ==========================================

def analyze_image(image_bytes):
    """Step 3: Attention-Based Triage (CancerNet)"""
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    tensor = transform(img).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        outputs = cancer_model(tensor)
        _, pred = torch.max(outputs, 1)
        
    return "Malignant" if pred.item() == 1 else "Benign"

def compress_image(image_bytes, quality):
    """Step 2: TRUE Neural Compression (Encoder)"""
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    tensor = transform(img).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        # The AI shrinks the image into a latent tensor
        latent_tensor = neural_encoder(tensor)
        
    # Convert the tensor to 16-bit floats to save maximum space, then to raw bytes
    latent_bytes = latent_tensor.half().cpu().numpy().tobytes()
    
    # --- UI VISUALIZATION PROXY ---
    # We generate a visible 'proxy' image for the React Frontend to display
    # by averaging the latent channels into a grayscale feature map.
    proxy_tensor = latent_tensor.mean(dim=1).squeeze(0).cpu() # Shape: (28, 28)
    
    # Normalize to 0-1 range so it saves as a valid JPEG
    proxy_tensor = (proxy_tensor - proxy_tensor.min()) / (proxy_tensor.max() - proxy_tensor.min() + 1e-5)
    proxy_img = transforms.ToPILImage()(proxy_tensor)
    proxy_img = proxy_img.resize((224, 224), Image.NEAREST)
    
    proxy_buffer = io.BytesIO()
    proxy_img.save(proxy_buffer, format="JPEG")
    proxy_bytes = proxy_buffer.getvalue()
    
    return latent_bytes, proxy_bytes

def reconstruct_image(compressed_bytes):
    """Step 6: TRUE Neural Decompression (Decoder)"""
    # Convert the raw bytes back into a numpy array, then to a PyTorch tensor
    # We know the shape is (1, 16, 28, 28) based on our Encoder architecture
    latent_np = np.frombuffer(compressed_bytes, dtype=np.float16).reshape(1, 16, 28, 28)
    latent_tensor = torch.from_numpy(latent_np).float().to(DEVICE)
    
    with torch.no_grad():
        # The AI decodes the latent math back into visual pixels
        restored_tensor = neural_decoder(latent_tensor)
        
    restored_img = transforms.ToPILImage()(restored_tensor.squeeze(0).cpu())
    
    buffer = io.BytesIO()
    restored_img.save(buffer, format="JPEG", quality=100)
    return buffer.getvalue()