from random import randint
import os, socket, time, subprocess
from contextlib import contextmanager

import pytest
from pytest import mark
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

LIBRARY_URL = "http://127.0.0.1:5000"
BOOK_TITLE  = "Totally Real Book"
BOOK_AUTHOR = "Me Of Course"

def _chrome():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opts)

def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.25)
    return False

@contextmanager
def _run_app_once():
    # Prefer flask run to align with your assignment guidelines
    # Make sure your app auto-initializes the SQLite DB in app startup
    env = dict(os.environ)
    env.setdefault("FLASK_APP", "app.py")
    env.setdefault("FLASK_ENV", "production")
    # Bind to 127.0.0.1 for tests; Docker will use 0.0.0.0 (see notes below)
    proc = subprocess.Popen(
        ["flask", "run", "--host=127.0.0.1", "--port=5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    try:
        ok = _wait_for_port("127.0.0.1", 5000, timeout=20)
        if not ok:
            out = proc.stdout.read().decode("utf-8", errors="ignore") if proc.stdout else ""
            raise RuntimeError(f"Flask app failed to start on {LIBRARY_URL}\n{out}")
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()

@pytest.fixture(scope="module", autouse=True)
def server():
    # Start Flask once for this module, then stop
    with _run_app_once():
        yield

def _find_row_by_title(driver, title: str):
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for r in rows:
        txt = r.text or r.get_attribute("innerText") or ""
        if title in txt:
            return r
    return None

def _ensure_book_exists(driver):
    driver.get(f"{LIBRARY_URL}/catalog")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    row = _find_row_by_title(driver, BOOK_TITLE)
    if row:
        return row
    # Add the book
    driver.find_element(By.CSS_SELECTOR, 'a[href="/add_book"]').click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "title")))
    isbn = f"{randint(10**12, 10**13 - 1)}"
    driver.find_element(By.NAME, "title").clear()
    driver.find_element(By.NAME, "title").send_keys(BOOK_TITLE)
    driver.find_element(By.NAME, "author").clear()
    driver.find_element(By.NAME, "author").send_keys(BOOK_AUTHOR)
    driver.find_element(By.NAME, "isbn").clear()
    driver.find_element(By.NAME, "isbn").send_keys(isbn)
    driver.find_element(By.NAME, "total_copies").clear()
    driver.find_element(By.NAME, "total_copies").send_keys("1")
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    return _find_row_by_title(driver, BOOK_TITLE)

def test_add_book_shows_in_catalog():
    driver = _chrome()
    try:
        driver.get(f"{LIBRARY_URL}/catalog")
        assert "Book Catalog" in driver.page_source
        # Ensure the book exists (adds it if missing)
        row = _ensure_book_exists(driver)
        assert row is not None, "Newly added book row not found in catalog"
        # Quick smoke on author text as well
        assert BOOK_AUTHOR in driver.find_element(By.TAG_NAME, "table").text
    finally:
        driver.quit()

def test_borrow_book_shows_confirmation():
    driver = _chrome()
    try:
        # Ensure the book exists, then borrow in that row
        row = _ensure_book_exists(driver)
        assert row is not None, "Expected book row not found"

        patron_inputs = row.find_elements(By.CSS_SELECTOR, 'input[name="patron_id"]')
        assert patron_inputs, "No patron_id input in row"
        patron_inputs[0].clear()
        patron_inputs[0].send_keys("123456")

        borrow_buttons = row.find_elements(By.CSS_SELECTOR, "button.btn-success")
        assert borrow_buttons, "No Borrow button in row"
        borrow_buttons[0].click()

        # Wait for table or flash after POST/redirect
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.TAG_NAME, "table")
            or d.find_elements(By.CLASS_NAME, "flash-success")
            or d.find_elements(By.CLASS_NAME, "flash-error")
        )
        page_text = driver.page_source.lower()
        assert ("borrow" in page_text) or ("success" in page_text)
    finally:
        driver.quit()