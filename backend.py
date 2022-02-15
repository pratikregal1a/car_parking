from turtle import st
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import cv2
from object_detector import *
import numpy as np
from datetime import datetime

from sqlalchemy import all_
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_flag = 0
option_flag_1 = 0
option_flag_2 = 0
signup_flag=0
users={"admin":"admin"}

db= SQLAlchemy(app)
class Todo(db.Model):
    user_name=db.Column(db.String(200),primary_key=True)
    user_pass=db.Column(db.String(200),nullable=False)
    date_created=db.Column(db.DateTime,default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.user_name} -> {self.user_pass} -> {self.date_created}"

def populate_dic():
    global users
    all_users_list=Todo.query.all()
    all_users_list=list(all_users_list)
    for i in all_users_list:
        a=str(i)
        a=a.split(" -> ")
        if(a[0] not in users):
            users[a[0]]=a[1]
        else:
            continue


@app.route('/')
def welcome():
    global login_flag
    login_flag = 1
    populate_dic()
    return render_template('loginpage.html')


@app.route('/loginpage', methods=['POST', 'GET'])
def loginpage():
    error = None
    global users
    populate_dic()
    user=request.form['username']
    password=request.form['password']
    if request.method == 'POST':
        if user not in users:
            error = 'user doesnt exist'
            return render_template('loginpage.html',user=user)
        elif users[user] != password:
            error ="wrong password"
            return render_template('WrongPassword.html')
        else:
            return render_template('options.html')
    return render_template('WrongPassword.html')
    

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    global signup_flag
    global users
    if signup_flag >0 and request.method=='POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return render_template('signup.html',username=username)
        else:
            update_database=Todo(user_name=username.lower(),user_pass=password)
            db.session.add(update_database)
            db.session.commit()
            return render_template('loginpage.html')
    else:
        signup_flag=1
        return render_template('signup.html')

@app.route('/WrongPassword', methods=['POST', 'GET'])
def WrongPassword():
    error = None
    global signup_flag
    signup_flag=0
    if request.method == 'POST':
        if request.form['username'] not in users:
            error = 'user doesnt exist'
        elif users[request.form['username']] != request.form['password']:
            error ="wrong password"
            return render_template('WrongPassword.html')
        else:
            return render_template('options.html')
    else:
        return render_template('WrongPassword.html')

@app.route('/options', methods=['POST', 'GET'])
def options():
    global heap_size
    if login_flag:
        return render_template('options.html', name=heap_size)
    else:
        return render_template('loginpage.html')


@app.route('/choice1', methods=['POST', 'GET'])
def choice1():
    sizefinder()
    global option_flag_1
    option_flag_1 = 1
    return render_template('choice1.html')
    
    
@app.route('/givloc', methods=['POST', 'GET'])
def givloc():
    global arr
    global heap_size
    global option_flag_1
    global diction
    global curr_used
    global startime
    if option_flag_1 and request.method == 'POST':
        carnum = request.form['carnum']
        try:
            diction[carnum]
            startime = datetime.now()
        except:
            minimum = extract_min()
            diction[carnum] = minimum
            curr_used[minimum] = 1
            option_flag_1 = 0
            print(minimum)
            print(carnum)
            print(curr_used)
            return render_template('givloc.html', name=[minimum, carnum, curr_used])
        else:
            return "<h1>Your Car is Already there</h1>"
    else:
        return render_template('options.html')


@app.route('/choice2', methods=['POST', 'GET'])
def choice2():
    return render_template('choice2.html')

@app.route('/parkinglist', methods=['POST', 'GET'])
def parkinglist():
    return render_template('parkinglist.html')

@app.route('/givcar', methods=['POST', 'GET'])
def givcar():
    carnum = request.form['carnum']
    try:
        diction[carnum]
    except:
        return "<h1>Car not there in Parking Area</h1>"
    else:
        plotnum = diction[carnum]
        return render_template('givcar.html', name=plotnum)


