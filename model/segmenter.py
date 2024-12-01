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
    # def __init__(self, path, object_size):
    #     super().__init__(path, object_size)

    def init_x20_model(self, path_to_model: str):
        self.model = YOLO(path_to_model, task="segment")

    def init_x10_model(self, path_to_model):
        return super().init_x10_model(path_to_model)

    def count_x20(self, input_image, plot = True, conf=False, labels=False, boxes=False,
              masks=True, probs=False, show=False, save=True, colormap="tab20", tracking=False,
              filename=".cache/cell_tmp_img_with_detections.png", min_score=0.05, alpha=0.75, store_bin_mask=False, **kwargs):
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

        colormap = self.object_size['color_map']
        if self.detections is None:
            outputs = self.model(input_image, conf=0.2, iou=0.6, retina_masks=True, **kwargs)[0]  # TODO: change the config definition point to a higher level
            self.original_image = outputs.orig_img
            # outputs.plot(conf=conf, labels=labels, boxes=boxes,
            #                                  masks=masks, probs=probs, show=show, save=save,
            #                                  color_mode=color_mode, filename=filename)
            self.detections = results_to_pandas(outputs, store_bin_mask)
            self.h, self.w = outputs.orig_img.shape[0], outputs.orig_img.shape[1]
            self.detections['box'] = self.detections['box'].apply(lambda b: b * np.array([self.w, self.h, self.w, self.h]))

            if tracking is False:
                self.object_size['signal']("set_size", self.detections['box'].copy())  #TODO: make sure it works with tracker

        detections = self.detections[self.detections['confidence'] >= min_score]
        if tracking is False:
            self.object_size['signal']("set_size", self.detections['box'].copy())  #TODO: make sure it works with tracker
        original_image = self.original_image.copy()
        if tracking is False:
            filtered_detections = filter_detections(detections,
                                                    min_size = self.object_size['min_size'],
                                                    max_size= self.object_size['max_size'])
        else:
            filtered_detections = detections

        # current_results = pandas_to_ultralytics(filtered_detections, original_image)
        # if current_results is None:
        #     return None
        # current_image = current_results.plot(conf=conf, labels=labels, boxes=boxes,
        #                                      masks=masks, probs=probs, show=show, save=save,
        #                                      color_mode=color_mode, filename=filename)
        if plot is True:
            plot_predictions(original_image, filtered_detections['mask'].tolist(),
                            filename=filename, colormap=colormap, alpha=alpha)
        # else:
        #     current_results = pandas_to_ultralytics(filtered_detections, original_image)
        #     if current_results is None:
        #         return None
        #     current_image = current_results.plot(conf=conf, labels=labels, boxes=boxes,
        #                                          masks=masks, probs=probs, show=show, save=save,
        #                                          color_mode="instance", filename=filename)
        return filtered_detections

    def count_x10(self, input_image: str, conf=False, labels=False, boxes=False,
              masks=True, probs=False, show=False, save=True, colormap="tab20",
              filename=".cache/cell_tmp_img_with_detections.png", min_score=0.01, alpha=0.75, **kwargs):
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        colormap = self.object_size['color_map']
        if self.detections is None:
            self.original_image = read_image(input_image)
            outputs = get_sliced_prediction(
                input_image,
                self.model_x10,
                slice_height=128,
                slice_width=128,
                overlap_height_ratio=.1,
                overlap_width_ratio=.1
            ).to_coco_predictions()
            # self.original_image = outputs.orig_img
            self.h, self.w = self.original_image.shape[0], self.original_image.shape[1]
            self.detections = sahi_to_pandas(outputs, self.h, self.w)
            self.object_size['signal']("set_size", self.detections['box'].copy())

        detections = self.detections[self.detections['confidence'] >= min_score]

        original_image = self.original_image.copy()

        filtered_detections = filter_detections(detections,
                                                min_size = self.object_size['min_size'],
                                                max_size= self.object_size['max_size'])
        
        # current_results = pandas_to_ultralytics(filtered_detections, original_image)
        # if current_results is None:
        #     return None
        # current_image = current_results.plot(conf=conf, labels=labels, boxes=boxes,
        #                                      masks=masks, probs=probs, show=show, save=save,
        #                                      color_mode=color_mode, filename=filename)
        
        plot_predictions(original_image, filtered_detections['mask'].tolist(),
                         filename=filename, colormap=colormap, alpha=alpha)
        return filtered_detections