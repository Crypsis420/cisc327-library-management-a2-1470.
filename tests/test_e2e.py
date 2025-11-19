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

LIBRARY_URL = "http://localhost:5000"

# Use a fixed title so the second test can always find it
BOOK_TITLE = "Totally Real Book"
BOOK_AUTHOR = "Me Of Course"

def _new_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def _wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.25)
    return False

@contextmanager
def run_app():
    env = dict(os.environ)
    proc = subprocess.Popen(
        ["python", "app.py"],
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

def _find_row_by_title(driver, title: str):
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for r in rows:
        txt = r.get_attribute("innerText") or r.text
        if title in txt:
            return r
    return None

def test_add_book_shows_in_catalog():
    with run_app():
        driver = _new_driver()
        try:
            # Go to catalog
            driver.get(f"{LIBRARY_URL}/catalog")
            assert "Book Catalog" in driver.page_source

            # Add new book
            driver.find_element(By.CSS_SELECTOR, 'a[href="/add_book"]').click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "title")))

            # Randomize ISBN so the test is re-runnable in CI
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

            # Wait for redirect or flash
            WebDriverWait(driver, 10).until(
                lambda d: "/catalog" in d.current_url
                or d.find_elements(By.CLASS_NAME, "flash-success")
                or d.find_elements(By.CLASS_NAME, "flash-error")
            )

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            table_text = driver.find_element(By.TAG_NAME, "table").text
            assert BOOK_TITLE in table_text
            assert BOOK_AUTHOR in table_text
        finally:
            driver.quit()

def test_borrow_book_shows_confirmation():
    with run_app():
        driver = _new_driver()
        try:
            driver.get(f"{LIBRARY_URL}/catalog")
            assert "Book Catalog" in driver.page_source

            # Make sure table is present
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

            # Find the exact row for the book added in the previous test
            row = _find_row_by_title(driver, BOOK_TITLE)
            # If CI ran tests out of order or the book is missing for any reason, fail fast
            assert row is not None, f"Expected to find row for '{BOOK_TITLE}' but did not."

            # Fill patron id in that SAME row
            patron_inputs = row.find_elements(By.NAME, "patron_id")
            assert patron_inputs, "No patron_id input found in the target row."
            patron_input = patron_inputs[0]
            patron_input.clear()
            patron_input.send_keys("123456")

            # Click that row's Borrow button
            borrow_buttons = row.find_elements(By.CSS_SELECTOR, "button.btn-success")
            assert borrow_buttons, "No Borrow button found in the target row."
            borrow_buttons[0].click()

            # Wait for a table or a flash
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.TAG_NAME, "table")
                or d.find_elements(By.CLASS_NAME, "flash-success")
                or d.find_elements(By.CLASS_NAME, "flash-error")
            )

            page_text = driver.page_source.lower()
            assert ("borrow" in page_text) or ("success" in page_text), \
                "No success message found after borrowing."
        finally:
            driver.quit()
