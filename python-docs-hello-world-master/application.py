import random
import sqlite3
from math import radians, sin, cos, asin, sqrt
import redis
from flask import Flask, render_template, request, redirect, url_for,session
import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
import os
from multiprocessing import Value
from forms import EarthForm


myHostname = "2234.redis.cache.windows.net"
myPassword = 'Dft4QQrSi1NZw55qAG3w5TFM94Vbct1bVOukhB84J+g='
r = redis.StrictRedis(host=myHostname, port=6380, password=myPassword, ssl=True)


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


def night_calculate(longitude, time):
    time_hour = str(time)[11:13]
    local_time = (float(time_hour) + (float(longitude) / 15)) % 24
    if local_time < 6 and local_time >= 0 or local_time < 24 and local_time > 18:
        return True
    else:
        return False


DATABASE = 'myDb.db'
application = Flask(__name__)
application.config["SECRET_KEY"]='05a5b375-96a3-4f89-9c8f-484f3127503a'


# index
@application.route("/")
def index():
    return render_template("admin/index.html")


# QUIZ2
# quiz2-5:  index & name & studentID
@application.route("/search/min/mag", methods=["GET"])
def Search_min_mag():
    earthquakeDB = sqlite3.connect(DATABASE)
    count = earthquakeDB.execute("select count(*) from quakes")
    mag = earthquakeDB.execute("select min(mag) from quakes where mag>2.0")
    Mag = mag.fetchall()
    print(Mag)
    Mag = Mag[0][0]
    data = earthquakeDB.execute("select * from quakes where mag = " + Mag)
    return render_template("admin/Quiz2/Q2-5minMag.html", count=count, Mag=Mag, data=data)


# quiz2-6:the  two depth values and an increment
@application.route("/quakes/count/mag/", methods=["GET"])
def count_mag():
    key1_mag = request.args.get("mag1", "3")
    key2_mag = request.args.get("mag2", "5")
    increment = request.args.get("increment", "2")
    earthquakeDB = sqlite3.connect(DATABASE)
    listlabel = []
    count2 = []
    mag = float(key1_mag)
    for mag in range(int(float(key1_mag) * 10), int(float(key2_mag) * 10), int(float(increment) * 10)):
        listlabel.append(mag / 10)
    print(listlabel)
    for v in listlabel:
        count = earthquakeDB.execute(
            "select count (*) from quakes where mag > " + str(v) + " AND mag < " + str(v + float(increment)))
        count1 = count.fetchall()
        count2.append(count1)
    print(count2)
    data=[]
    for i in range(len(count2)):
        _data=[]
        _data.append(listlabel[i])
        _data.append(count2[i])
        data.append(_data)
    return render_template("admin/Quiz2/Q2-6 CountByMag.html", key1_mag=key1_mag, key2_mag=key2_mag, count1=count2,
                           listlabel=listlabel, increment=float(increment),data=data)


# quiz2-7:cluster by latitude and longitude
@application.route("/quakes/find/cluster/", methods=["GET"])
def find_cluster():
    latitude1 = request.args.get("latitude1", "0")
    latitude2 = request.args.get("latitude2", "50")
    longitude1 = request.args.get("longitude1", "-190")
    longitude2 = request.args.get("longitude2", "-170")
    earthquakeDB = sqlite3.connect(DATABASE)
    c = earthquakeDB.cursor()
    print(latitude1)
    print(latitude2)
    print(longitude1)
    print(longitude2)
    data = c.execute(
        "select * from quakes WHERE latitude >" + latitude1 + " AND latitude<" + latitude2 + " AND longitude>" + longitude1 + " AND longitude<" + longitude2)
    rows = data.fetchall()
    count = len(rows)
    return render_template("admin/Quiz2/Q2-7cluster&La&Lo.html", data=rows, count=count, latitude1=latitude1,
                           latitude2=latitude2,
                           longitude1=longitude1, longitude2=longitude2)


# quiz2-8:search by depth and time
@application.route("/quakes/search/depth_time/", methods=["GET"])
def search_depth_time():
    key1_depth = request.args.get("depth1", "3")
    key2_depth = request.args.get("depth2", "10")
    key1_time = request.args.get("time1", "2019-06-02")
    key2_time = request.args.get("time2", "2019-06-08")
    earthquakeDB = sqlite3.connect(DATABASE)
    data = earthquakeDB.execute(
        "select * from quakes where depth > " + key1_depth + " AND depth < " + key2_depth + " and time <'" + key1_time + "' or time > '" + key2_time + "'")

    return render_template("admin/Quiz2/Q2-8SearchByDepth&&Time.html", data=data, key1_depth=key1_depth,
                           key2_depth=key2_depth,
                           key1_time=key1_time, key2_time=key2_time)


