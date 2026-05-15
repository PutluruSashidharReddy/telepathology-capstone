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

# --- Clinical Neural Compression (Residual Autoencoder) ---
class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super(ResidualBlock, self).__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(channels),
            nn.PReLU(),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(channels)
        )
    def forward(self, x):
        return x + self.conv_block(x)

class ClinicalEncoder(nn.Module):
    def __init__(self):
        super(ClinicalEncoder, self).__init__()
        self.initial = nn.Sequential(nn.Conv2d(3, 64, kernel_size=3, padding=1), nn.PReLU())
        self.down1 = nn.Sequential(nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1), nn.PReLU())
        self.res1 = ResidualBlock(128)
        self.down2 = nn.Sequential(nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1), nn.PReLU())
        self.res2 = ResidualBlock(256)
        self.down3 = nn.Sequential(nn.Conv2d(256, 32, kernel_size=3, stride=2, padding=1), nn.PReLU())
        
    def forward(self, x):
        x = self.initial(x)
        x = self.res1(self.down1(x))
        x = self.res2(self.down2(x))
        return self.down3(x)

class ClinicalDecoder(nn.Module):
    def __init__(self):
        super(ClinicalDecoder, self).__init__()
        self.initial = nn.Sequential(nn.Conv2d(32, 256, kernel_size=3, padding=1), nn.PReLU())
        self.res1 = ResidualBlock(256)
        self.up1 = nn.Sequential(nn.ConvTranspose2d(256, 128, kernel_size=3, stride=2, padding=1, output_padding=1), nn.PReLU())
        self.res2 = ResidualBlock(128)
        self.up2 = nn.Sequential(nn.ConvTranspose2d(128, 64, kernel_size=3, stride=2, padding=1, output_padding=1), nn.PReLU())
        self.res3 = ResidualBlock(64)
        self.up3 = nn.Sequential(nn.ConvTranspose2d(64, 3, kernel_size=3, stride=2, padding=1, output_padding=1), nn.Sigmoid())

    def forward(self, x):
        x = self.res1(self.initial(x))
        x = self.res2(self.up1(x))
        x = self.res3(self.up2(x))
        return self.up3(x)

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
        return self.linear(lstm_out[:, -1, :])

# ==========================================
# 2. LOAD TRAINED WEIGHTS
# ==========================================
cancer_model = CancerNet().to(DEVICE)
clinical_encoder = ClinicalEncoder().to(DEVICE)
clinical_decoder = ClinicalDecoder().to(DEVICE)

# Safely load weights
try:
    cancer_model.load_state_dict(torch.load("models/final_cancer_model.pth", map_location=DEVICE))
    cancer_model.eval()
    print("✅ CancerNet Loaded.")
except Exception as e: print(f"⚠️ CancerNet Error: {e}")

try:
    clinical_encoder.load_state_dict(torch.load("models/clinical_encoder.pth", map_location=DEVICE))
    clinical_encoder.eval()
    print("✅ Clinical Encoder Loaded.")
except Exception as e: print(f"⚠️ Clinical Encoder Error: {e}")

try:
    clinical_decoder.load_state_dict(torch.load("models/clinical_decoder.pth", map_location=DEVICE))
    clinical_decoder.eval()
    print("✅ Clinical Decoder Loaded.")
except Exception as e: print(f"⚠️ Clinical Decoder Error: {e}")

# ==========================================
# 3. PIPELINE FUNCTIONS FOR FASTAPI
# ==========================================

def analyze_image(image_bytes):
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
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    tensor = transform(img).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        latent_tensor = clinical_encoder(tensor)
        
    latent_bytes = latent_tensor.half().cpu().numpy().tobytes()
    
    # UI VISUALIZATION PROXY
    proxy_tensor = latent_tensor.mean(dim=1).squeeze(0).cpu() 
    proxy_tensor = (proxy_tensor - proxy_tensor.min()) / (proxy_tensor.max() - proxy_tensor.min() + 1e-5)
    proxy_img = transforms.ToPILImage()(proxy_tensor).resize((224, 224), Image.NEAREST)
    
    proxy_buffer = io.BytesIO()
    proxy_img.save(proxy_buffer, format="JPEG")
    
    return latent_bytes, proxy_buffer.getvalue()

def reconstruct_image(compressed_bytes):
    # Shape is now 32x28x28 due to the deeper residual architecture
    latent_np = np.frombuffer(compressed_bytes, dtype=np.float16).reshape(1, 32, 28, 28)
    latent_tensor = torch.from_numpy(latent_np).float().to(DEVICE)
    
    with torch.no_grad():
        restored_tensor = clinical_decoder(latent_tensor)
        
    restored_img = transforms.ToPILImage()(restored_tensor.squeeze(0).cpu())
    
    buffer = io.BytesIO()
    restored_img.save(buffer, format="JPEG", quality=100)
    return buffer.getvalue()