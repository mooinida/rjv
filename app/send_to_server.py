import requests
import os
from dotenv import load_dotenv

load_dotenv()

SPRING_SERVER = "http://localhost:8080"
JWT_TOKEN = os.getenv("JWT_TOKEN")

def send_restaurant_rating(place_id: int, rating: float, count: int):
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/rating"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    payload = {
        "rating": rating,
        "reviewCount": count
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

def send_restaurant(restaurant: dict):
    url = f"{SPRING_SERVER}/api/restaurants"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    response = requests.post(url, json=restaurant, headers=headers)
    return response.status_code, response.text

def restaurant_is_exist(place_id: int) -> bool:
    try:
        url = f"{SPRING_SERVER}/api/restaurants/{place_id}"
        headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
        response = requests.get(url, headers=headers)
        return response.ok and response.json()
    except Exception as e:
        return False

def send_reviews(place_id: int, reviews: list):
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/reviews"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    response = requests.post(url, json=reviews, headers=headers)
    return response.status_code, response.text

def send_menus(place_id: int, items: list):
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/menus"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            url,
            json=items,
            headers=headers
        )
        return response.status_code, response.text
    except requests.RequestException as e:
        return 500