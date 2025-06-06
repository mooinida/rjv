import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SPRING_SERVER = "http://localhost:8080"
JWT_TOKEN = os.getenv("JWT_TOKEN")

async def get_menu_texts(place_id: str) -> list:
    url = f"{SPRING_SERVER}/api/restaurants/{place_id}/menus"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            raw_texts = response.json()
            return [{"text": t} for t in raw_texts]
    except httpx.RequestError as e:
        return [{"text": f"메뉴 텍스트 요청 실패: {e}"}]