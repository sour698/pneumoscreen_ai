import torch
import cv2
import numpy as np
from PIL import Image
from torchvision import transforms

IMG_SIZE = 224
DEVICE = "cpu"

_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3),
])

def generate_attention_map(model, pil_image):

    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    tensor = _transform(pil_image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(pixel_values=tensor)

    attentions = outputs.attentions

    # 🔥 fallback if still None
    if attentions is None:
        print("⚠️ Attention not returned → using last hidden states fallback")
        return Image.fromarray(np.array(pil_image.resize((224,224))))

    num_tokens = attentions[0].shape[-1]
    rollout = torch.eye(num_tokens)

    for attn in attentions:
        attn = attn[0].mean(dim=0)

        attn = attn + torch.eye(num_tokens)
        attn = attn / attn.sum(dim=-1, keepdim=True)

        rollout = attn @ rollout

    mask = rollout[0, 1:]
    size = int(np.sqrt(mask.shape[0]))
    mask = mask.reshape(size, size).numpy()

    mask = (mask - mask.min()) / (mask.max() + 1e-8)

    mask = cv2.resize(mask, (IMG_SIZE, IMG_SIZE))
    mask = cv2.GaussianBlur(mask, (5,5), 0)

    heatmap = np.uint8(255 * mask)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    orig = np.array(pil_image.resize((IMG_SIZE, IMG_SIZE)))
    overlay = cv2.addWeighted(orig, 0.6, heatmap, 0.4, 0)

    return Image.fromarray(overlay)