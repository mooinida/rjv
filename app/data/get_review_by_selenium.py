from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from send_to_server import send_restaurant_rating, send_reviews, send_menus

import time

def init_driver():
    options = Options()
    options.add_argument("--headless=new")  # Headless 모드
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def crawl_review(driver ,url: str, place_id: int):
    try:
        # 새 탭 열기
        driver.execute_script("window.open(arguments[0]);", url)
        driver.switch_to.window(driver.window_handles[-1])

        wait = WebDriverWait(driver, 10)

        # 탭 목록 찾기
        tab_list = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#mainContent > div.main_detail.home > div.wrap_tab.tab_primary > div > ul > li"))
        )

        review_button = None
        menu_button = None
        for tab in tab_list:
            try:
                a_tag = tab.find_element(By.TAG_NAME, "a")
                if "후기" in a_tag.text:
                    review_button = a_tag
                if "메뉴" in a_tag.text:
                    menu_button = a_tag
            except:
                continue

        # 메뉴 수집
        menus = []
        if menu_button:
            menu_button.click()
            menu_items = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#mainContent > div.main_detail > div.detail_cont > div > div.wrap_goods > ul > li"))
            )
            for item in menu_items:
                try:
                    name = item.find_element(By.CSS_SELECTOR, "div > div:nth-child(1) > strong").text.strip()
                    price = item.find_element(By.CSS_SELECTOR, "div > div:nth-child(2) > p").text.strip()
                    menus.append({"name": name, "price": price})
                except:
                    continue

        # 리뷰 수집
        reviews = []
        rating = 0.0
        review_count = 0
        if review_button:
            review_button.click()

            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            try:
                rating = float(driver.find_element(By.CSS_SELECTOR, "#mainContent span.num_star").text)
                review_count = int(driver.find_element(By.CSS_SELECTOR, "#mainContent a > strong").text.replace("후기", "").strip())
            except:
                pass

            review_items = driver.find_elements(By.CSS_SELECTOR, "#mainContent div.group_review > ul > li")
            for item in review_items:
                try:
                    p_tags = item.find_elements(By.CSS_SELECTOR,
                        "div > div.area_review > div > div.review_detail > div.wrap_review > a > p"
                    )
                    if not p_tags:
                        continue
                    review_text = p_tags[0].text.strip()
                    if review_text and len(review_text) >= 5:
                        reviews.append({"text": review_text})
                except:
                    continue

        # 서버 전송
        send_restaurant_rating(place_id, rating, review_count)
        send_reviews(place_id, reviews)
        send_menus(place_id, menus)

    except Exception as e:
        print(f"[{place_id}] 오류 발생:", e)

    finally:
        driver.close()  # 현재 탭 닫기
        driver.switch_to.window(driver.window_handles[0])  # 원래 탭으로 전환
