import cv2
import numpy as np



vs = cv2.VideoCapture(0)

while True:
    _,frame = vs.read()
    
    greenLower = np.array([29, 86, 6])
    greenUpper = np.array([64, 255, 255])


    blurred = cv2.GaussianBlur(frame, (31, 31), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # print(type(mask), mask.shape,frame.shape, blurred.shape, hsv.shape)
    center = None
    cnts,high  = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    
    if(len(cnts)>0 ):
            
        c= max(cnts,key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        
        if radius >30:    
            cv2.drawContours(frame, cnts, -1, (0,255,75), 2)

            print (len(cnts), x,y,radius,center )
            cv2.circle(frame,center, radius=2, color =(0,0,255), thickness=-1 )
            # cv2.circle(frame,(x,y), radius=2, color =(0,255,0), thickness=-1 )
            

    cv2.imshow("frame",frame)
    
    cv2.waitKey(1)
