'''
This is client this will first receive video feed from server detect centroid of the ball 
'''


import numpy as np
import cv2
import asyncio
from multiprocessing import Process, Queue, Value
from aiortc.contrib.signaling import BYE, TcpSocketSignaling
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
import matplotlib.pyplot as plt
from collections import deque
import time



class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that takes images from the webcam and gets the center of the green ball on the screen.
    """

    kind = "video"

    def __init__(self, track):

        super().__init__()  
        self.track = track  
        self.r=0
        self.My_Q = Queue(maxsize=50) # Declare the Shared Memory Queue

        # Declare the upper and lower threshold for green colour
        self.greenLower = np.array([29, 86, 6]) 
        self.greenUpper = np.array([64, 255, 255])

        # Declare the shared memory to store x and y coordinates of the ball.
        self.x =Value('i',-1)
        self.y =Value('i',-1)

        # Declare the child process that parses an image and determines the center of the green ball.
        p1=Process(target=self.Parse_image,args=())
        p1.daemon=True
        p1.start()

    async def recv(self):
        try:            
            frame = await self.track.recv() 
            
            img = frame.to_ndarray(format="bgr24")

            '''
            Show received images on the client side (comment it if "Fatal IO error 0 (Success) on X server :1" erro is encounterd)
            '''
            # cv2.imshow("Client Side Window", img)
            # cv2.waitKey(1)

            if not self.My_Q.full():
                self.My_Q.put(img) # put the received image into the shared Process Queue
            # print("CENTER: ", self.x.value, self.y.value)
        except KeyboardInterrupt:
            pass
            # print("interr from recv")
        return frame
    
    def Parse_image(self):
        """
        Function to display Client side parsed window, get the centroid of the ball and draw the center of the ball. This
        is the Child process forked by the parent client.py process
        """
        # print("Parse image function")
        try:
            while True:
                if self.My_Q.qsize() > 0:
                    
                    frame = self.My_Q.get() # Get the frame from the Queue
                    
                    blurred = cv2.GaussianBlur(frame, (21, 21), 0) # Blurr the image
                    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV) # convert to HSV
 
                    mask = cv2.inRange(hsv, self.greenLower, self.greenUpper) # Build a mask using green colour threshold
                    mask = cv2.erode(mask, None, iterations=2) # Erode to remove noise
                    mask = cv2.dilate(mask, None, iterations=2) # Dilate further to expose large contours even further

                    center = None
                    cnts,high  = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE) # Find the contours
                    
                    if(len(cnts)>0 ): # Check to see if there are contours in the image
                            
                        c= max(cnts,key=cv2.contourArea) # Get the largest contour 
                        ((x, y), radius) = cv2.minEnclosingCircle(c) # get a circle radius that can enclose the largest contour
                        
                        M = cv2.moments(c) # Find the Moment of the largest contour
                        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])) # Find the center of the largest contour 
                        
                        if radius >20: # Update the x,y value of the ball's center if circle radius is > 20
                            # print ("get Center Proc",center )
                            self.x.value=center[0]
                            self.y.value=center[1]
                            # Draw circle and center point on the image
                            cv2.circle(frame,center, radius=int(radius), color =(255,0,0), thickness=2 ) 
                            cv2.circle(frame,center, radius=1, color =(0,0,255), thickness=-1 )
                        else: # Else assign -1 to both x and y positions
                            self.x.value=-1
                            self.y.value=-1
                    else: # Else there are no contours/Ball in the image hence assign -1 to both x and y positions
                        self.x.value=-1
                        self.y.value=-1
                
                    #Display the parsed image on the client side
                    cv2.putText(frame, "Queue Size: {}".format(self.My_Q.qsize()),(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.imshow("Parsed Image Window (Client)",frame)
                    cv2.waitKey(1)
                # else: # Else there are no contours/Ball in the image hence assign -1 to both x and y positions
                #         self.x.value=-1
                #         self.y.value=-1
        except KeyboardInterrupt:
            # print(" keyboard interr returning")
            return


async def run(pc, signaling, role):
    
    # connect signaling
    await signaling.connect()

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        
        if track.kind == "video":
            stream_obj=VideoTransformTrack(track) # Declare a VideoTransformTrack Class object
            pc.addTrack(stream_obj)
        
        # SEND x, y coordinate back to Server
        @pc.on('datachannel')
        def on_datachannel(channel):
            @channel.on('message')
            def on_message(message):
                data_send = str(stream_obj.x.value)+","+str(stream_obj.y.value)
                arr = bytes(data_send, 'utf-8')
                print(arr)
                channel.send(data_send)
    
    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            if obj.type == "offer":
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif obj is BYE:
            print("Exiting")
            break

if __name__=="__main__":
    print("Client Startup")

    host="192.168.1.118"
    port="20"

    signaling = TcpSocketSignaling(host,port) # Create TCP socket signalling object
    pc=RTCPeerConnection() # Create a RTCPeerConnection object

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            run(pc=pc, signaling=signaling, role="answer")
        )
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
