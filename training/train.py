import os, json, torch, numpy as np
from torch import nn, optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from transformers import ViTForImageClassification
from tqdm import tqdm

# ── CONFIG ─────────────────────────────────────
DATASET_DIR = "/content/dataset/chest_xray"
MODEL_SAVE  = "/content/vit_xray.pt"
CLASSES_F   = "/content/classes.json"

NUM_EPOCHS = 10
BATCH_SIZE  = 8
LR          = 2e-5
IMG_SIZE    = 224
NUM_CLASSES = 2
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME  = "google/vit-base-patch16-224-in21k"

# ── TRANSFORMS ────────────────────────────────
train_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3),
])

val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3),
])

# ── DATASETS ───────────────────────────────────
train_ds = datasets.ImageFolder(DATASET_DIR + "/train", train_tf)
test_ds  = datasets.ImageFolder(DATASET_DIR + "/test", val_tf)

train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
test_dl  = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

# ── CLASS MAP ──────────────────────────────────
class_to_idx = train_ds.class_to_idx
idx_to_class = {v:k for k,v in class_to_idx.items()}

with open(CLASSES_F, "w") as f:
    json.dump(idx_to_class, f)

print("Classes:", idx_to_class)

# ── CLASS WEIGHTS ──────────────────────────────
counts = []
for c in train_ds.classes:
    counts.append(len(os.listdir(DATASET_DIR + "/train/" + c)))

counts = np.array(counts)
weights = 1 / counts
weights = weights / weights.sum()
weights = torch.tensor(weights, dtype=torch.float).to(DEVICE)

# ── MODEL ──────────────────────────────────────
model = ViTForImageClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_CLASSES,
    ignore_mismatched_sizes=True
).to(DEVICE)

# ── TRAIN SETUP ───────────────────────────────
optimizer = optim.AdamW(model.parameters(), lr=LR)
loss_fn   = nn.CrossEntropyLoss(weight=weights)

best_acc = 0

# ── TRAIN LOOP ────────────────────────────────
for epoch in range(NUM_EPOCHS):

    model.train()
    correct, total, loss_sum = 0, 0, 0

    for imgs, labels in tqdm(train_dl):
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(pixel_values=imgs)
        loss = loss_fn(outputs.logits, labels)

        loss.backward()
        optimizer.step()

        loss_sum += loss.item()
        preds = outputs.logits.argmax(1)

        correct += (preds == labels).sum().item()
        total += labels.size(0)

    train_acc = correct / total

    # ── VALIDATION ──
    model.eval()
    vc, vt = 0, 0

    with torch.no_grad():
        for imgs, labels in test_dl:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)

            outputs = model(pixel_values=imgs)
            preds = outputs.logits.argmax(1)

            vc += (preds == labels).sum().item()
            vt += labels.size(0)

    val_acc = vc / vt

    print(f"Epoch {epoch+1}: Loss={loss_sum/len(train_dl):.4f} "
          f"Train Acc={train_acc:.4f} Val Acc={val_acc:.4f}")

    # ── SAVE BEST MODEL ──
    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), MODEL_SAVE)
        print("Saved Best Model")

print("Training Done! Best Accuracy:", best_acc)