# quiz2-8:madify the mag value
@application.route("/quakes/edit/mag/<string:time>/", methods=["GET", "POST"])
def edit_mag(time=None):
    form = EarthForm()
    earthquakeDB = sqlite3.connect(DATABASE)
    earth = earthquakeDB.execute("select * from quakes where time ='" + time + "'")
    earth = earth.fetchall()[0]
    if form.validate_on_submit():
        data = form.data
        latitude = data["latitude"]
        longitude = data["longitude"]
        depth = data["depth"]
        mag = data["mag"]
        rms = data["rms"]
        earthquakeDB.execute("update quakes set mag=" + mag + " where time ='" + time + "'")
        earthquakeDB.commit()
        return redirect(url_for('search_depth_time'))
    return render_template("admin/Quiz2/Q2-8 mag_edit.html", form=form, earth=earth)


# quiz2-9: location and distance
@application.route("/quakes/search/distance/", methods=["GET"])
def search_distance():
    palce = request.args.get("place", "CA")
    key1_dis = request.args.get("dis1", "2")
    key2_dis = request.args.get("dis2", "10")
    print(palce)
    earthquakeDB = sqlite3.connect(DATABASE)
    c = earthquakeDB.cursor()
    data1 = c.execute("select * from quakes where place like '%" + palce + "%'")
    rows1 = data1.fetchall()
    data2 = c.execute("select * from quakes")
    rows = data2.fetchall()
    res = []
    for row in rows:
        if haversine(rows1[0][1], rows1[0][2], row[1], row[2]) > float(key1_dis) and haversine(rows1[0][1], rows1[0][2],
                                                                                               row[1], row[2]) < float(
            key2_dis):
            res.append(row)
    return render_template("admin/Quiz2/Q2-9 SearchByDistance.html", data=res, key1_dis=key1_dis, key2_dis=key2_dis,
                           palce=palce)


# Assignment2
# Assignment2- Search All data
@application.route("/allmonth/list/", methods=["GET"])
def earthquake_list():
    earthquakeDB = sqlite3.connect(DATABASE)
    data = earthquakeDB.execute("select * from allmonth limit 0,100")
    return render_template("admin/Assignment2/earthquake_list.html", data=data)


# Assignment2-1-查询大于某个值的数据
@application.route("/allmonth/search/mag/", methods=["GET"])
def search_mag():
    key = request.args.get("key", "8")
    earthquakeDB = sqlite3.connect(DATABASE)
    data = earthquakeDB.execute("select * from allmonth where mag > " + key)
    count = earthquakeDB.execute("select count(*) from allmonth where mag > " + key)
    return render_template("admin/Assignment2/1-SearchByMag.html", data=data, magvalue=key, count=count)


# 2-通过实践范围和mag范围查找
@application.route("/allmonth/search/mag_time/", methods=["GET"])
def search_mag_time():
    key1_mag = request.args.get("mag1", "3")
    key2_mag = request.args.get("mag2", "10")
    key1_time = request.args.get("time1", "2019-06-02")
    key2_time = request.args.get("time2", "2019-06-08")
    earthquakeDB = sqlite3.connect(DATABASE)
    data = earthquakeDB.execute(
        "select * from allmonth where mag > " + key1_mag + " AND mag < " + key2_mag + " and time <'" + key1_time + "' or time > '" + key2_time + "'")

    return render_template("admin/Assignment2/2-SearchByMag&&Time.html", data=data, key1_mag=key1_mag,
                           key2_mag=key2_mag,
                           key1_time=key1_time, key2_time=key2_time)


# 3-通过经纬度和距离范围搜索
@application.route("/allmonth/search/distance/la", methods=["GET"])
def search_distance_la_lo():
    key_latitude = request.args.get("latitude", "30")
    key_longitude = request.args.get("longitude", "-120")
    key1_dis = request.args.get("dis1", "50")
    key2_dis = request.args.get("dis2", "300")
    earthquakeDB = sqlite3.connect(DATABASE)
    c = earthquakeDB.cursor()
    data = c.execute("select * from allmonth")
    rows = data.fetchall()
    res = []
    for row in rows:
        if haversine(key_latitude, key_longitude, row[1], row[2]) > float(key1_dis) and haversine(key_latitude,
                                                                                                  key_longitude, row[1],
                                                                                                  row[2]) < float(
            key2_dis):
            res.append(row)
    count = len(res)
    return render_template("admin/Assignment2/3-SearchByDistance.html", data=res, count=count,
                           key_latitude=key_latitude,
                           key_longitude=key_longitude, key1_dis=key1_dis, key2_dis=key2_dis)


# 4-大于mag的都是夜晚吗
@application.route("/allmonth/mag/night/", methods=["GET"])
def mag_night():
    mag = request.args.get("key", "8")
    earthquakeDB = sqlite3.connect(DATABASE)
    c = earthquakeDB.cursor()
    data = c.execute(
        "select * from allmonth WHERE mag >" + mag)
    rows = data.fetchall()
    count_night = 0
    count_day = 0
    for row in rows:
        if night_calculate(row[2], row[0]):
            count_night += 1
        else:
            count_day += 1
    if count_night > count_day:
        flag = "Yes"
    else:
        flag = "No"
    count = len(rows)
    return render_template("admin/Assignment2/4-MagNight.html", data=rows, count=count, mag=mag, flag=flag,
                           count_day=count_day, count_night=count_night)


