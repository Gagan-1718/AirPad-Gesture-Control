"""MediaPipe hand tracking (Tasks HandLandmarker API, MediaPipe >= 0.10)."""
import os
import urllib.request

import config


def ensure_model(path=config.MODEL_PATH, url=config.MODEL_URL):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Downloading hand model to {path} ...")
    tmp = path + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, path)
