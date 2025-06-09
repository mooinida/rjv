import requests
import os
from dotenv import load_dotenv

load_dotenv()

SPRING_SERVER = "http://mooin.shop:8080"
JWT_TOKEN = os.getenv("JWT_TOKEN")

def bring_menu_filter_restaurants(keywords:list):
    url = f"{SPRING_SERVER}/api/restaurants/filter/menu"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    payload = {"keywords": keywords}
    response = requests.post(url, json = payload, headers = headers)
    response.raise_for_status()
    data = response.json()
    return {"restaurants": data} 
    


def bring_context_filter_restaurants(contexts:list):
    url = f"{SPRING_SERVER}/api/restaurants/filter/context"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    payload = {"keywords": contexts}
    response = requests.post(url, json = payload, headers = headers)
    response.raise_for_status()
    data = response.json()
    return {"restaurants": data} 

def bring_restaurants_list(placeIds:list):
    url = f"{SPRING_SERVER}/api/restaurants/restaurants"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    response = requests.post(url, json = placeIds, headers = headers)
    response.raise_for_status()
    data = response.json()
    return {"restaurants": data} 


