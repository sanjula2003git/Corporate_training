"""
Run VGG16 ONCE on the helmet images and save real assets the Streamlit app displays:
  cnn_assets/<name>/input.png  early.png  mid.png  deep.png  gradcam.png
  cnn_assets/predictions.json  (top-3 ImageNet guesses per image)
No torch is needed at app runtime -- only these PNGs.
"""
import os, json, glob
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import matplotlib.cm as cm

BASE = r"C:\Users\fersa\Corporate Training\Smart-Construction-DL"
HELMETS = os.path.join(BASE, "helmets")
OUT = os.path.join(BASE, "cnn_assets")
os.makedirs(OUT, exist_ok=True)

# ---- model ----
weights = models.VGG16_Weights.IMAGENET1K_V1
model = models.vgg16(weights=weights).eval()
for _m in model.modules():                      # avoid in-place ReLU vs backward-hook clash
    if isinstance(_m, torch.nn.ReLU):
        _m.inplace = False
categories = weights.meta["categories"]
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# feature.  VGG16 features indices: early relu=3 (block1), mid relu=15 (block3), deep relu=29 (block5)
TAPS = {"early": 3, "mid": 15, "deep": 29}
LAST_CONV = 28  # for Grad-CAM

def montage(act, n=16, cols=4):
    """act: (C,H,W) tensor -> tiled colormap image (uint8 RGB)."""
    act = act.detach().numpy()
    C, H, W = act.shape
    n = min(n, C); rows = int(np.ceil(n / cols))
    pad = 2
    canvas = np.zeros((rows * (H + pad) - pad, cols * (W + pad) - pad, 3), dtype=np.uint8)
    for i in range(n):
        r, c = divmod(i, cols)
        m = act[i]
        m = (m - m.min()) / (np.ptp(m) + 1e-9)
        rgb = (cm.viridis(m)[:, :, :3] * 255).astype(np.uint8)
        canvas[r*(H+pad):r*(H+pad)+H, c*(W+pad):c*(W+pad)+W] = rgb
    im = Image.fromarray(canvas)
    scale = max(1, 640 // im.width)                 # upscale small deep/mid maps crisply
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)

def gradcam(x, class_idx):
    acts, grads = {}, {}
    layer = model.features[LAST_CONV]
    h1 = layer.register_forward_hook(lambda m, i, o: acts.__setitem__("v", o))
    h2 = layer.register_full_backward_hook(lambda m, gi, go: grads.__setitem__("v", go[0]))
    out = model(x)
    model.zero_grad()
    out[0, class_idx].backward()
    h1.remove(); h2.remove()
    a = acts["v"][0]              # (512,14,14)
    g = grads["v"][0]            # (512,14,14)
    w = g.mean(dim=(1, 2))       # (512,)
    cam = F.relu((w[:, None, None] * a).sum(0))
    cam = cam / (cam.max() + 1e-9)
    cam = F.interpolate(cam[None, None], size=(224, 224), mode="bilinear", align_corners=False)[0, 0]
    return cam.detach().numpy()

def overlay(pil_img, cam, alpha=0.45):
    base = np.asarray(pil_img.resize((224, 224)).convert("RGB")).astype(float) / 255
    heat = cm.jet(cam)[:, :, :3]
    out = (1 - alpha) * base + alpha * heat
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))

files = sorted(glob.glob(os.path.join(HELMETS, "*.jpg")) + glob.glob(os.path.join(HELMETS, "*.png")))
print(f"{len(files)} images")
predictions = {}

for path in files:
    name = os.path.splitext(os.path.basename(path))[0]
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    img = Image.open(path).convert("RGB")
    img.resize((224, 224)).save(os.path.join(d, "input.png"))
    x = preprocess(img).unsqueeze(0)

    # capture taps in one forward pass
    feats = {}
    handles = [model.features[idx].register_forward_hook(
        (lambda key: (lambda m, i, o: feats.__setitem__(key, o[0])))(k)) for k, idx in TAPS.items()]
    with torch.no_grad():
        logits = model(x)
    for h in handles:
        h.remove()

    probs = F.softmax(logits[0], dim=0)
    top = torch.topk(probs, 3)
    predictions[name] = [[categories[i], round(float(probs[i]), 3)] for i in top.indices]
    print(f"  {name}: {predictions[name][0]}")

    montage(feats["early"]).save(os.path.join(d, "early.png"))
    montage(feats["mid"]).save(os.path.join(d, "mid.png"))
    montage(feats["deep"]).save(os.path.join(d, "deep.png"))

    top_idx = int(top.indices[0])
    cam = gradcam(x, top_idx)
    overlay(img, cam).save(os.path.join(d, "gradcam.png"))

with open(os.path.join(OUT, "predictions.json"), "w") as f:
    json.dump(predictions, f, indent=2)

# --- export the REAL first conv layer kernels so the app can show the actual
#     convolution arithmetic (multiply-accumulate) without needing torch ---
conv1 = model.features[0]                       # Conv2d(3, 64, kernel_size=3)
np.savez_compressed(
    os.path.join(OUT, "conv1_kernels.npz"),
    W=conv1.weight.detach().numpy(),            # (64, 3, 3, 3)
    b=conv1.bias.detach().numpy(),              # (64,)
)
print("Saved conv1 kernels:", conv1.weight.shape, "->", os.path.join(OUT, "conv1_kernels.npz"))

# feature-map shapes at each tap (for the 'deeper = smaller & more abstract' myth)
shapes = {k: list(v.shape) for k, v in feats.items()}
with open(os.path.join(OUT, "shapes.json"), "w") as f:
    json.dump(shapes, f, indent=2)
print("Feature map shapes:", shapes)

print("Saved assets to", OUT)
