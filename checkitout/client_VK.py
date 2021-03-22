import numpy as np
import aiortc
import multiprocessing
import cv2
import asyncio
import logging
import math

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

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        # self.transform = transform

    async def recv(self):
        frame = await self.track.recv()
        return frame


async def run(pc, signaling):
    def add_tracks():
        # pc.addTrack(BouncingBallStreamTrack())
        pass

    @pc.on("track")
    def on_track(track):
        if(track.kind == "video"):
           pc.addTrack(VideoTransformTrack(track)) 
    # connect signaling
    await signaling.connect()
    print("Signaling connected in client!")
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
                # add_tracks()
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
