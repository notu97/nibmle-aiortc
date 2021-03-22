'''
This is client this will first receive video feed from server detect centroid of the ball 
'''


import numpy as np
import cv2
import asyncio
# import json
from av import VideoFrame
from multiprocessing import Process, Queue, Value
from aiortc.contrib.signaling import BYE, TcpSocketSignaling, create_signaling, add_signaling_arguments
from aiortc.contrib.media import MediaBlackhole, MediaRelay, MediaPlayer, MediaRecorder
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from skimage import io
import matplotlib.pyplot as plt
from collections import deque
import time
from myUtils import FrameVideoStream
from threading import Thread
# from queue import Queue

plt.ion()

def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))

# player = MediaRelay()

def channel_send(channel, message):
    # channel_log(channel, ">", message)
    channel.send(message)

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.r=0
        # frame = await self.track.recv()
        # self.fvs=FrameVideoStream(queueSize=100).start()
        self.My_Q = Queue(maxsize=50)
        self.image =0
        self.greenLower = np.array([29, 86, 6])
        self.greenUpper = np.array([64, 255, 255])
        self.x =Value('i',-1)
        self.y =Value('i',-1)
        
        # self.coords= Value

        p1=Process(target=self.Parse_image,args=())
        p1.daemon=True
        p1.start()

    async def recv(self):
        try:            
            frame = await self.track.recv()
            # print(frame)
            img = frame.to_ndarray(format="bgr24")
            # self.image = img
            # self.fvs.get_frame(img)
            
            # cv2.circle(frame,center, radius=int(radius), color =(255,0,0), thickness=2 )
            # cv2.circle(frame,center, radius=1, color =(0,0,255), thickness=-1 )
            
            cv2.imshow("Client Side Window", img)
            cv2.waitKey(1)

            if not self.My_Q.full():
                self.My_Q.put(img)
            # print("CENTER: ", self.x.value, self.y.value)
        except KeyboardInterrupt:
            print("interr from recv")
            # self.fvs.stop()
        return frame
    
    def Parse_image(self):
        """
        Function to display Client side window  and also get the centroid of the ball
        """
        print("MY PROC")
        try:
            while True:
                # print(" Processing Image ", self.My_Q.qsize())
                if self.My_Q.qsize() > 0:
                    # print("No Ball Detected ", end="\r")
                    
                    frame = self.My_Q.get()
                    
                    blurred = cv2.GaussianBlur(frame, (21, 21), 0)
                    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

                    mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
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
                        
                        if radius >20:    
                            # cv2.drawContours(frame, cnts, -1, (0,255,75), 2)
                            # print ("get Center Proc",center )
                            self.x.value=center[0]
                            self.y.value=center[1]
                            cv2.circle(frame,center, radius=int(radius), color =(255,0,0), thickness=2 )
                            cv2.circle(frame,center, radius=1, color =(0,0,255), thickness=-1 )
                        else:
                            self.x.value=-1
                            self.y.value=-1
                    else:
                        self.x.value=-1
                        self.y.value=-1

                    cv2.putText(frame, "Queue Size: {}".format(self.My_Q.qsize()),(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.imshow("Parsed Image Window",frame)
                    cv2.waitKey(1)
                
        except KeyboardInterrupt:
            print(" keyboard interr returning")
            return

time_start = None


def current_stamp():
    global time_start

    if time_start is None:
        time_start = time.time()
        return 0
    else:
        return int((time.time() - time_start) * 1000000)

async def run(pc, player, recorder, signaling, role, fp):
    
    # def add_tracks():
    #     if player and player.audio:
    #         pc.addTrack(player.audio)

    #     if player and player.video:
    #         print("Client add_Track vid")
    #         pc.addTrack(  player.video )
    #     else:
            # print("Client add_Track vid-FLAG")
            # pc.addTrack(VideoTransformTrack(track))
            # pc.addTrack(FlagVideoStreamTrack())

    # connect signaling
    await signaling.connect()

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        
        if track.kind == "video":
            stream_obj=VideoTransformTrack(track)
            pc.addTrack(stream_obj)
        
        # ************ WORKING*********************
        @pc.on('datachannel')
        def on_datachannel(channel):
            @channel.on('message')
            def on_message(message):
                data_send = str(stream_obj.x.value)+","+str(stream_obj.y.value)
                # print(data_send)
                channel.send(data_send)
        # ************ WORKING*********************
       
        
    
    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            # await recorder.start()
            # await pc.start()
            
            print("inside True")
            if obj.type == "offer":
                print("Client send Answer")
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
            # elif isinstance(obj, RTCIceCandidate):
            #     await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break

# print("HI")


if __name__=="__main__":
    print(__name__,"CLIENT HI")

    host="192.168.1.118"
    port="20"

    signaling = TcpSocketSignaling(host,port)
    pc=RTCPeerConnection()
    
    fp = open("/home/shiladitya/Downloads/my_file_send.txt", "wb")

    # options={"framerate":"30", "video_size": "640x480"}
    # player = MediaPlayer("/dev/video3",format="v4l2", options=options)
    player = None
    # video=relay.subscribe(player.video)

    recorder = MediaRecorder("/home/shiladitya/Downloads/sample_recorded_NEW.mp4")

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            run(pc=pc, player=player ,recorder=recorder, signaling=signaling, role="answer", fp=fp)
        )
    except KeyboardInterrupt:
        pass
    finally:
        print("cleanup")
        # loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())