# assignment3
@application.route("/allmonth/random/search/mag/", methods=["GET"])
def random_search_mag():
    starttime = sqlite3.datetime.datetime.now()
    earthquakeDB = sqlite3.connect(DATABASE)
    data1 = []
    for i in range(1, 1000):
        mag = random.uniform(0, 8)
        data = earthquakeDB.execute("select * from allmonth where mag =" + str(mag))
    endtime = sqlite3.datetime.datetime.now()
    sqltime = endtime - starttime

    starttime1 = sqlite3.datetime.datetime.now()
    for i in range(1, 1000):
        mag = round(random.uniform(0, 8), 1)
        if r.hexists("data", str(mag)):
            data = r.hget("data", str(mag))
        else:
            data = earthquakeDB.execute("select * from allmonth where mag =" + str(mag))
            data = data.fetchall()
            r.hset("data", str(mag), str(data))
    endtime1 = sqlite3.datetime.datetime.now()
    redistime = endtime1 - starttime1
    return render_template("admin/Assignment3/1-random.html", sqltime=sqltime, redistime=redistime)


@application.route("/allmonth/range/mag", methods=["GET"])
def range_page():
    key1 = None
    key2 = None
    key1 = request.args.get("mag1")
    key2 = request.args.get("mag2")
    sqltime = None
    redistime = None
    if key1 != None:
        starttime = sqlite3.datetime.datetime.now()
        earthquakeDB = sqlite3.connect(DATABASE)
        data = earthquakeDB.execute("select * from allmonth where mag >=" + str(key1) + " and mag <= " + str(key1))
        endtime = sqlite3.datetime.datetime.now()
        sqltime = endtime - starttime

        starttime1 = sqlite3.datetime.datetime.now()
        mag = str(key1) + "-" + str(key2)
        if r.hexists("quakes1", mag):
            data = r.hget("quakes1", mag)
        else:
            data = earthquakeDB.execute("select * from allmonth where mag >" + str(key1) + " and mag <" + str(key2))
            data = data.fetchall()
            r.hset("quakes1", str(mag), str(data))
        endtime1 = sqlite3.datetime.datetime.now()
        redistime = endtime1 - starttime1
    return render_template("admin/Assignment3/2-range.html", sqltime=sqltime, redistime=redistime, key1=key1, key2=key2)

#Quiz3
#输入两个deptherror和一个longitude
@application.route("/quake3/quiz3-1/", methods=["GET"])
def list_la():
    key1_depthError=request.args.get("dep1")
    key2_depthError=request.args.get("dep2")
    longitude=request.args.get("long")
    if key1_depthError!=None:
        earthquakeDB=sqlite3.connect(DATABASE)
        data=earthquakeDB.execute("select * from quake6 where depthError >= "+ str(key1_depthError)+" and depthError <= "+ str(key2_depthError)+" and longitude >"+str(longitude))
        count=earthquakeDB.execute("select count(*) from quake6 where depthError >= "+ str(key1_depthError)+" and depthError <= "+ str(key2_depthError)+" and longitude >"+str(longitude))
        return render_template("admin/Quiz3/Q3-5 list_depthError.html",data=data,count=count,key1_depthError=key1_depthError,key2_depthError=key2_depthError)
    return render_template("admin/Quiz3/Q3-5 list_depthError.html")

@application.route("/quake3/random/search/sql/", methods=["GET"])
def random_search_sql():
    key1_la = request.args.get("la1")
    key2_la = request.args.get("la2")
    times = request.args.get("times")
    data=[]
    if key1_la!=None:
        earthquakeDB = sqlite3.connect(DATABASE)
        for i in range(int(times)):
            data1=[]
            starttime = sqlite3.datetime.datetime.now()
            key1= round(random.uniform(float(key1_la), float(key2_la)), 1)
            key2= round(random.uniform(float(key1_la), float(key2_la)), 1)
            temp=key1
            if key1>key2:
                key1=key2
                key2=temp
            earthquakeDB = sqlite3.connect(DATABASE)
            count = earthquakeDB.execute(
                "select count(*) from quake6 where depth >= " + str(key1) + " and depth <= " + str(key2))
            count=count.fetchall()
            endtime = sqlite3.datetime.datetime.now()
            time=endtime-starttime
            data1.append(i+1)
            data1.append(count[0][0])
            data1.append(key1)
            data1.append(key2)
            data1.append(time)
            data.append(data1)
        print(data)
    return render_template("admin/Quiz3/Q3-6 sql_time.html",data=data,key1_la=key1_la,key2_la=key2_la)

