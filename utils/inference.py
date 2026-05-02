import os
import torch
from transformers import ViTForImageClassification
from torchvision import transforms
from PIL import Image
import json
from huggingface_hub import hf_hub_download

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DEVICE = torch.device("cpu")   # 🔥 FORCE CPU for stability

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = hf_hub_download(
    repo_id="https://huggingface.co/sourav2069/xray-vit-model/blob/main/vit_xray.pt",
    filename="vit_xray.pt"
)
CLASSES_PATH = os.path.join(BASE_DIR, "..", "backend", "classes.json")

# ─────────────────────────────────────────────
# LOAD CLASSES (SAFE)
# ─────────────────────────────────────────────
if os.path.exists(CLASSES_PATH):
    with open(CLASSES_PATH) as f:
        idx_to_class = json.load(f)
else:
    print("⚠️ classes.json not found → using default labels")
    idx_to_class = {
        "0": "BACTERIAL",
        "1": "NORMAL"
    }

NUM_CLASSES = len(idx_to_class)

# ─────────────────────────────────────────────
# LOAD MODEL (FIXED)
# ─────────────────────────────────────────────
model = ViTForImageClassification.from_pretrained(
    "google/vit-base-patch16-224-in21k",
    num_labels=NUM_CLASSES,
    ignore_mismatched_sizes=True,
    attn_implementation="eager"   # ✅ REQUIRED for attention maps
)

# ❌ REMOVE THIS (causes issues)
# model.config.output_attentions = True

# ─────────────────────────────────────────────
# LOAD WEIGHTS SAFELY
# ─────────────────────────────────────────────
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"❌ Model not found at {MODEL_PATH}")

state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
model.load_state_dict(state_dict)

model.to(DEVICE)
model.eval()

# ─────────────────────────────────────────────
# TRANSFORM
# ─────────────────────────────────────────────
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3)
])

# ─────────────────────────────────────────────
# PREDICTION FUNCTION
# ─────────────────────────────────────────────
def predict(image: Image.Image):

    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(pixel_values=tensor)

        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)[0]

    pred_idx = torch.argmax(probs).item()

    prediction = {
        "class": idx_to_class.get(str(pred_idx), "Unknown"),
        "confidence": float(probs[pred_idx])
    }

    return prediction, tensor, probs.cpu().numpy()