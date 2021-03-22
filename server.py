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
from aiortc.contrib.media import MediaBlackhole, MediaRelay, MediaPlayer, MediaRecorder
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from threading import Thread
import matplotlib.pyplot as plt
from myUtils import FrameVideoStream
import time
import math
# def server_display():
#     while True:

def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))

def channel_send(channel, message):
    # channel_log(channel, ">", message)
    channel.send(message)       

#############################
counter =0
class MY_Class(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.vid = MediaRelay().subscribe(self.track)
        # self.r=0
        # frame = await self.track.recv()
        # self.fvs=FrameVideoStream(queueSize=100).start()
        # self.My_Q = Queue(maxsize=100)
        # self.player = player

        self.greenLower = np.array([29, 86, 6])
        self.greenUpper = np.array([64, 255, 255])
        self.x =-1
        self.y =-1
        
        # self.coords= Value

        # p1=Process(target=self.func,args=())
        # p1.daemon=True
        # p1.start()
    
    async def recv(self):
        global counter
        frame = await self.vid.recv()
        # print("###############",counter)
        # counter=counter+1
        img = frame.to_ndarray(format="bgr24")
        # print("***************",counter)
        # counter=counter+1
        # self.Parse_image(img)

        cv2.imshow("Server side window",img)
        cv2.waitKey(1)

        #######################

        my_frame = img
        
        blurred = cv2.GaussianBlur(my_frame, (21, 21), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # # print(type(mask), mask.shape,frame.shape, blurred.shape, hsv.shape)
        center = None
        cnts,high  = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        
        if(len(cnts)>0 ):
                
            c= max(cnts,key=cv2.contourArea)
            ((x_e, y_e), radius) = cv2.minEnclosingCircle(c)
            
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            
            if radius >20:    
                # cv2.drawContours(frame, cnts, -1, (0,255,75), 2)
                # print ("get Center Proc",center )
                self.x=center[0]
                self.y=center[1]
                cv2.circle(my_frame,center, radius=int(radius), color =(255,0,0), thickness=2 )
                cv2.circle(my_frame,center, radius=1, color =(0,0,255), thickness=-1 )
        else:
            self.x=-1
            self.y=-1

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
    class_obj = MY_Class(player.video)
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            # print("hi")
            print("Server add_Track vid")
            pc.addTrack(class_obj)
        else:
            print("Server add_Track vid-FLAG")
            pc.addTrack(FlagVideoStreamTrack())

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
            # print(message.decode('utf-8'))
            if x<0 or y<0 :
                print("No ball in frame")
            else:        
                error= math.sqrt((x-class_obj.x)**2 + (y-class_obj.y)**2)

                print(f"Received Coords (x,y): {x,y}, original: {class_obj.x,class_obj.y}, Error: {error}") 
                print("-------------------------------------------------")

        # ************ WORKING*********************

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