@application.route("/quake3/random/search/redis/", methods=["GET"])
def random_search_redis():
    key1_la = request.args.get("la1")
    key2_la = request.args.get("la2")
    times = request.args.get("times")
    data=[]
    if key1_la!=None:
        earthquakeDB = sqlite3.connect(DATABASE)
        for i in range(int(times)):
            data1=[]
            starttime = sqlite3.datetime.datetime.now()
            key1= round(random.uniform(float(key1_la), float(key2_la)), 1)
            key2= round(random.uniform(float(key1_la), float(key2_la)), 1)
            temp=key1
            if key1>key2:
                key1=key2
                key2=temp
            la = str(key1) + "-" + str(key2)
            if r.hexists("las5", la):
                count = r.hget("las5", la)
            else:
                earthquakeDB = sqlite3.connect(DATABASE)
                count = earthquakeDB.execute(
                    "select count(*) from quake6 where depth >= " + str(key1) + " and depth <= " + str(key2))
                count = count.fetchall()
                count=count[0][0]
                r.hset("las5", str(la), str(count))
            endtime = sqlite3.datetime.datetime.now()
            time=endtime-starttime
            data1.append(i+1)
            data1.append(count)
            data1.append(key1)
            data1.append(key2)
            data1.append(time)
            data.append(data1)
    return render_template("admin/Quiz3/Q3-7 redis_time.html",data=data,key1_la=key1_la,key2_la=key2_la)

@application.route("/quake3/random/SqlorRedis", methods=["GET"])
def sql_or_redis():
    key1_la = request.args.get("la1")
    key2_la = request.args.get("la2")
    times = request.args.get("times")
    flag=request.args.get("flag")
    database=None
    data=[]
    time=None
    if key1_la!=None:
        earthquakeDB = sqlite3.connect(DATABASE)
        #sql
        if int(flag)==2:
            starttime = sqlite3.datetime.datetime.now()
            for i in range(int(times)):
                data1 = []
                key1 = round(random.uniform(float(key1_la), float(key2_la)), 1)
                key2 = round(random.uniform(float(key1_la), float(key2_la)), 1)
                temp = key1
                if key1 > key2:
                    key1 = key2
                    key2 = temp
                la = str(key1) + "-" + str(key2)
                if r.hexists("las3", la):
                    count = r.hget("las3", la)
                else:
                    earthquakeDB = sqlite3.connect(DATABASE)
                    count = earthquakeDB.execute(
                        "select count(*) from quake6 where depth >= " + str(key1) + " and depth <= " + str(key2))
                    count = count.fetchall()
                    count=count[0][0]
                    r.hset("las3", str(la), str(count))
                data1.append(i + 1)
                data1.append(count)
                data1.append(key1)
                data1.append(key2)
                print(count)
                data.append(data1)
            endtime = sqlite3.datetime.datetime.now()
            time = endtime - starttime
            database="Redis"
        elif int(flag)==1:
            starttime = sqlite3.datetime.datetime.now()
            for i in range(int(times)):
                data1 = []
                key1 = round(random.uniform(float(key1_la), float(key2_la)), 1)
                key2 = round(random.uniform(float(key1_la), float(key2_la)), 1)
                temp = key1
                if key1 > key2:
                    key1 = key2
                    key2 = temp
                earthquakeDB = sqlite3.connect(DATABASE)
                count = earthquakeDB.execute(
                    "select count(*) from quake6 where depth >= " + str(key1) + " and depth <= " + str(key2))
                count=count.fetchall()
                data1.append(i + 1)
                data1.append(count[0][0])
                data1.append(key1)
                data1.append(key2)
                data.append(data1)
            endtime = sqlite3.datetime.datetime.now()
            time = endtime - starttime
            database="Sql"
    return render_template("admin/Quiz3/Q3-8 sql&redis.html",time=time,database=database,key1_la=key1_la,key2_la=key2_la,data=data)

# 作业4
# 柱状图
@application.route("/chart/histogram/", methods=["GET"])
def histogram():
    key1 = None
    key2 = None
    label = []
    data = []
    key1 = request.args.get("mag1")
    key2 = request.args.get("mag2")
    increment = request.args.get("increment")
    if key1 != None:
        earthquakeDB = sqlite3.connect(DATABASE)
        listlabel = []
        count2 = []
        mag = float(key1)
        for mag in range(int(float(key1) * 10), int(float(key2) * 10), int(float(increment) * 10)):
            listlabel.append(mag / 10)
        for v in listlabel:
            count = earthquakeDB.execute(
                "select count (*) from quakes where mag > " + str(v) + " AND mag < " + str(v + float(increment)))
            count1 = count.fetchall()
            count2.append(count1)
        data = []
        for i in range(len(count2)):
            data.append(count2[i][0][0])
        listlabel.append(float(key2))
        label = []
        for i in range(len(listlabel) - 1):
            label.append(str(listlabel[i]) + "-" + str(listlabel[i + 1]))
        print(label)
        print(data)
        print(type(data))
        print(type(label))
    return render_template("admin/Assignment4/1-histogram.html", label=label, data=data)


# 饼图
@application.route("/chart/pie/", methods=["GET"])
def pie():
    label = ["day", "night"]
    mag = request.args.get("key", "8")
    earthquakeDB = sqlite3.connect(DATABASE)
    c = earthquakeDB.cursor()
    data = c.execute(
        "select * from quakes WHERE mag >" + mag)
    rows = data.fetchall()
    count_night = 0
    count_day = 0
    for row in rows:
        if night_calculate(row[2], row[0]):
            count_night += 1
        else:
            count_day += 1
    if count_night > count_day:
        flag = "Yes"
    else:
        flag = "No"
    data = []
    data.append(count_day)
    data.append(count_night)
    print(data)
    print(label)
    print(type(data))
    print(type(label))
    return render_template("admin/Assignment4/2-pie.html", data=data, label=label, flag=flag, count_night=count_night,
                           count_day=count_day,len=2)


