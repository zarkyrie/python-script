"""
从face++获取图片人脸坐标信息，并插入到mysql数据库
"""
import os
import requests
import base64
import json
import pymysql

ROOT_DIR = '/Users/jhl/Downloads/old'

DETECT_URL = 'https://api-cn.faceplusplus.com/facepp/v3/detect'

API_KEY = "Xc-fBUfAfeo-UjO_WNfJ-jCw1GF9IFT-"

SECRET_KEY = "R_jnNrqpehH8ePAjJ4JuDJuLl1ZQO5Z-"


def show_pics(target, pic_list: list):
    if os.path.isfile(target):
        pic_list.append(target)
    else:
        dirs = os.listdir(target)
        for sub_dir in dirs:
            if sub_dir.startswith('.') is not True:
                show_pics(target + '/' + sub_dir, pic_list)


def request_face(file_url):
    param = dict()
    param['api_key'] = API_KEY
    param['api_secret'] = SECRET_KEY
    with open(file_url, 'rb') as f:
        base64_data = base64.b64encode(f.read())
        param['image_base64'] = base64_data
    response: requests.Response = requests.api.post(DETECT_URL, data=param)
    r_str = response.content.decode()
    d = json.loads(r_str)
    face_rectangle = d['faces'][0]['face_rectangle']
    width = face_rectangle['width']
    top = face_rectangle['top']
    left = face_rectangle['left']
    height = face_rectangle['height']
    face_str = str(top) + ',' + str(left) + ',' + \
        str(width) + ',' + str(height)
    return face_str


def insert_db(r_list: list):
    global db
    insert_sql = "insert into t_age_pic_rectangle(ethnicity,age,sex,idx,rectangle) VALUES(%s,%s,%s,%s,%s)"
    if len(r_list) != 0:
        try:
            db = pymysql.connect('47.106.115.144', 'root',
                                 '1234abcd', 'face_secret')
            cursor = db.cursor()
            cursor.executemany(insert_sql, r_list)
            db.commit()
        except Exception as ex:
            db.rollback()
            print(ex)
        finally:
            db.close()


if __name__ == '__main__':
    ethnicity_list = ['assian', 'white', 'black']
    age_list = ['50', '70', '90']
    sex_list = ['m', 'f']
    idx_list = ['1', '2']
    db_list = []
    for e in ethnicity_list:
        for a in age_list:
            for s in sex_list:
                for i in idx_list:
                    rectangle = request_face(
                        '/Users/jhl/Downloads/old/' + e + '/' + s + a + '_' + i + '.jpg')
                    db_dict = (e, a, s, i, rectangle)
                    db_list.append(db_dict)
    insert_db(db_list)