@app.route('/choice3', methods=['POST', 'GET'])
def choice3():
    global option_flag_2
    option_flag_2 = 1
    return render_template('choice3.html')


@app.route('/givexit', methods=['POST', 'GET'])
def givexit():
    global arr
    global heap_size
    global option_flag_2
    global diction
    global curr_used
    global endtime
    if option_flag_2 and request.method == 'POST':
        carnum = request.form['carnum']
        try:
            diction[carnum]
            endtime = datetime.now()
        except:
            return "<h1>Car not there in Parking Area</h1>"
        else:
            plotnum = diction[carnum]
            curr_used[plotnum] = 0
            del diction[carnum]
            insert(plotnum)
            option_flag_2 = 0
            return render_template('givexit.html', name=[plotnum, curr_used])
    else:
        return render_template('options.html')

@app.route('/givexit')
def timer():
    time = endtime-startime
    return render_template('givexit.html', time=time)

def heapify(i):
    global heap_size
    global arr
    smallest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if (l < heap_size and arr[l] < arr[smallest]):
        smallest = l
    if (r < heap_size and arr[r] < arr[smallest]):
        smallest = r
    if (smallest != i):
        swap = arr[i]
        arr[i] = arr[smallest]
        arr[smallest] = swap
        heapify(smallest)


def insert(key):
    global arr
    global heap_size
    heap_size += 1
    arr[heap_size - 1] = key
    heapify_bottom(heap_size - 1)


def heapify_bottom(i):
    global arr
    global heap_size
    parent = (i - 1) // 2
    if (parent >= 0):
        if (arr[parent] > arr[i]):
            swap = arr[parent]
            arr[parent] = arr[i]
            arr[i] = swap
            heapify_bottom(parent)


def extract_min():
    global arr
    global heap_size
    if heap_size==0:
        return(-1)
    minimum = arr[0]
    arr[0] = arr[heap_size-1]
    heap_size = heap_size-1
    heapify(0)
    return(minimum)


def buildHeap():
    global heap_size
    global arr
    startIdx = int((heap_size / 2)) - 1
    for i in range(startIdx, -1, -1):
        heapify(i)

def sizefinder():
# Load Aruco detector
  parameters = cv2.aruco.DetectorParameters_create()
  aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_50)


# Load Object Detector
  detector = HomogeneousBgDetector()

# Load Image
  img = cv2.imread("bc.jpg")

# Get Aruco marker
  corners, _, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)

# Draw polygon around the marker
  int_corners = np.int0(corners)
  cv2.polylines(img, int_corners, True, (0, 255, 0), 5)

# Aruco Perimeter
  aruco_perimeter = cv2.arcLength(corners[0], True)

# Pixel to cm ratio
  pixel_cm_ratio = aruco_perimeter / 20

  contours = detector.detect_objects(img)

# Draw objects boundaries
  for cnt in contours:
    # Get rect
      rect = cv2.minAreaRect(cnt)
      (x, y), (w, h), angle = rect

    # Get Width and Height of the Objects by applying the Ratio pixel to cm
      object_width = w / pixel_cm_ratio
      object_height = h / pixel_cm_ratio

    # Display rectangle
      box = cv2.boxPoints(rect)
      box = np.int0(box)

      cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)
      cv2.polylines(img, [box], True, (255, 0, 0), 2)
      cv2.putText(img, "Width {} inches".format(round(object_width, 1)), (int(x - 100), int(y - 20)), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)
    

  cv2.imshow("Image", img)
  cv2.waitKey(0)

if __name__ == "__main__":
    global heap_size
    global arr
    global diction
    global curr_used
    curr_used = {}
    diction = {}
    arr = []
    c = chr(65)
    for i in range(1, 7):
        for j in range(1, 9):
            s = c + str(j)
            arr.append(s)
            curr_used[s] = 0
        c = chr(65 + i)
    heap_size = len(arr)
    buildHeap()
    app.run(debug=True)

