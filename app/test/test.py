import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.recommend_location import recommend_by_location
from tools.recommend_menu import recommend_by_menu 
from service.saveRestaurant_pipeline import get_location_and_menu

async def main():
    results = await recommend_by_menu.ainvoke("강남역 근처에 매운 닭발이나 맵찔이도 먹을 수 있는 쭈꾸미집 추천해줘")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())