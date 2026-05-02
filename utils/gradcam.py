import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from scipy.ndimage import gaussian_filter

IMG_SIZE = 224
DEVICE = "cpu"

_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3),
])

def generate_attention_map(model, pil_image):
    """Generate attention map using ViT attention weights (no OpenCV)"""

    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    tensor = _transform(pil_image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(pixel_values=tensor)

    attentions = outputs.attentions

    # Fallback if attention not returned
    if attentions is None:
        print("⚠️ Attention not returned → using fallback")
        return pil_image.resize((224, 224))

    num_tokens = attentions[0].shape[-1]
    rollout = torch.eye(num_tokens)

    for attn in attentions:
        attn = attn[0].mean(dim=0)
        attn = attn + torch.eye(num_tokens)
        attn = attn / attn.sum(dim=-1, keepdim=True)
        rollout = attn @ rollout

    mask = rollout[0, 1:]
    size = int(np.sqrt(mask.shape[0]))
    mask = mask.reshape(size, size).cpu().numpy()

    # Normalize
    mask = (mask - mask.min()) / (mask.max() + 1e-8)

    # Resize using PIL (instead of cv2.resize)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))
    mask_img = mask_img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)
    mask = np.array(mask_img) / 255.0

    # Apply Gaussian blur using scipy (instead of cv2.GaussianBlur)
    mask = gaussian_filter(mask, sigma=2)
    
    # Normalize again
    mask = (mask - mask.min()) / (mask.max() + 1e-8)

    # Create heatmap with jet colormap (instead of cv2.applyColorMap)
    heatmap = create_jet_colormap(mask)
    heatmap = heatmap.astype(np.uint8)

    # Get original image
    orig = pil_image.resize((IMG_SIZE, IMG_SIZE))
    orig_array = np.array(orig)

    # Blend overlay (instead of cv2.addWeighted)
    overlay = (orig_array * 0.6 + heatmap * 0.4).astype(np.uint8)

    return Image.fromarray(overlay)


def create_jet_colormap(mask):
    """
    Create jet colormap (blue to red) without OpenCV
    Maps values 0-1 to colors: blue -> cyan -> green -> yellow -> red
    """
    h, w = mask.shape
    heatmap = np.zeros((h, w, 3), dtype=np.float32)
    
    for i in range(h):
        for j in range(w):
            val = mask[i, j]
            
            if val < 0.25:
                # Blue to Cyan (0 to 0.25)
                t = val / 0.25
                r = 0
                g = t
                b = 1
            elif val < 0.5:
                # Cyan to Green (0.25 to 0.5)
                t = (val - 0.25) / 0.25
                r = 0
                g = 1
                b = 1 - t
            elif val < 0.75:
                # Green to Yellow (0.5 to 0.75)
                t = (val - 0.5) / 0.25
                r = t
                g = 1
                b = 0
            else:
                # Yellow to Red (0.75 to 1)
                t = (val - 0.75) / 0.25
                r = 1
                g = 1 - t
                b = 0
            
            heatmap[i, j] = [r * 255, g * 255, b * 255]
    
    return heatmap.astype(np.uint8)
