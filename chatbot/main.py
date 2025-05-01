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

