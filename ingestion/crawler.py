import os
import time
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from ingestion.image_search import search_breed  # Import Selenium script

# Đường dẫn đến thư mục lưu trữ dữ liệu
DATA_IN_DIR = 'app/utils/data/data_in/'  # Đường dẫn đến thư mục lưu bài viết
MAX_ARTICLES = 5  # Giới hạn số bài viết cho mỗi giống

# Tạo thư mục lưu trữ nếu chưa có
os.makedirs(DATA_IN_DIR, exist_ok=True)

# Danh sách các từ khóa và thẻ cần loại bỏ
EXCLUDE_KEYWORDS = ['advertisement', 'ads', 'sponsored', 'related content']
EXCLUDE_TAGS = ['aside', 'footer', 'nav', 'form']

def format_breed_name(breed):
    return breed.replace(' ', '_')

def clean_content(content):
    soup = BeautifulSoup(content, 'html.parser')

    # Loại bỏ các thẻ không cần thiết
    for tag in EXCLUDE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    paragraphs = soup.find_all('p')
    clean_text = []
    for p in paragraphs:
        text = p.get_text().strip()

        # Loại bỏ các đoạn chứa từ khóa quảng cáo
        if any(keyword in text.lower() for keyword in EXCLUDE_KEYWORDS):
            continue

        clean_text.append(text)

    return '\n'.join(clean_text).strip()

# Kiểm tra số lượng bài viết đã lưu trong file
def count_existing_articles(breed):
    filepath = os.path.join(DATA_IN_DIR, f"{format_breed_name(breed)}.txt")
    if not os.path.exists(filepath):
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
        return content.count('📌 Nguồn:')

# Lưu bài viết vào file duy nhất
def save_article(breed, url):
    existing_articles = count_existing_articles(breed)
    if existing_articles >= MAX_ARTICLES:
        return False
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = clean_content(response.text)

        if content:
            filepath = os.path.join(DATA_IN_DIR, f"{format_breed_name(breed)}.txt")
            article_number = existing_articles + 1
            with open(filepath, 'a', encoding='utf-8') as file:
                file.write(f"\n=== [Bài viết {article_number}] ===\n")
                file.write(f"📌 Nguồn: {url}\n\n")
                file.write(content + "\n" + "-" * 50 + "\n")
            print(f"📥 Đã lưu bài viết cho giống '{breed}' từ: {url}")
            return True
        else:
            print(f"⚠️ Nội dung từ {url} không hợp lệ hoặc bị loại bỏ.")
            return False

    except Exception as e:
        print(f"⚠️ Lỗi khi tải bài viết từ {url}: {e}")
        return False

# Lấy các kết quả tìm kiếm từ DuckDuckGo
def get_search_results(query, num_results=20):
    links = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=num_results)
            links = [result['href'] for result in results]
        time.sleep(1)  # Giảm tần suất để tránh bị chặn
    except Exception as e:
        print(f"⚠️ Lỗi khi tìm kiếm '{query}': {e}")
    return links

# Crawl bài viết cho giống
def crawl_breed(breed):
    existing_articles = count_existing_articles(breed)
    if existing_articles >= MAX_ARTICLES:
        print(f"✅ Đã có đủ {MAX_ARTICLES} bài viết cho giống '{breed}', bỏ qua...")
        return
    
    print(f"🔎 Đang tìm kiếm bài viết cho giống '{breed}'...")

    search_query = f"{breed} cat breed information"
    links = get_search_results(search_query)

    count = existing_articles
    for link in links:
        if save_article(breed, link):
            count += 1
            if count >= MAX_ARTICLES:
                break

# Lấy tên giống từ Selenium và cào bài viết
def crawl_breed_from_image(image_path):
    breed = search_breed(image_path)
    if breed:
        print(f"🔍 Tên giống tìm thấy: {breed}")
        crawl_breed(breed)
    else:
        print("❌ Không thể tìm thấy giống từ hình ảnh.")

# Chạy crawler cho tất cả giống từ ảnh
if __name__ == "__main__":
    # Giả sử bạn có đường dẫn đến các ảnh
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]  # Đổi thành đường dẫn ảnh thực tế

    for image_path in image_paths:
        crawl_breed_from_image(image_path)
        time.sleep(2)  # Nghỉ 2 giây giữa các lần tìm kiếm để tránh bị chặn

    print("\n🎉 Hoàn tất lấy dữ liệu!")
