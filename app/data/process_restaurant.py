from get_review_by_selenium import crawl_review, init_driver
from send_to_server import send_restaurant, restaurant_is_exist

def process_restaurant(r):
    try:
        place_id = int(r["id"])
        if restaurant_is_exist(place_id):
            return

        restaurant = {
            "place_id": place_id,
            "name": r.get("place_name", ""),
            "address": r.get("road_address_name"),
            "url": r.get("place_url", ""),
            "category": r.get("category_name", ""),
            "latitude": r.get("y"),
            "longitude": r.get("x")
        }

        send_restaurant(restaurant)

        driver = init_driver()
        crawl_review(driver, restaurant["url"], place_id)
        driver.quit()

    except Exception as e:
        print(f"[{place_id}] ❌ 오류 발생: {e}")
