from fastapi import APIRouter, UploadFile, File
from utils.inference import predict_image
from utils.gradcam import generate_heatmap

router = APIRouter(prefix="/predict", tags=["Prediction"])

@router.post("/")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()

    prediction, tensor, probs = predict_image(image_bytes)
    heatmap = generate_heatmap(tensor)

    return {
        "prediction": prediction,
        "confidence": float(max(probs)),
        "heatmap": heatmap
    }