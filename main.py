#!./venv/bin/python
""" Description of the main entry point
"""

# ================ Built-in Imports ================ #

import argparse

# ================ Third Party Imports ================ #

import cv2 as cv
from time import time

# ================ User Imports ================ #

import config
from classes.Imu import Imu
from classes.object_position_processing import calculate_angle
from image_manipulation import image_transformation
from object_detection import detect_and_track
from object_detection import CentroidTracker

# ================ Authorship ================ #

__author__ = "Chris Patenaude"
__contributors__ = ["Chris Patenaude", "Gabriel Michael",
                    "Gregory Sanchez", "Donald 'Max' Harkens", "Tobias Hodges"]


# ================ Global Variables ================ #

# ================ Functions ================ #


def get_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", help="Set enviroment: 'prod', or 'dev' (default)")
    return vars(ap.parse_args())


# ================ Main ================ #

if __name__ == "__main__":

    # Parse Command Line Arguments
    args = get_args()

    # Component initilization
    imu = Imu(config.IMU_PATH)

    # Video Frame Streaming
    cap = cv.VideoCapture(config.CAPTURE_DEVICE)

    # Set up video writer
    # Define the codec and create VideoWriter object
    fourcc = cv.VideoWriter_fourcc(*'XVID')
    out = cv.VideoWriter('output.avi', fourcc, 20.0, (1200, 675))

    # Set up object tracker
    tracker = CentroidTracker.CentroidTracker()

    # Time in seconds
    frame_processing_interval = config.FRAME_INTERVAL

    # Last time a frame was processed
    last_processed_at = time()

    # Number of skipped frames
    skipped_frames = 0

    # Current frame count
    frame_count = 0

    while True:
        # Press Q on keyboard to  exit
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

        # get image
        ret, img = cap.read()
        if not ret:
            break

        frame_count += 1

        # Process a frame each time the interval has passed
        if last_processed_at + frame_processing_interval < time():

            if config.VERBOSE:
                print("__________ Frame: " + str(frame_count) + " __________")
                print("Skipped Frames: " + str(skipped_frames))
                skipped_frames = 0

            last_processed_at = time()

            # get attitude if valid image
            attitude = imu.get_last_orientation()

            # Transform image
            transformed_image = image_transformation.rotate_image(
                img, attitude)

            # detect and classify object
            detect_and_track.detect_in_image(transformed_image, tracker)

            # display on system
            if config.DRAW_TO_SCREEN:
                # Draw the objects being tracked
                tracker.draw_objects(transformed_image)
                cv.imshow('Tracked Objects', transformed_image)

            # calculate pos
            output = []
            viewport_width = transformed_image.shape[1]  # image x dimension px
            viewport_height = transformed_image.shape[0]  # image y dimension px
            viewport_angle = config.VIEWPORT_ANGLE  # image diagnal px
            for item in tracker.objects.items():

                (objID, obj) = item
                centroid_xpos = obj.centroid[0]  # horizontal center of bounding box

                compass_angle = calculate_angle(
                    viewport_width,
                    viewport_height,
                    viewport_angle,
                    centroid_xpos
                )

                if config.VERBOSE:
                    print("objID: " + str(objID) +
                          ", Centroid_xpos: " + str(centroid_xpos) +
                          ", size_increase: " + str(obj.size_increase))

                detected_obj = (objID, compass_angle)
                output.append(detected_obj)

            # output pos
            print(output)

        else:
            skipped_frames += 1

    # Clean up
    cap.release()
    out.release()
    cv.destroyAllWindows()