# 折线图
@application.route("/chart/line/", methods=["GET"])
def line():
    key1 = None
    key2 = None
    label = []
    data = []
    key1 = request.args.get("mag1")
    key2 = request.args.get("mag2")
    increment = request.args.get("increment")
    if key1 != None:
        earthquakeDB = sqlite3.connect(DATABASE)
        listlabel = []
        count2 = []
        mag = float(key1)
        for mag in range(int(float(key1) * 10), int(float(key2) * 10), int(float(increment) * 10)):
            listlabel.append(mag / 10)
        for v in listlabel:
            count = earthquakeDB.execute(
                "select count (*) from quakes where mag > " + str(v) + " AND mag < " + str(v + float(increment)))
            count1 = count.fetchall()
            count2.append(count1)
        data = []
        for i in range(len(count2)):
            data.append(count2[i][0][0])
        listlabel.append(float(key2))
        label = []
        for i in range(len(listlabel) - 1):
            label.append(str(listlabel[i]) + "-" + str(listlabel[i + 1]))
    return render_template("admin/Assignment4/3-line.html", label=label, data=data)


@application.route("/chart/scatter/", methods=["GET"])
def scatter():
    place = None
    key1_dis = None
    key2_dis = None
    label = []
    data = []
    _data = []
    palce = request.args.get("place")
    key1_dis = request.args.get("dis1")
    key2_dis = request.args.get("dis2")
    if key1_dis != None:
        earthquakeDB = sqlite3.connect(DATABASE)
        c = earthquakeDB.cursor()
        data1 = c.execute("select * from quakes where place like '%" + palce + "%'")
        rows1 = data1.fetchall()
        data2 = c.execute("select * from quakes")
        rows = data2.fetchall()
        for row in rows:
            if haversine(rows1[0][1], rows1[0][2], row[1], row[2]) > float(key1_dis) and haversine(rows1[0][1],
                                                                                                   rows1[0][2],
                                                                                                   row[1],
                                                                                                   row[2]) < float(
                key2_dis):
                _data.append(row[3])
                _data.append(row[4])
                data.append(_data)
                _data = []
        print(data)
        print(type(data))
    return render_template("admin/Assignment4/4-scatter.html", data=data)

#统计时间段内的数量
@application.route("/quakes/count/time/", methods=["GET"])
def count_time_line():
    key1_time = request.args.get("time1")
    key2_time = request.args.get("time2")
    label=None
    count1=None
    if key1_time!=None:
        earthquakeDB = sqlite3.connect(DATABASE)
        label = []
        count1 = []
        time = key1_time
        while time <= key2_time:
            label.append(time)
            time1 = time[0:9] + str(int(time[9]) + 1)
            count = earthquakeDB.execute(
                "select count(*) from quakes where  time >='" + time + "' and time < '" + time1 + "'")
            time = time1
            count1.append(count.fetchall()[0][0])
            print(count.fetchall())
        print(label)
        print(count1)
    return render_template("admin/Assignment4/5-time-line.html", label=label,count1=count1)

#quiz4
@application.route("/quiz4/list/", methods=["GET"])
def quiz_list():
    earthquakeDB = sqlite3.connect(DATABASE)
    data=[]
    data1=[]
    state1=earthquakeDB.execute("select StateName from voting where TotalPop >=" +"2000"+" and TotalPop <="+"8000");
    state2=earthquakeDB.execute("select StateName from voting where TotalPop >=" +str(8000)+" and TotalPop <="+str(40000));
    state1=state1.fetchall()
    state2=state2.fetchall()
    return render_template("admin/Quiz4/Q4-5 list.html",state1=state1,state2=state2)

@application.route("/quiz4/pie/", methods=["GET"])
def quiz_pie():
    key1 = request.args.get("key1")
    count=None
    if key1 !=None:
        label=[]
        count=[]
        earthquakeDB = sqlite3.connect(DATABASE)
        max=earthquakeDB.execute("select max(TotalPop) from voting")
        max=max.fetchall()[0][0]/1000
        cur=0
        label1 = []
        while (cur+float(key1))<max:
            label1.append(str(cur)+"-"+str(cur+float(key1)))
            count1=earthquakeDB.execute("select count(*) from voting where TotalPop>="+str(cur*1000)+" and TotalPop <"+str((cur+float(key1))*1000));
            count1=count1.fetchall()[0][0]
            print(count1,cur)
            cur=cur+float(key1)
            count.append(count1)
            label.append(label1)
        print(count)
        return render_template("admin/Quiz4/Q4-6 pie.html", label=label1, count=count)
    return render_template("admin/Quiz4/Q4-6 pie.html")

