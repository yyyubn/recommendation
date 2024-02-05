# -*- coding: utf-8 -*-

import numpy as np
import boto3
from flask import Flask, request
from flask_cors import CORS
import json

def get_secret(secret_name, region_name='ap-northeast-2'):
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret_value = response['SecretString']
    return json.loads(secret_value)
secret_value = get_secret(secret_name='secret/aws')

if secret_value:
    aws_access_key_id = secret_value.get("aws.accessKey")
    aws_secret_access_key = secret_value.get("aws.secretKey")


app = Flask(__name__)
CORS(app)


#Dynamodb 연동
dynamodb = boto3.resource('dynamodb',region_name='ap-northeast-2')
table = dynamodb.Table('restaurant')


# Amazon Translate 클라이언트 생성
translate_client = boto3.client('translate',region_name='ap-northeast-2')



#-------------------------------------------------------------------------------------
# 매개변수로 넘어온 텍스트를 반환한다. AWS 번역기능
def translate_text(text, target_language):
    translate_response = translate_client.translate_text(
        Text= text, 
        SourceLanguageCode='ko',  # 가게 이름이 한국어로 되어 있다고 가정
        TargetLanguageCode=target_language
    )
    return translate_response['TranslatedText']
#-------------------------------------------------------------------------------------




#-------------------------------------------------------------------------------------
def translate_store_info(store_info: dict, target_language): # target_language는 유저정보 받아오는 data에 따라 바뀔 것
    translated_store = {}
    if store_info:
        # 가게 정보에서 번역 대상 텍스트 추출 (이 예제에서는 'name' 필드를 번역합니다)
        
        name_to_translate = store_info.get('name', '')
        category_to_translate = store_info.get('category', '')


        translated_store['id']=store_info.get('id', '')
        translated_store['photo']=store_info.get('photo', '')
        translated_store['name'] = translate_text(name_to_translate, target_language)
        translated_store['category'] = translate_text(category_to_translate, target_language)

    return translated_store
#-------------------------------------------------------------------------------------


def get_items_by_store_id_existence(table):
    # DynamoDB 테이블에서 store_id 속성이 존재하는 아이템을 가져오기
    response = table.scan(
        FilterExpression='attribute_exists(id)'
    )

    # DynamoDB 아이템 리스트에서 데이터 추출
    dynamodb_items = response.get('Items', [])

    return dynamodb_items



@app.route('/recomm', methods=['POST','GET'])
def recommendation222():
    items = get_items_by_store_id_existence(table)

    data_list = []
        
    latitude=request.headers.get('La')
    longitude=request.headers.get('Lo')
    target_language=request.headers.get('Language')
    location=[latitude, longitude]
    location=list(map(float, location))


    for item in items:
        data = {
            'id': item.get('id'),
            'photo': item.get('photo'),
            'name': item.get('name'),
            'category': item.get('category'),
            'coodinate': item.get('coodinate'),
        }
        data_list.append(data)

    all_documents_dic={}
    coordinates_array=[]


    for i in range (len(data_list)):
        all_documents_dict=data_list[i]
        name_coordinate_dict = {all_documents_dict.get("name"): all_documents_dict.get("coodinate")}
        coordinates_array.extend([list(map(float, value.split(', '))) for value in name_coordinate_dict.values()])
        

    nearest_store=[] #거리차이가 담길 리스트
    #user_location = get_user_location()
    coordinates = np.array(coordinates_array)
    print(coordinates.shape)
    for i in range (len(coordinates_array)): #위도 경도 담긴 만큼 돌거임
        location = np.array(location)
        print(location.shape)
        result=np.abs(np.sum(np.array(location)-np.array(coordinates_array[i])))
        nearest_store.append(result) #이 리스트에 그럼 거리 차이 담기는거



    for i, d in enumerate(data_list):
        if 'coodinate' in d:
            d['coodinate'] = nearest_store[i]


    sorted_list = sorted(data_list, key=lambda x: x['coodinate'])
    result_store = sorted_list[:3]
    names_list = [item['name'] for item in result_store]
    #-------------------------------------

    last=[]
    #차례대로 출력

    for i in range(len(result_store)):
        store_info = next((item for item in data_list if item['name'] == names_list[i]), None)
        last.append(translate_store_info(store_info,target_language))


    return last

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)