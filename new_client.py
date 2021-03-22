'''
This is client this will first receive video feed from server detect centroid of the ball 
'''


import numpy as np
import cv2
import asyncio
# import json
from av import VideoFrame
from multiprocessing import Process, Queue
from aiortc.contrib.signaling import BYE, TcpSocketSignaling, create_signaling, add_signaling_arguments
from aiortc.contrib.media import MediaBlackhole, MediaRelay, MediaPlayer, MediaRecorder
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from skimage import io
import matplotlib.pyplot as plt
from matplotlib.pyplot import imshow
from collections import deque
import time


plt.ion()

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.r=0
        self.disp_queue=Queue()
        self.out_queue=Queue()
        
    async def recv(self):
        frame = await self.track.recv()
        print(frame)
        new_img=frame.to_image()
        imshow(new_img)

        img = frame.to_ndarray(format="bgr24")
        print(type(img))
        
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # self.disp_queue.put(img)

        # time.sleep(0.01)
        # self.disp_queue.put_nowait(img)

        # disp_f= multiprocessing.Process(target=disp_img,args=(img))
        # disp_f.start()
        # disp_f.join
        # im = Imag

        # self.img_buff.append(gray)
        # print(len(self.img_buff))

        # while len(self.img_buff) >5:
        #     print("buff")
        #     show_im=self.img_buff.popleft()
        #     print(len(self.img_buff))
        #     cv2.imshow("IMG",show_im)
            # plt.show()

        # img_color = cv2.pyrDown(cv2.pyrDown(img))
        # gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        
        # cv2.imshow("img", self.img_buff.pop())


        # .show()
        # plt.pause(0.2)
        # plt.close()
        # print(frame, img.shape)
        # plt.imsh/()
        # cv2.imwrite('/home/shiladitya/Downloads/imgs/im_'+str(self.r)+'.png',img)
        # self.r=self.r+1
        # print("Disp------------")
        # # gray = cv2.cvtColor(img, cv2.COLOR_2GRAY)
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        # l,g,_=img.shape

        # print(frame)

        
        # cv2.imshow('my_frame',gray)

        # img = frame.to_ndarray(format="bgr24")
        # rows, cols, _ = img.shape
        # M = cv2.getRotationMatrix2D((cols / 2, rows / 2), frame.time * 45, 1)
        # img = cv2.warpAffine(img, M, (cols, rows))

        # # rebuild a VideoFrame, preserving timing information
        # new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        # new_frame.pts = frame.pts
        # new_frame.time_base = frame.time_base
        # return new_frame
        

        return new_frame


        # return frame

        # if self.transform == "cartoon":
        #     img = frame.to_ndarray(format="bgr24")

        #     # prepare color
        #     img_color = cv2.pyrDown(cv2.pyrDown(img))
        #     for _ in range(6):
        #         img_color = cv2.bilateralFilter(img_color, 9, 9, 7)
        #     img_color = cv2.pyrUp(cv2.pyrUp(img_color))

        #     # prepare edges
        #     img_edges = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        #     img_edges = cv2.adaptiveThreshold(
        #         cv2.medianBlur(img_edges, 7),
        #         255,
        #         cv2.ADAPTIVE_THRESH_MEAN_C,
        #         cv2.THRESH_BINARY,
        #         9,
        #         2,
        #     )
        #     img_edges = cv2.cvtColor(img_edges, cv2.COLOR_GRAY2RGB)

        #     # combine color and edges
        #     img = cv2.bitwise_and(img_color, img_edges)

        #     # rebuild a VideoFrame, preserving timing information
        #     new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        #     new_frame.pts = frame.pts
        #     new_frame.time_base = frame.time_base
        #     return new_frame
        # elif self.transform == "edges":
        #     # perform edge detection
        #     img = frame.to_ndarray(format="bgr24")
        #     img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)

        #     # rebuild a VideoFrame, preserving timing information
        #     new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        #     new_frame.pts = frame.pts
        #     new_frame.time_base = frame.time_base
        #     return new_frame
        # elif self.transform == "rotate":
        #     # rotate image
        #     img = frame.to_ndarray(format="bgr24")
        #     rows, cols, _ = img.shape
        #     M = cv2.getRotationMatrix2D((cols / 2, rows / 2), frame.time * 45, 1)
        #     img = cv2.warpAffine(img, M, (cols, rows))

        #     # rebuild a VideoFrame, preserving timing information
        #     new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        #     new_frame.pts = frame.pts
        #     new_frame.time_base = frame.time_base
        #     return new_frame
        # else:
        #     return frame


async def run(pc, recorder, signaling, role):
    # def add_tracks():
        # if player and player.audio:
        # #     pc.addTrack(player.audio)

        # if player and player.video:
        #     pc.addTrack(  VideoTransformTrack(player.subscribe(track) ))
        # else:
        #     pc.addTrack(FlagVideoStreamTrack())

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        
        if track.kind == "video":
            pc.addTrack(  VideoTransformTrack(track))

        recorder.addTrack(track)

    # connect signaling
    await signaling.connect()

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()
            # await pc.start()
            print("inside True")
            if obj.type == "offer":
                print("inside offer True")
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif obj is BYE:
            print("Exiting")
            break


if __name__=="__main__":
    print(__name__,"CLIENT HI")

    host="0.0.0.0"
    port="20"

    signaling = TcpSocketSignaling(host,port)
    pc=RTCPeerConnection()

    recorder = MediaRecorder("/home/shiladitya/Downloads/sample_recorded_myrec.mp4")
    

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(pc=pc, recorder=recorder, signaling=signaling, role="answer")
        )
    except KeyboardInterrupt:
        pass
    finally:
        print("cleanup")
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