@application.route("/quiz4/scatter/", methods=["GET"])
def quiz_scatter():
    key1 = request.args.get("key1")
    key2 = request.args.get("key2")
    people=None
    print(type(key1))
    data=None
    if key1!=None:
        key1=float(key1)*1000
        key1=str(key1)
        key2=str(float(key2)*1000)
        earthquakeDB = sqlite3.connect(DATABASE)
        people=earthquakeDB.execute("select TotalPop/1000,Registerd/1000 from voting where TotalPop >="+key1+" and TotalPop<="+key2)
        people=people.fetchall()
    return render_template("admin/Quiz4/Q4-7 scatter.html",data=people)

@application.route("/Quiz/count/line/", methods=["GET"])
def count_line_quiz():
    key1 = request.args.get("key1")
    key2 = request.args.get("key2")
    label=None
    data=None
    Y=None
    X=None
    if key1!=None:
        key1=int(key1)
        key2=int(key2)
        label=[]
        Y=[]
        X=[]
        key=key1
        while key<=key2:
            label.append(key)
            Y.append(key)
            x=(key*key*key)%10
            X.append(x)
            key=key+1
    return render_template("admin/Quiz4/Q4-8 line.html", label=Y, data=X)

#作业5
@application.route("/Assignment5/list/", methods=["GET"])
def Assignment5_list():
    earthquakeDB = sqlite3.connect(DATABASE)
    data=earthquakeDB.execute("select * from titanic3")
    count=earthquakeDB.execute("select count(*) from titanic3")
    return render_template("admin/Assignment5/1-list.html",data=data,count=count)

def distEclud(x,y):
    return np.sqrt(np.sum((x-y)**2))

@application.route("/Assignment5/cluster/",methods=["GET"])
def Assignment5_cluster():
    key=request.args.get("key")
    cluster=[]
    inter=None
    if key!=None:
        earthquakeDB = sqlite3.connect(DATABASE)
        data = earthquakeDB.execute("select age,sibsp from titanic3 where sibsp>=0 and age>=0")
        data = data.fetchall()
        kmeans = KMeans(n_clusters=int(key))
        kmeans.fit(data)
        label = kmeans.labels_#分类
        quantity = pd.Series(label).value_counts()#每个类别中的数据量
        centers=kmeans.cluster_centers_  #中心点
        dis=[]
        for i in range(len(quantity)):
            distance=0
            for j in range(len(label)):
                if label[j]==i:
                    distance=distance+distEclud(centers[i],data[j])
            dis.append(distance)
        for i in range(len(quantity)):
            _cluster=[]
            _cluster.append(i)
            _cluster.append(centers[i])
            _cluster.append(quantity[i])
            _cluster.append(dis[i])
            cluster.append(_cluster)
        inter=kmeans.inertia_
    return render_template("admin/Assignment5/2-cluster.html",cluster=cluster,inter=inter)

#Quiz5
@application.route("/Quiz5/cluster/5",methods=["GET"])
def Quiz5_cluster5():
    cluster1=[]
    cluster2=[]
    earthquakeDB = sqlite3.connect(DATABASE)
    starttime1 = sqlite3.datetime.datetime.now()
    data1=earthquakeDB.execute("select wealth,Height from minnow where wealth>=0 and Height>=0")
    data1=data1.fetchall()
    kmeans = KMeans(n_clusters=4)
    kmeans.fit(data1)
    label = kmeans.labels_  # 分类
    quantity = pd.Series(label).value_counts()  # 每个类别中的数据量
    centers = kmeans.cluster_centers_  # 中心点
    for i in range(len(quantity)):
        _cluster = []
        _cluster.append(i)
        _cluster.append(centers[i])
        _cluster.append(quantity[i])
        cluster1.append(_cluster)
    endtime1 = sqlite3.datetime.datetime.now()
    cluster1time=endtime1-starttime1

    starttime2 = sqlite3.datetime.datetime.now()
    data2 = earthquakeDB.execute("select Age,Fare from minnow where Age>=0 and Fare>=0")
    data2 = data2.fetchall()
    kmeans = KMeans(n_clusters=3)
    kmeans.fit(data2)
    label = kmeans.labels_  # 分类
    quantity = pd.Series(label).value_counts()  # 每个类别中的数据量
    centers = kmeans.cluster_centers_  # 中心点
    for i in range(len(quantity)):
        _cluster = []
        _cluster.append(i)
        _cluster.append(centers[i])
        _cluster.append(quantity[i])
        cluster2.append(_cluster)
    endtime2 = sqlite3.datetime.datetime.now()
    cluster2time = endtime2 - starttime2
    return render_template("admin/Quiz5/5-cluster.html",cluster1=cluster1,cluster1time=cluster1time,cluster2=cluster2,cluster2time=cluster2time)

