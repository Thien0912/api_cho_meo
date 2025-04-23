import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys

# Hàm tìm kiếm giống chó/mèo từ hình ảnh
def search_breed(image_path: str):
    # Tạo đối tượng ChromeOptions mới mỗi lần khởi tạo
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")

    # Khởi tạo undetected-chromedriver
    driver = uc.Chrome(options=options)
    try:
        # Truy cập Google
        driver.get("https://www.google.com/imghp")
        
        # Tối đa hóa cửa sổ trình duyệt
        driver.maximize_window()

        # Nhấn vào nút tìm kiếm bằng hình ảnh
        try:
            time.sleep(2)
            image_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Tìm kiếm bằng hình ảnh"]'))
            )
            image_button.click()
        except Exception as e:
            print(f"❌ Lỗi khi nhấn nút tìm kiếm bằng hình ảnh: {e}")

        # Tải ảnh lên
        try:
            time.sleep(2)
            upload_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
            )
            upload_button.send_keys(image_path)
        except Exception as e:
            print(f"❌ Lỗi khi tải ảnh lên: {e}")

        # Chờ kết quả và cuộn trang nhẹ
        time.sleep(5)
        driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(2)

        # Lấy tên giống từ XPath
        try:
            breed_name_element = driver.find_element(By.XPATH, "/html/body/div[3]/div/div[9]/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[1]/div/div[1]/div/a[1]/div/div/div/div[2]/div/div/div")
            breed_name = breed_name_element.text
            return breed_name
        except Exception as e:
            print(f"❌ Lỗi khi lấy tên giống từ XPath: {e}")
            return None
    except Exception as e:
        print(f"🚨 Lỗi chung: {e}")
        return None
    finally:
        driver.quit()

# Nếu script được gọi từ dòng lệnh, chạy hàm search_breed
if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        breed = search_breed(image_path)
        if breed:
            print(f"Tên giống chó/mèo là: {breed}")
        else:
            print("Không thể nhận diện giống chó/mèo.")
