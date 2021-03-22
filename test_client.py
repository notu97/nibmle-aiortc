import numpy as np
import cv2
import asyncio
from multiprocessing import Process, Queue, Value
from aiortc.contrib.signaling import BYE, TcpSocketSignaling
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
import matplotlib.pyplot as plt
from collections import deque
import time
import client
import server


def test_run():
    '''
        Client side
    '''
    pc=RTCPeerConnection()

    host="192.168.1.118"
    port="20"

    signaling = TcpSocketSignaling(host,port)

    role= "answer"

    client.my_run_tester(pc,signaling,"offer")
    