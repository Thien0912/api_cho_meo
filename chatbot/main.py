from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os

# Tải mô hình Keras đã huấn luyện
MODEL_PATH = 'efficientnetb0_1.keras'
model = tf.keras.models.load_model(MODEL_PATH)

# Khởi tạo FastAPI
app = FastAPI()

# Định nghĩa request body để nhận ảnh từ frontend
# Đường dẫn ảnh trên server hoặc URL

# Chuyển ảnh từ đường dẫn sang định dạng mà mô hình có thể nhận diện


# Định nghĩa endpoint để nhận diện giống chó/mèo

