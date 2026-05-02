import torch, json, os
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from transformers import ViTForImageClassification
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_PATH = "../backend/models/vit_xray.pt"
TEST_DIR   = "../dataset/test"
IMG_SIZE   = 224

tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.5,0.5,0.5],[0.5,0.5,0.5]),
])
test_ds = datasets.ImageFolder(TEST_DIR, tf)
test_dl = DataLoader(test_ds, batch_size=32, shuffle=False)
idx_to_class = {v: k for k, v in test_ds.class_to_idx.items()}

model = ViTForImageClassification.from_pretrained(
    "google/vit-base-patch16-224-in21k",
    num_labels=2, ignore_mismatched_sizes=True
)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.to(DEVICE).eval()

all_preds, all_labels = [], []
with torch.no_grad():
    for imgs, labels in test_dl:
        out = model(pixel_values=imgs.to(DEVICE))
        preds = out.logits.argmax(dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.numpy())

names = [idx_to_class[i] for i in range(len(idx_to_class))]
print(classification_report(all_labels, all_preds, target_names=names))
print("Confusion matrix:")
print(confusion_matrix(all_labels, all_preds))
