'''
  Server.py

  This serves the image to the client
'''

import numpy as np
import cv2
import asyncio
# import json
from multiprocessing import Process, Queue, Value
from aiortc.contrib.signaling import BYE, TcpSocketSignaling, create_signaling, add_signaling_arguments
from aiortc.contrib.media import RelayStreamTrack, MediaRelay, MediaPlayer, MediaRecorder, PlayerStreamTrack
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription

from threading import Thread
import matplotlib.pyplot as plt
from myUtils import FrameVideoStream
import time
import math


def channel_log(channel, t, message): # Helper function to display data channel logs
    print("channel(%s) %s %s" % (channel.label, t, message))

def channel_send(channel, message): 
    '''
    Function to send PINGS to the Client
    '''
    # print(type(channel))
    assert isinstance(message, str)

    channel.send(message)       

class Webcam_Class(MediaStreamTrack):
    """
    A video stream track that takes images from the webcam (at /dev/video0) and gets the center of the green ball on the screen.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        assert isinstance(track, PlayerStreamTrack)
        
        self.track = track
        self.vid = MediaRelay().subscribe(self.track) # Subscribe to the local Media player (Here it is the webcam at "/dev/video0")
        
        assert isinstance(self.vid, RelayStreamTrack)

        # Declare the upper and lower threshold for green colour
        self.greenLower = np.array([29, 86, 6])
        self.greenUpper = np.array([64, 255, 255])

        # Set initial position of the ball
        self.x =-1
        self.y =-1
        
    
    async def recv(self):
        frame = await self.vid.recv() # get frames from Webcam 
        img = frame.to_ndarray(format="bgr24") # Convert it into BGR format

        # Display Server Side Frames
        cv2.imshow("Server side window",img)
        cv2.waitKey(1)

        my_frame = img
        
        # Parse the image to get center of the ball
        blurred = cv2.GaussianBlur(my_frame, (21, 21), 0) # Blurr the image
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
                self.x=center[0]
                self.y=center[1]
                # Draw circle and center point on the image
                cv2.circle(my_frame,center, radius=int(radius), color =(255,0,0), thickness=2 ) 
                cv2.circle(my_frame,center, radius=1, color =(0,0,255), thickness=-1 )
            else: # Else assign -1 to both x and y positions
                self.x=-1
                self.y=-1
        else: # Else there are no contours/Ball in the image hence assign -1 to both x and y positions
            self.x=-1
            self.y=-1

        #Display the parsed image on the Server side
        cv2.imshow("Parsed Image Window (Server)",my_frame)
        cv2.waitKey(1)
        return frame

time_start = None


def current_stamp():
    global time_start

    if time_start is None:
        time_start = time.time()
        return 0
    else:
        return int((time.time() - time_start) * 1000000)


async def run(pc, player, signaling, role):
    '''
    This function sends an offer to the Client side using the signaling type 
    declared in the main function. Here role="Offer"
    '''

    assert isinstance(pc, RTCPeerConnection)
    assert isinstance(signaling,TcpSocketSignaling)
    assert isinstance(player, MediaPlayer)
    assert role == "offer"

    class_obj = Webcam_Class(player.video) # Declare webcam class object
    def add_tracks():
        # Add Webcam Object to aiortc addTrack function
        pc.addTrack(class_obj)

    # connect signaling
    await signaling.connect()
    
    if role == "offer":
        add_tracks()

        # Create a DataChannel called "chat" 
        channel = pc.createDataChannel("chat")
        channel_log(channel, "-", "created by local party")

        async def send_pings(): 
            '''
                Ping to the client at a given rate
            '''
            while True:
                channel_send(channel, "ping %d" % current_stamp())
                await asyncio.sleep(0.001)

        @channel.on("open")
        def on_open():
            asyncio.ensure_future(send_pings())

        @channel.on("message")
        def on_message(message):
            # Receive and split the message to get x and y
            x = int(message.split(",")[0]) 
            y = int(message.split(",")[1])
            if x<0 or y<0 :
                print("No ball in frame")
            else:        
                error= math.sqrt((x-class_obj.x)**2 + (y-class_obj.y)**2)

                print(f"Received Coords (x,y): {x,y}, original: {class_obj.x,class_obj.y}, Error: {error}") 
                print("-------------------------------------------------")

        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)

    # consume signaling

    while True:
        
        obj = await signaling.receive()
        # disp_img()
        print("Server while: ", obj.type )
        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            # await recorder.start()
            # print(obj.type)
            if obj.type == "offer":
                # send answer
                print("Server acks answer")
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
            
        elif obj is BYE:
            print("Exiting")
            break


if __name__=="__main__":
    print(__name__,"HI")

    host="192.168.1.118"
    port="20"

    signaling = TcpSocketSignaling(host,port) # Create the TCP socket signaling object
    pc=RTCPeerConnection()

    # Webcam properties
    options={"framerate":"30", "video_size": "640x480"}
    
    # Setup the Media source i.e. webcam
    player = MediaPlayer("/dev/video0",format="v4l2", options=options)
    
    loop = asyncio.get_event_loop()

    # Start the asyncio loop
    try:
        loop.run_until_complete(
            run(pc=pc, player=player, signaling=signaling, role="offer")
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
