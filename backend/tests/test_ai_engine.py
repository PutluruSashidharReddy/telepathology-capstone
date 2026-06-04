import unittest
from unittest.mock import MagicMock, patch
import sys
import numpy as np
import io

# Mock heavy dependencies if they don't exist in the current environment
# This allows tests to run and validate logic even without GPU/heavy libs
try:
    import torch
    import torch.nn as nn
except ImportError:
    torch = MagicMock()
    nn = MagicMock()
    torch.nn = nn
    torch.device = MagicMock()
    sys.modules["torch"] = torch
    sys.modules["torch.nn"] = nn
    sys.modules["torchvision"] = MagicMock()
    sys.modules["torchvision.models"] = MagicMock()
    sys.modules["torchvision.transforms"] = MagicMock()

try:
    import cv2
except ImportError:
    cv2 = MagicMock()
    sys.modules["cv2"] = cv2

try:
    from PIL import Image
except ImportError:
    Image = MagicMock()
    sys.modules["PIL"] = Image

from backend.ai_engine import CancerNet, calculate_metrics, SUBTYPES, analyze_image

class TestAIEngineLogic(unittest.TestCase):

    def test_subtypes_count(self):
        """Requirement 4: Multi-class classification should have 8 subtypes."""
        self.assertEqual(len(SUBTYPES), 8)
        self.assertIn("Adenosis", SUBTYPES)
        self.assertIn("Papillary Carcinoma", SUBTYPES)

    def test_cancernet_initialization(self):
        """Verify CancerNet initializes with 8 classes."""
        model = CancerNet(num_classes=8)
        self.assertIsNotNone(model)

    @patch('backend.ai_engine.cancer_model')
    @patch('backend.ai_engine.transforms')
    @patch('backend.ai_engine.Image')
    def test_analyze_image_logic(self, mock_image, mock_transforms, mock_model):
        """Test the logic of image analysis mapping to subtypes."""
        # Mock model output to return index 5 (Lobular Carcinoma)
        mock_output = MagicMock()
        mock_model.return_value = mock_output
        mock_torch = sys.modules["torch"]
        mock_torch.max.return_value = (None, mock_torch.tensor(5))
        mock_torch.tensor(5).item.return_value = 5
        
        # Call function
        diagnosis, subtype = analyze_image(b"fake_bytes")
        
        self.assertEqual(subtype, "Lobular Carcinoma")
        self.assertEqual(diagnosis, "Malignant")

    def test_calculate_metrics_structure(self):
        """Requirement 8: Check PSNR and SSIM calculation logic."""
        # Mock cv2 outputs
        cv2.imdecode.return_value = np.zeros((224, 224, 3), dtype=np.uint8)
        cv2.PSNR.return_value = 35.5
        
        with patch('backend.ai_engine.ssim', return_value=0.92):
            metrics = calculate_metrics(b"orig", b"restored")
            
            self.assertEqual(metrics["psnr"], 35.5)
            self.assertEqual(metrics["ssim"], 0.92)
            self.assertIn("diagnostic_usability", metrics)
            self.assertGreaterEqual(metrics["diagnostic_usability"], 0)
            self.assertLessEqual(metrics["diagnostic_usability"], 1.0)

if __name__ == '__main__':
    unittest.main()
