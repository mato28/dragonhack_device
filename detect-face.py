
import boto3
import time
import requests
import base64
import cv2
import numpy as np
import io
import sys
import tkinter
from PIL import Image, ImageTk, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

def showPIL(pilImage):
    root = tkinter.Tk()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.overrideredirect(1)
    root.geometry("%dx%d+0+0" % (w, h))
    root.focus_set()    
    root.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit()))
    canvas = tkinter.Canvas(root,width=w,height=h)
    canvas.pack()
    canvas.configure(background='black')
    imgWidth, imgHeight = pilImage.size
    if imgWidth > w or imgHeight > h:
        ratio = min(w/imgWidth, h/imgHeight)
        imgWidth = int(imgWidth*ratio)
        imgHeight = int(imgHeight*ratio)
        pilImage = pilImage.resize((imgWidth,imgHeight), Image.ANTIALIAS)
    image = ImageTk.PhotoImage(pilImage)
    imagesprite = canvas.create_image(w/2,h/2,image=image)
    root.mainloop()


def get_emotion(emotions):
    topEmotional = 'HAPPY'
    maxPercentEmotional = 0

    for emotional in emotions:
        if maxPercentEmotional < emotional['Confidence']:
            topEmotional = emotional['Type']
            maxPercentEmotional = emotional['Confidence']
    return topEmotional


def get_tag(data):
    age = data['ageFrom']
    if age < 40:
        if data['eyeglassesNumber'] > 0:
            return 'eyeglassesYoung'
        if data['sunglassesNumber'] > 0:
            return 'sunglassesYoung'
        if data['beardNumber'] > 0:
            return 'beardYoung'
    elif age < 50:
        if data['eyeglassesNumber'] > 0:
            return 'eyeglassesMiddle'
        if data['sunglassesNumber'] > 0:
            return 'sunglassesMiddle'
        if data['beardNumber'] > 0:
            return 'beardMiddle'
    else:
        if data['eyeglassesNumber'] > 0:
            return 'eyeglassesOld'
        if data['sunglassesNumber'] > 0:
            return 'sunglassesOld'
        if data['beardNumber'] > 0:
            return 'beardOld'
    return 'default'


def full_screen_catch(base):
    imgdata = base64.b64decode(base)
    image = Image.open(io.BytesIO(imgdata))
    # showPIL(image)
    image.show()


def make_request(data):
    print(data)
    r = requests.post("http://193.2.178.254:3000/reports", data=data)
    full_screen_catch(r.content.decode("utf-8").split('base64,')[1])


def detect():
    client = boto3.client('rekognition')
    cap = cv2.VideoCapture(0)
    retval, image = cap.read()
    ret, jpeg = cv2.imencode('.jpg', image)

    # cv2.imwrite('test.jpg', image)
    # with open(imageFile, 'rb') as image:
    response = client.detect_faces(Image={'Bytes': jpeg.tobytes()},  Attributes=[
        'ALL'
    ])
    cap.release()

    results = []
    data = {'ageFrom': 0,
            'ageTo': 0,
            'sunglassesNumber': 0,
            'eyeglassesNumber': 0,
            'maleNumber': 0,
            'emotionsNumber': 0,
            'beardNumber': 0,
            'mustacheNumber': 0,
            'numberOfPeople': len(response['FaceDetails']),
            'emotional': 'HAPPY',
            'gender': 'male'
            }
    ageFromTotal = 0
    ageToTotal = 0
    for label in response['FaceDetails']:

        result = {'ageFrom': label['AgeRange']['Low'],
                  'ageTo': label['AgeRange']['High'],
                  'sunglasses': label['Sunglasses']['Value'],
                  'eyeglasses': label['Eyeglasses']['Value'],
                  'gender': label['Gender']['Value'],
                  'emotions': get_emotion(label['Emotions']),
                  'beard': label['Beard']['Value'],
                  'mustache': label['Mustache']['Value'],
                  }
        ageFromTotal += result['ageFrom']
        ageToTotal += result['ageTo']
        data['emotional'] = get_emotion(label['Emotions'])
        if result['sunglasses']:
            data['sunglassesNumber'] += 1
        if result['eyeglasses']:
            data['eyeglassesNumber'] += 1
        if result['gender'] == 'Male':
            data['maleNumber'] += 1
        if result['beard']:
            data['beardNumber'] += 1
        if result['mustache']:
            data['mustacheNumber'] += 1

        results.append(result)
        print(result)

    if data['numberOfPeople'] != 0:
        data['ageFrom'] = ageFromTotal / data['numberOfPeople']
        data['ageTo'] = ageToTotal / data['numberOfPeople']
        if data['maleNumber'] > (data['numberOfPeople']/2):
            data['gender'] = 'male'
        else:
            data['gender'] = 'female'

    data['adTag'] = get_tag(data)
    make_request(data)


if __name__ == "__main__":
    while True:
        # try:
        detect()
        # except:
            # print('napaka')
        time.sleep(5)