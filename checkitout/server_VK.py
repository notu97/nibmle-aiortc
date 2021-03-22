import numpy as np
import aiortc
import multiprocessing
import cv2
import asyncio
import logging
import math

# def screensaver():
#     img = np.zeros((480,640,3),dtype='uint8')
#     dx,dy =1,1
#     x,y = 100,100
#     while True:
#         # Display the image
#         # cv2.imshow('a',img)
#         send(img)
#         k = cv2.waitKey(10)
#         img = np.zeros((480,640,3),dtype='uint8') 
#         # Increment the position
#         x = x+dx
#         y = y+dy
#         cv2.circle(img,(x,y),20,(255,0,0),-1)
#         if k != -1:
#             break
#         # Change the sign of increment on collision with the boundary
#         if y >=480:
#             dy *= -1
#         elif y<=0:
#             dy *= -1
#         if x >=640:
#             dx *= -1
#         elif x<=0:
#             dx *= -1
#     # cv2.destroyAllWindows()

# screensaver()
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    MediaStreamTrack,
    VideoStreamTrack,
)
from av import VideoFrame
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, create_signaling, TcpSocketSignaling
import fractions
import time
from typing import Tuple

# VIDEO_CLOCK_RATE = 90000
# VIDEO_PTIME = 1 / 30  # 30fps
# VIDEO_TIME_BASE = fractions.Fraction(1, VIDEO_CLOCK_RATE)
class BouncingBallStreamTrack(VideoStreamTrack):
    """
    A Media track that sends a bouncing ball.
    """
    # kind = "video"

    def __init__(self):
        super().__init__()
        self.counter = 0
        self.frames = []
        img = np.zeros((480,640,3),dtype='uint8')
        dx,dy =1,1
        x,y = 100,100
        print("Init BouncingBallStreamTrack!")
        while True:
            self.frames.append(VideoFrame.from_ndarray(img))
            img = np.zeros((480,640,3),dtype='uint8') 
            # Increment the position
            x = x+dx
            y = y+dy
            cv2.circle(img,(x,y),20,(255,0,0),-1)
            # Change the sign of increment on collision with the boundary
            if y >=480:
                dy *= -1
            elif y<=0:
                dy *= -1
            if x >=640:
                dx *= -1
            elif x<=0:
                dx *= -1
            # k += 1
    
    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.frames[self.counter]
        frame.pts = pts
        frame.time_base = time_base
        self.counter += 1
        return frame   


async def run(pc, signaling):
    def add_tracks():
        pc.addTrack(BouncingBallStreamTrack())
        print("PC added!")



    # connect signaling
    await signaling.connect()
    print("About to send offer")
    # send offer
    add_tracks()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)
    # consume signaling
    for k in range(30):
        obj = await signaling.receive()
        print("Obj = Awaiting signal receive!")
        print("Object Type:",type(obj))
        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            # await recorder.start()

            if obj.type == "offer":
                # send answer
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


# create signaling and peer connection
signaling = TcpSocketSignaling("0.0.0.0",8888)
pc = RTCPeerConnection()

print("Signaling and PC set!")

# run event loop
loop = asyncio.get_event_loop()
print("Loop set!")
try:
    loop.run_until_complete(
        run(
            pc=pc,
            signaling=signaling,
        )
    )
except KeyboardInterrupt:
    pass
finally:
    # cleanup
    loop.run_until_complete(signaling.close())
    loop.run_until_complete(pc.close())
