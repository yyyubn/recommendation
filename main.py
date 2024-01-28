from geopy.geocoders import Nominatim
import geocoder
from pymongo import MongoClient
import numpy as np

# MongoDB 클라이언트 생성
mongo_client = MongoClient("localhost", 27017)
db = mongo_client["menu"]
collection = db["sample"]


#현재 사용자 위치
def get_user_location():
    location = geocoder.ip('me')    
    return np.array(location.latlng)

# 모든 문서 가져오기
cursor = collection.find({})

# 결과를 담을 딕셔너리 초기화({name : coodinate, name : coodinate} 형식으로 담김)
all_documents_dict = {}

# 각 문서를 딕셔너리로 변환하여 추가
for document in cursor:
    name_coordinate_dict = {document.get("name"): document.get("coodinate")}
    all_documents_dict.update(name_coordinate_dict)

#각 가게의 위도, 경도를 담을 넘파이배열 생성
coordinates_array = np.array([list(map(float, value.split(', '))) for value in all_documents_dict.values()])

#거리 차이가 담길 리스트
nearest_store=[]

#현재 사용자의 좌표와 각 가게의 좌표 거리 차이를 계산
for i in range (len(coordinates_array)):
    result=np.abs(np.sum(get_user_location()-coordinates_array[i]))
    nearest_store.append(result)


#가장 가까운 거리 가게 이름을 뽑기위해 value값을 거리 차이 계산한 값으로 치환한다.
for key, value in zip(all_documents_dict.keys(), nearest_store):
    all_documents_dict[key] = value


#거리 차이가 가장 작은 가게 오름차순으로 정렬 후 상위 5개 추출
sorted_store = sorted(all_documents_dict, key=all_documents_dict.get)
result_store = sorted_store[:5] #이부분이 이름 추출하는 거


print(result_store)

# #차례대로 출력
# for i in range(len(result_store)):
#     store_info = collection.find_one({"name": result_store[i]})
#     print(store_info)    


# 연결 닫기
mongo_client.close()