import os
import io
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# Use GPU if available, else CPU (Safe for laptops)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 AI Engine loading on: {DEVICE.upper()}")

# ==========================================
# 1. MODEL ARCHITECTURES (From your Colab)
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
        self.attention = SE_Block(2048); self.avgpool = self.base.avgpool
        self.fc = nn.Sequential(nn.Linear(2048, 512), nn.ReLU(), nn.Dropout(0.4), nn.Linear(512, 2))
    def forward(self, x):
        x=self.layer0(x); x=self.layer1(x); x=self.layer2(x); x=self.layer3(x); x=self.layer4(x)
        x=self.attention(x); x=self.avgpool(x); x=torch.flatten(x, 1); return self.fc(x)

# --- Restoration (ResUNet) ---
class ResidualBlock(nn.Module):
    def __init__(self, in_c, out_c):
        super(ResidualBlock, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, 3, padding=1), nn.BatchNorm2d(out_c), nn.PReLU(),
            nn.Conv2d(out_c, out_c, 3, padding=1), nn.BatchNorm2d(out_c)
        )
        self.shortcut = nn.Sequential()
        if in_c != out_c:
            self.shortcut = nn.Sequential(nn.Conv2d(in_c, out_c, 1), nn.BatchNorm2d(out_c))
    def forward(self, x): return torch.relu(self.conv(x) + self.shortcut(x))

class ResUNet(nn.Module):
    def __init__(self):
        super(ResUNet, self).__init__()
        self.enc1 = ResidualBlock(3, 64); self.pool1 = nn.MaxPool2d(2)
        self.enc2 = ResidualBlock(64, 128); self.pool2 = nn.MaxPool2d(2)
        self.enc3 = ResidualBlock(128, 256); self.pool3 = nn.MaxPool2d(2)
        self.bridge = ResidualBlock(256, 512)
        self.up3 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True); self.dec3 = ResidualBlock(512 + 256, 256)
        self.up2 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True); self.dec2 = ResidualBlock(256 + 128, 128)
        self.up1 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True); self.dec1 = ResidualBlock(128 + 64, 64)
        self.final = nn.Conv2d(64, 3, kernel_size=1)
    def forward(self, x):
        e1 = self.enc1(x); e2 = self.enc2(self.pool1(e1)); e3 = self.enc3(self.pool2(e2))
        b = self.bridge(self.pool3(e3))
        d3 = self.dec3(torch.cat([self.up3(b), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return torch.sigmoid(self.final(d1))

# ==========================================
# 2. LOAD TRAINED WEIGHTS
# ==========================================
cancer_model = CancerNet().to(DEVICE)
resunet_model = ResUNet().to(DEVICE)

# Safely load weights
try:
    cancer_model.load_state_dict(torch.load("models/final_cancer_model_retrained.pth", map_location=DEVICE))
    cancer_model.eval()
    print("✅ CancerNet (ResNet50+SE) Loaded.")
except Exception as e: print(f"⚠️ CancerNet Error: {e}")

try:
    resunet_model.load_state_dict(torch.load("models/resunet_model.pth", map_location=DEVICE))
    resunet_model.eval()
    print("✅ ResUNet Loaded.")
except Exception as e: print(f"⚠️ ResUNet Error: {e}")

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
        
    # Assuming standard PyTorch ImageFolder sorting: 0 = Benign, 1 = Malignant
    return "Malignant" if pred.item() == 1 else "Benign"

def compress_image(image_bytes, quality):
    """Step 2: Adaptive Compression"""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()

def reconstruct_image(compressed_bytes):
    """Step 6: Deep Learning Reconstruction (ResUNet)"""
    img = Image.open(io.BytesIO(compressed_bytes)).convert('RGB')
    original_size = img.size
    
    transform_resunet = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])
    tensor = transform_resunet(img).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        restored_tensor = resunet_model(tensor)
        
    restored_img = transforms.ToPILImage()(restored_tensor.squeeze(0).cpu())
    restored_img = restored_img.resize(original_size, Image.BILINEAR) # Scale back to original
    
    buffer = io.BytesIO()
    restored_img.save(buffer, format="JPEG", quality=100)
    return buffer.getvalue()