@application.route("/Quiz5/options/6",methods=["GET"])
def Quiz5_option():
    features=["CabinNum","Lat","Age","Wealth","Education","fare"]
    cluster1=[]
    earthquakeDB = sqlite3.connect(DATABASE)
    list=["CabinNum","Lat"]
    list = request.values.getlist("feature")
    n_cluster=request.args.get("n_cluster")
    key11=request.args.get("range11")
    key12=request.args.get("range12")
    key21=request.args.get("range21")
    key22=request.args.get("range22")
    count=None
    if len(list)>1:
        data1 = earthquakeDB.execute(
            "select " + list[0] + "," + list[1] + " from minnow where " + list[0] + " >= "+str(key11)+" and "+list[0]+" <= "+str(key12)+" and "+list[1]+" >= "+str(key21)+" and "+list[1]+" <= "+str(key22))
        data1 = data1.fetchall()
        count = earthquakeDB.execute(
            "select count(*) from minnow where " + list[0] + " >= " + str(key11) + " and " +
            list[0] + " <= " + str(key12) + " and " + list[1] + " >= " + str(key21) + " and " + list[1] + " <= " + str(
                key22))
        count=count.fetchall()[0][0]
        print(data1)
        kmeans = KMeans(n_clusters=int(n_cluster))
        kmeans.fit(data1)
        label = kmeans.labels_  # 分类
        quantity = pd.Series(label).value_counts()  # 每个类别中的数据量
        centers = kmeans.cluster_centers_  # 中心点
        dis = []
        for i in range(len(quantity)):
            maxdistance = 0
            for j in range(len(label)):
                if label[j] == i:
                    curdis = distEclud(centers[i], data1[j])
                    print(curdis)
                    if curdis > maxdistance:
                        maxdistance = curdis
            dis.append(maxdistance)
        for i in range(len(quantity)):
            _cluster = []
            _cluster.append(i)
            _cluster.append(centers[i])
            _cluster.append(quantity[i])
            _cluster.append(dis[i])
            cluster1.append(_cluster)
    return render_template("admin/Quiz5/6-option.html",features=features,cluster1=cluster1,list=list,count=count)


@application.route("/Quiz5/centroids/7",methods=["GET"])
def Quiz5_centroid():
    features = ["CabinNum", "Lat", "Age", "Wealth", "Education", "fare"]
    cluster1 = []
    earthquakeDB = sqlite3.connect(DATABASE)
    list = ["CabinNum", "Lat"]
    list = request.values.getlist("feature")
    n_cluster = request.args.get("n_cluster")
    key1=request.args.get("key1")
    key2=request.args.get("key2")
    data=[]
    if key1!=None:
        data1 = earthquakeDB.execute(
            "select " + list[0] + "," + list[1] + " from minnow where " + list[0] + " >=0 and " + list[1] + " >=0")
        data1 = data1.fetchall()
        finaldata=earthquakeDB.execute("select * from minnow where "+ list[0] + " >=0 and " + list[1] + " >=0")
        finaldata=finaldata.fetchall()
        kmeans = KMeans(n_clusters=int(n_cluster))
        kmeans.fit(data1)
        label = kmeans.labels_  # 分类
        quantity = pd.Series(label).value_counts()  # 每个类别中的数据量
        centers = kmeans.cluster_centers_  # 中心点
        dis = []
        key=[]
        key.append(int(key1))
        key.append(int(key2))
        mindis=10000
        flag=None
        for i in range(int(n_cluster)):
            cen_distance=distEclud(centers[i],key)
            if cen_distance<=mindis:
                mindis=cen_distance
                flag=i
        print(flag)
        data=[]
        for i in range(len(label)):
            if label[i]==flag:
                data.append(finaldata[i])
    return render_template("admin/Quiz5/7-centroids.html",features=features,data=data)

counter = Value('i', -1)
@application.route("/Quiz5/chart/8",methods=["GET"])
def Quiz5_chart():
    features=["CabinNum","Lat","Age","Wealth","Education","fare"]
    cluster1=[]
    earthquakeDB = sqlite3.connect(DATABASE)
    list=["CabinNum","Lat"]
    list = request.values.getlist("feature")
    n_cluster=request.args.get("n_cluster")
    quantity=[]
    centers1=[]
    if len(list)>1:
        data1 = earthquakeDB.execute(
            "select " + list[0] + "," + list[1] + " from minnow where " + list[0] + " >=0 and " + list[1] + " >=0")
        data1 = data1.fetchall()
        kmeans = KMeans(n_clusters=int(n_cluster))
        kmeans.fit(data1)
        label = kmeans.labels_  # 分类
        quantity = pd.Series(label).value_counts()  # 每个类别中的数据量
        centers = kmeans.cluster_centers_  # 中心点
        quantity=np.mat(quantity).tolist()
        centers=np.mat(centers).tolist()
        centers1=[]
        for i in centers:
            cen = []
            for k in i:
                cen.append(round(k,1))
            centers1.append(cen)
        quantity=quantity[0]
        print(centers1)
        print(quantity)
    return render_template("admin/Quiz5/8-chart.html",features=features,list=list,quantity=quantity,centers=centers1)

#Quiz6
# @application.route("/Quiz6/6-pic",methods=["GET","POST"])
# def show_picture1():
#     starttime = sqlite3.datetime.datetime.now()
#     endtime = sqlite3.datetime.datetime.now()
#     time=endtime-starttime
#     time1=str(starttime)
#     pointtime=int(time1[len(time1)-1])
#     if pointtime%2==0:
#         picture="a.jpg"
#     else:
#         picture="b.jpg"
#     earthquakeDB = sqlite3.connect(DATABASE)
#     earthquakeDB.execute("INSERT INTO jmeter (starttime,endtime,elapsedtime,pic) VALUES (?,?,?,?)",(str(starttime),str(endtime),str(time),str(picture)))
#     earthquakeDB.commit()
#     return render_template("admin/Quiz6/Q6-6pic.html",starttime=starttime,endtime=endtime,picture=picture,time=time)


