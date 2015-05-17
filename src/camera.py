import cv2
import numpy as np
from time import sleep

DEFAULT_CAP_PROPS = {
   cv2.CAP_PROP_FRAME_WIDTH: 1400,#1280,
   cv2.CAP_PROP_FRAME_HEIGHT: 1080,#960,
   cv2.CAP_PROP_FPS: 25
}

TESTING_CAP_PROPS = {
   cv2.CAP_PROP_FRAME_WIDTH: 1280/2,
   cv2.CAP_PROP_FRAME_HEIGHT: 960/2,
   cv2.CAP_PROP_FPS: 25
}

def capture_image(filename):
   return cv2.imread(filename)

def capture_on_key(capture_keys=None, all_frames=False, quit_key='q'):
   video_capture = cv2.VideoCapture(0)

   while True:
      key = chr(cv2.waitKey(1) & 0xFF)

      ret, frame = video_capture.read()

      if capture_keys is None or key in capture_keys:
         yield (key, frame)
      elif key == quit_key:
         break
      elif all_frames:
         yield (False, frame)

   video_capture.release()

def greyscale(img):
   grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
   grey_img = cv2.equalizeHist(grey_img)
   return grey_img

def set_up_cameras(camera_config):   
   min_x = 0
   max_x = 0
   min_y = 0
   max_y = 0
   
   for cam_props in camera_config:
      x, y = cam_props['offset']
      w, h = cam_props['resolution']

      min_x = min(x, min_x)
      max_x = max(x + w, max_x)
      min_y = min(y, min_y)
      max_y = max(y + h, max_y)

      props = {
         cv2.CAP_PROP_FRAME_WIDTH: w,
         cv2.CAP_PROP_FRAME_HEIGHT: h
      }

      if not cam_props.get('juggle', True):
         cam_src = init_cam(cam_props, props)
         cam_props['capture'] = cam_src

      cam_props['props'] = props


   cams = sorted(camera_config, key=lambda x: x.get('z-index', 0))

   return {
      'cameras': cams,
      'dimensions': (
         (max_x - min_x),
         (max_y - min_y)
      ),
      'offset': (min_x, min_y)
   }

def release_cams(cam_setup):
   for cam_props in cam_setup:
      if 'capture' in cam_props:
         try:
            cam_props['capture'].release()
         except Exception:
            pass

def init_cam(cam_props, cv_props):
   cam_src = cv2.VideoCapture(cam_props['source'])
   for prop in cv_props:
      cam_src.set(prop, cv_props[prop])
   return cam_src

def get_blended_frame(cam_setup, use_juggled=False):
   cameras = cam_setup['cameras']
   w, h = cam_setup['dimensions']
   min_x, min_y = cam_setup['offset']

   frame = np.zeros((h, w))

   if use_juggled:
      for cam_props in cameras:
         if not cam_props.get('juggle', False):
            cam_props['capture'].release()

   for cam_props in cameras:
      cam_x, cam_y = cam_props['offset']
      cam_w, cam_h = cam_props['resolution']

      cam_x -= min_x
      cam_y -= min_y

      is_captured = False

      if use_juggled:
         cam_src = init_cam(cam_props, cam_props['props'])
         is_captured, cam_frame = cam_src.read()
         cam_frame = cam_frame.copy()
         cam_props['last_frame'] = cam_frame

         if cam_props.get('juggle', False):
            cam_src.release()
         else:
            cam_props['capture'] = cam_src
      elif not cam_props.get('juggle', False):
         is_captured, cam_frame = cam_props['capture'].read()
      elif 'last_frame' in cam_props:
         is_captured = True
         cam_frame = cam_props['last_frame']

      if is_captured:
         cam_frame = greyscale(cam_frame)
         frame[cam_y:(cam_y+cam_h), cam_x:(cam_x+cam_w)] = cam_frame

   return np.array(frame, dtype='uint8')

def get_frames(quit_key='q', source=0, props=DEFAULT_CAP_PROPS, crop=None):
   video_capture = cv2.VideoCapture(source)
   
   if props:
      for prop in props:
         video_capture.set(prop, props[prop])

      w, h = (props[cv2.CAP_PROP_FRAME_WIDTH], props[cv2.CAP_PROP_FRAME_HEIGHT])
   else:
      w, h = 1280, 960


   while True:
      key = cv2.waitKey(1) & 0xFF

      ret, frame = video_capture.read()

      if crop is not None:
         x1, y1, x2, y2 = crop
         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
         frame = frame[y1:y2, x1:x2]

      if key == ord(quit_key):
         # wait for quit key to be pressed
         break
      
      yield frame

   video_capture.release()
