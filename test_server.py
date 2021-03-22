import numpy as np
import cv2
import asyncio
# import json
from multiprocessing import Process, Queue, Value
from aiortc.contrib.signaling import BYE, TcpSocketSignaling, create_signaling, add_signaling_arguments
from aiortc.contrib.media import RelayStreamTrack, MediaRelay, MediaPlayer, MediaRecorder, PlayerStreamTrack
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
import aiortc
from threading import Thread
import matplotlib.pyplot as plt
from myUtils import FrameVideoStream
import time
import math
import server

# def test_channel_send(channel, message):
#     server.channel_send(chann)
#     assert 

options={"framerate":"30", "video_size": "640x480"}
player = MediaPlayer("/dev/video0",format="v4l2", options=options)


def test_Webcam_Class():
        server.Webcam_Class(player.video)


def test_run():
    '''
       Server side
    '''
    pc=RTCPeerConnection()

    host="192.168.1.118"
    port="20"

    signaling = TcpSocketSignaling(host,port)

    role= "offer"

    server.run(pc=pc,player=player,signaling=signaling,role=role)
    