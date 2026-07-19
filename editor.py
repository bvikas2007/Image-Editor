from PIL import Image, ImageEnhance
import numpy as np

# This file does the actual pixel manipulation. No AI model is needed for
# tone/colour edits, just Pillow. Background removal uses the rembg library,
# which is a free, pretrained model you just pip install.


def _sky_mask(image: Image.Image):
    """A simple mask that treats the top 30% of the image as 'sky'."""
    arr = np.array(image.convert("RGB"))
    height = arr.shape[0]
    mask = np.zeros((height, arr.shape[1]), dtype=np.float32)
    top_band = int(height * 0.3)
    mask[:top_band, :] = 1.0
    return mask


def _apply_warmth(image: Image.Image, amount: float) -> Image.Image:
    """Shifts the image toward amber (positive) or blue (negative)."""
    arr = np.array(image.convert("RGB")).astype(np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] + amount * 40, 0, 255)  # red channel
    arr[:, :, 2] = np.clip(arr[:, :, 2] - amount * 40, 0, 255)  # blue channel
    return Image.fromarray(arr.astype(np.uint8))


def apply_tone_edit(image: Image.Image, params: dict, region: str = "full") -> Image.Image:
    """Applies warmth, contrast, saturation and brightness adjustments."""
    result = image.convert("RGB")

    if "warmth" in params:
        result = _apply_warmth(result, params["warmth"])

    if "contrast" in params:
        factor = 1.0 + params["contrast"]
        result = ImageEnhance.Contrast(result).enhance(max(factor, 0.1))

    if "saturation" in params:
        factor = 1.0 + params["saturation"]
        result = ImageEnhance.Color(result).enhance(max(factor, 0.0))

    if "brightness" in params:
        factor = 1.0 + params["brightness"]
        result = ImageEnhance.Brightness(result).enhance(max(factor, 0.1))

    if region == "sky":
        # blend the edited version with the original, only inside the sky mask
        mask_arr = _sky_mask(image)
        original_arr = np.array(image.convert("RGB")).astype(np.float32)
        edited_arr = np.array(result).astype(np.float32)
        mask_3d = np.stack([mask_arr] * 3, axis=-1)
        blended = original_arr * (1 - mask_3d) + edited_arr * mask_3d
        result = Image.fromarray(blended.astype(np.uint8))

    return result


def remove_background(image: Image.Image) -> Image.Image:
    """Removes the background using the rembg model (U^2-Net under the hood)."""
    # rembg needs onnxruntime to actually run the model. If it's missing,
    # rembg's own import code calls sys.exit(1) instead of raising a normal
    # error, which would crash the whole app instead of showing a message
    # in the chat. So we check for it ourselves first and fail politely.
    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Background removal needs the 'onnxruntime' package, which is not installed. "
            "Run this in your terminal, then restart the app: pip install onnxruntime"
        )

    from rembg import remove
    return remove(image.convert("RGB"))


def build_explanation(op: str, region: str, params: dict) -> str:
    """Turns the applied operation into a short human readable sentence,
    used in the chat log so the user sees what actually happened."""
    if op == "remove_bg":
        return "Removed the background using the rembg AI model."
    if not params:
        return f"Applied a light {op} adjustment."
    parts = []
    for key, value in params.items():
        direction = "increased" if value > 0 else "decreased"
        parts.append(f"{key} {direction} by {abs(value) * 100:.0f}%")
    region_text = f" on the {region}" if region != "full" else ""
    return "Applied: " + ", ".join(parts) + region_text + "."
