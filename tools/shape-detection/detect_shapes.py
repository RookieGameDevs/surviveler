# USAGE
# python detect_shapes.py --image shapes_and_colors.png

# import the necessary packages
from rdp import rdp
from numpy import array
import argparse
import imutils
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
                help="path to the input image")
args = vars(ap.parse_args())

# load the image and resize it to a smaller factor so that
# the shapes can be approximated better
image = cv2.imread(args["image"])
resized = imutils.resize(image, width=300)
ratio = image.shape[0] / float(resized.shape[0])

# convert the resized image to grayscale, blur it slightly,
# and threshold it
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]

# find contours in the thresholded image and initialize the
# shape detector
contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)
contours = contours[0] if imutils.is_cv2() else contours[1]

# loop over the contours
for ct in contours:
    # compute the center of the contour, then detect the name of the
    # shape using only the contour
    M = cv2.moments(ct)
    cX = int((M["m10"] / M["m00"]) * ratio)
    cY = int((M["m01"] / M["m00"]) * ratio)

    # Get the minimal number of points to describe the shape
    peri = cv2.arcLength(ct, True)
    epsilon = 0.04 * peri
    approx = cv2.approxPolyDP(ct, epsilon, True)
    arr = approx.flatten().reshape((len(approx), 2))
    print(arr.tolist())

    flat = ct.flatten().reshape((len(ct), 2))
    print(flat)
    #ct_tuples = [(flat[i], flat[i + 1]) for i in range(0, len(flat) - 1, 2)]
    red = array(rdp(flat.tolist(), epsilon), flat.dtype)
    print(red)
    print(len(red))

    # multiply the contour (x, y)-coordinates by the resize ratio,
    # then draw the contours and the name of the shape on the image
    red = red.astype("float")
    red *= ratio
    red = red.astype("int")

    cv2.drawContours(image, [red], -1, (0, 255, 0), 2)

    # show the output image
    cv2.imshow("Image", image)
    cv2.waitKey(1000)