@application.route("/Quiz6/6-pic",methods=["GET","POST"])
def show_picture():
    starttime = sqlite3.datetime.datetime.now()
    earthquakeDB = sqlite3.connect(DATABASE)
    year=["2010","2011","2012","2013","2014","2015","2016","2017","2018"]
    data=earthquakeDB.execute("select * from population where State='Texas'or State='Louisiana' or State='Oklahoma'")
    data=data.fetchall()
    finaldata=[]
    for i in range(len(data)):#3
        _final=data[i][1:len(data[i])-1]
        finaldata.append(_final)
    print(finaldata)
    print(len(finaldata))
    finaldata=np.mat(finaldata).T
    finaldata=finaldata.tolist()
    ffinaldata=[]
    for i in range(len(finaldata)):
        _ff=[]
        _ff.append(year[i])
        _ff.append(finaldata[i])
        ffinaldata.append(_ff)
    forfinal=[]
    while counter.value<8:

        if counter.value <7:
            counter.value=counter.value+1
            forfinal=ffinaldata[counter.value]
        else:
            counter.value = 0
            forfinal=ffinaldata[counter.value]
        endtime = sqlite3.datetime.datetime.now()
        time = endtime - starttime
        print(forfinal)

        earthquakeDB.execute("INSERT INTO jmeter (starttime,endtime,elapsedtime) VALUES (?,?,?)",
                             (str(starttime), str(endtime), str(time)))
        earthquakeDB.commit()
        return render_template("admin/Quiz6/Q6-6pic.html", starttime=starttime, endtime=endtime, time=time,
                               finaldata=forfinal)

@application.route("/Quiz6/8-pic",methods=["GET","POST"])
def bonus():
    earthquakeDB = sqlite3.connect(DATABASE)
    data=earthquakeDB.execute("select * from jmeter")
    return render_template("/admin/Quiz6/Q6-8 bon.html",data=data)

#Quiz7
@application.route("/Quiz7/5-studentview",methods=["GET","POST"])
def studentView():
    id = request.args.get('id')
    session["id"] = id
    conn = sqlite3.connect('myDb.db')
    if id!=None:
        c = conn.cursor()
        c.execute(
            "select * from quiz7courstu left join quiz7fall where quiz7courstu.Course=quiz7fall.Course and quiz7courstu.Section=quiz7fall.Section and IdNum='" + id+"'")
        rows = c.fetchall()
        c.execute("select * from quiz7fall")
        rows2=c.fetchall()
        return render_template("admin/Quiz7/Q7-5 studentview.html", rows=rows,id=id,rows2=rows2)
    return render_template("admin/Quiz7/Q7-5 studentview.html")

@application.route("/Quiz7/5-studentview/roll/<int:course><int:section>/", methods=["GET"])
def student_roll(course=None,section=None):
    id=session["id"]
    print(course)
    print(id)
    print(section)
    earthquakeDB = sqlite3.connect(DATABASE)
    count=earthquakeDB.execute("select count(*) from quiz7courstu where IdNum="+str(id))
    count=count.fetchall()
    count=count[0][0]
    if count<3:
        key=True
        data=earthquakeDB.execute("select Course,Section from quiz7courstu where IdNum="+id)
        data=data.fetchall()
        print(data)
        for curdata in data:
            print(curdata)
            if curdata[0]==course and curdata[1]==section:
                key=False
        print(key)
        if key:
            earthquakeDB.execute("insert  OR IGNORE into quiz7courstu values (?,?,?)",
                                 (str(course), str(id), str(section)))
            earthquakeDB.commit()
            flag = None
    else:
        flag="You can not roll in the course!"
    return redirect(url_for('studentView',id=id))

@application.route("/Quiz7/6-adview/", methods=["GET"])
def Admin_view():
    course=request.args.get("course")
    section=request.args.get("section")
    if course!=None:
        earthquakeDB = sqlite3.connect(DATABASE)
        data=earthquakeDB.execute("select * from quiz7courstu left join quiz7stu where quiz7courstu.IdNum=quiz7stu.IdNum and Course='" + course+"' and Section= '"+section+"'" )
        data=data.fetchall()
        print(data)
        return render_template("admin/Quiz7/Q7-6 Adminview.html",data=data)
    return render_template("admin/Quiz7/Q7-6 Adminview.html")

global count
count=0
@application.route('/Quiz7/7-view/', methods=['GET'])
def ques8():
    time=sqlite3.datetime.datetime.now()
    global count
    count+=1
    return render_template("admin/Quiz7/Q7-7.html", time=time,count=count)


if __name__ == "__main__":
    # if push to cloud, need close debug
    #application.run('0.0.0.0', port=port, debug=False)
    application.debug = True
    application.run(debug=True)
