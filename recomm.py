from geopy.geocoders import Nominatim
import geocoder
from pymongo import MongoClient
import numpy as np
import boto3
import os
from dotenv import load_dotenv
from flask import Flask, request
from utils.t_print import print_test
import json

load_dotenv()
#aws_access_key_id = os.environ.get('aws_access_key_id')
#aws_secret_access_key = os.environ.get('aws_secret_access_key')


def get_secret(secret_name, region_name='ap-northeast-2'):
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret_value = response['SecretString']
    return json.loads(secret_value)
    # try:
    #     response = client.get_secret_value(SecretId=secret_name)
    #     secret_value = response['SecretString']
    #     return json.loads(secret_value)
    # except Exception as e:
    #     print(f"Secret 값을 가져오는 중 에러 발생: {e}")
    #     return None
secret_value = get_secret(secret_name='secret/aws')

if secret_value:
    # "a" 필드의 값 가져오기
    aws_access_key_id = secret_value.get("aws.accessKey")
    aws_secret_access_key = secret_value.get("aws.secretKey")
    
    #print("Value of 'a':", a_value)

app = Flask(__name__)

#Dynamodb 연동
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2',aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
table = dynamodb.Table('omnivore')


# Amazon Translate 클라이언트 생성
translate_client = boto3.client('translate', region_name='ap-northeast-2', aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key)


#현재 사용자 위치
# def get_user_location():
#     location = geocoder.ip('me')    
#     #return np.array(location.latlng) #이 부분 이제 팡이 넘겨주는 변수로 바꾸기
#     return ([12.0, 13.0])




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


        translated_store['id']=store_info.get('store_id', '')
        translated_store['photo']=store_info.get('photo', '')
        translated_store['name'] = translate_text(name_to_translate, target_language)
        translated_store['category'] = translate_text(category_to_translate, target_language)

        # menus_to_translate

    return translated_store
#-------------------------------------------------------------------------------------


def get_items_by_store_id_existence(table):
    # DynamoDB 테이블에서 store_id 속성이 존재하는 아이템을 가져오기
    response = table.scan(
        FilterExpression='attribute_exists(store_id)'
    )

    # DynamoDB 아이템 리스트에서 데이터 추출
    dynamodb_items = response.get('Items', [])

    return dynamodb_items



@app.route('/recomm', methods=['POST','GET'])
def recommendation222():
    items = get_items_by_store_id_existence(table)

    data_list = []
    
    #Content_Length=request.headers.get('Content-Length')
    
    # latitude=request.headers.get('La')
    # longitude=request.headers.get('Lo')
    # target_language=request.headers.get('Language')
    
    # location=[latitude, longitude]


    target_language='en'
    
    location=[13.0, 12.0]

    

    for item in items:
        data = {
            'store_id': item.get('store_id'),
            'photo': item.get('photo'),
            'name': item.get('store_name'),
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
        

    #print(coordinates_array)

    nearest_store=[] #거리차이가 담길 리스트
    #user_location = get_user_location()

    for i in range (len(coordinates_array)): #위도 경도 담긴 만큼 돌거임
        result=np.abs(np.sum(location-np.array(coordinates_array[i])))
        nearest_store.append(result) #이 리스트에 그럼 거리 차이 담기는거



    for i, d in enumerate(data_list):
        if 'coodinate' in d:
            d['coodinate'] = nearest_store[i]


    sorted_list = sorted(data_list, key=lambda x: x['coodinate'])
    result_store = sorted_list[:3]
    names_list = [item['name'] for item in result_store]

    #print(result_store)

    #-------------------------------------

    last=[]
    #차례대로 출력

    #target_dict = 

    for i in range(len(result_store)):
        store_info = next((item for item in data_list if item['name'] == names_list[i]), None)
        last.append(translate_store_info(store_info,target_language))


    
    print_test()
    return last

if __name__ == '__main__':
    app.run(debug = True)
