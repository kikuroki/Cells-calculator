"""
Here we define the general class for segmentation models used within the application.
These are the models for:
- segmenting L929 cellular monolayer;
- segmenting spherical MSCs;
- segmenting spheroids.
"""
import os
import pandas as pd
import cv2
import numpy as np
from ultralytics import YOLO
from model.sahi.auto_model import AutoDetectionModel
from model.sahi.utils.cv import read_image
from model.sahi.predict import get_prediction, get_sliced_prediction, predict

from model.BaseModel import BaseModel
from model.utils import *

class Segmenter(BaseModel):
    def __init__(self, path, object_size):
        super().__init__(path, object_size)
        self.detections=None

    def init_x20_model(self, path_to_model: str):
        self.model = YOLO(path_to_model, task="segment")

    def init_x10_model(self, path_to_model):
        return super().init_x10_model(path_to_model)

    def count_x20(self, input_image, conf=False, labels=False, boxes=False,
              masks=True, probs=False, show=False, save=True, color_mode="instance",
              filename=".cache/cell_tmp_img_with_detections.png", min_score=0.2, **kwargs):
        """
        This function performs inference on a given image using a pre-trained given model.
        The general pipeline can be described through the following steps:
        1. Load model, load image;
        2. Perform forward propagation and get results: bboxes, masks, confs;
        3. Structure the output;
        4. Save output in RAM cache as pandas DataFrame for further possible recalculations;
        5. Display obtained results through masks, if available, or simply through bboxes.

        Args:
            - model: loaded ultralytics YOLO model;
            - input_image: path to input image;
            - **kwargs: additional configurations for model inference: conf, iou etc.

        Returns:
            - list of dictionaries containing detections information.
        """
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        if self.detections is None:
            outputs = self.model(input_image, conf=0.2, iou=0.6, retina_masks=True, **kwargs)[0]  # TODO: change the config definition point to a higher level
            self.original_image = outputs.orig_img
            outputs.plot(conf=conf, labels=labels, boxes=boxes,
                                             masks=masks, probs=probs, show=show, save=save,
                                             color_mode=color_mode, filename=filename)
            self.detections = results_to_pandas(outputs)
            self.h, self.w = outputs.orig_img.shape[0], outputs.orig_img.shape[1]
            self.detections['box'] = self.detections['box'].apply(lambda b: b * np.array([self.w, self.h, self.w, self.h]))
            # self.object_size['set_size'](self.detections[detections['confidence'] >= min_score]['box'].copy())
            self.object_size['set_size'](self.detections['box'].copy())

        detections = self.detections[self.detections['confidence'] >= min_score]
        # self.object_size['set_size'](detections['box'].copy())
        original_image = self.original_image.copy()

        filtered_detections = filter_detections(detections,
                                                min_size = self.object_size['min_size'],
                                                max_size= self.object_size['max_size'])
        # self.detections['box'] = filtered_detections['box'].apply(lambda b: b / np.array([self.w, self.h, self.w, self.h]))
        current_results = pandas_to_ultralytics(filtered_detections, original_image)
        if current_results is None:
            return None
        current_image = current_results.plot(conf=conf, labels=labels, boxes=boxes,
                                             masks=masks, probs=probs, show=show, save=save,
                                             color_mode=color_mode, filename=filename)
        return filtered_detections

    def count_x10(self, input_image: str, conf=False, labels=False, boxes=False,
              masks=True, probs=False, show=False, save=True, color_mode="instance",
              filename=".cache/cell_tmp_img_with_detections.png", min_score=0.2, **kwargs):
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        if self.detections is None:
            self.original_image = read_image(input_image)
            outputs = get_sliced_prediction(
                input_image,
                self.model_x10,
                slice_height=512,
                slice_width=512,
                overlap_height_ratio=0.2,
                overlap_width_ratio=0.2
            ).to_coco_predictions()
            # self.original_image = outputs.orig_img
            self.h, self.w = self.original_image.shape[0], self.original_image.shape[1]
            self.detections = sahi_to_pandas(outputs, self.h, self.w)
            # self.detections['box'] = self.detections['box'].apply(lambda b: b * np.array([self.w, self.h, self.w, self.h]))
            # self.object_size['set_size'](self.detections[detections['confidence'] >= min_score]['box'].copy())
            self.object_size['set_size'](self.detections['box'].copy())

        detections = self.detections[self.detections['confidence'] >= min_score]
        # self.object_size['set_size'](detections['box'].copy())
        original_image = self.original_image.copy()

        filtered_detections = filter_detections(detections,
                                                min_size = self.object_size['min_size'],
                                                max_size= self.object_size['max_size'])
        # self.detections['box'] = filtered_detections['box'].apply(lambda b: b / np.array([self.w, self.h, self.w, self.h]))
        current_results = pandas_to_ultralytics(filtered_detections, original_image)
        if current_results is None:
            return None
        current_image = current_results.plot(conf=conf, labels=labels, boxes=boxes,
                                             masks=masks, probs=probs, show=show, save=save,
                                             color_mode=color_mode, filename=filename)
        return filtered_detections
