import cv2

cap = cv2.VideoCapture(0)
retval, image = cap.read()

cv2.imwrite('test.jpg', image)
