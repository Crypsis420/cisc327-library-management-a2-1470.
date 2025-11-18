"""
NOTE: Before running these tests, start the Flask app in a separate terminal as this is not headless: python app.py
"""

from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


import os, socket, time, subprocess
from contextlib import contextmanager

LIBRARY_URL = "http://localhost:5000"

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
    # If you ever switch ports, set PORT env and update LIBRARY_URL to match
    env = dict(os.environ)
    proc = subprocess.Popen(
        ["python", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    try:
        ok = _wait_for_port("127.0.0.1", 5000, timeout=15)
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


def test_add_book_shows_in_catalog():
    # Run the app for this test
    with run_app():
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Launch browser INSIDE the run_app context
        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Navigate to catalog
            driver.get(f"{LIBRARY_URL}/catalog")
            assert "Book Catalog" in driver.page_source

            # Click Add New Book link
            add_book_link = driver.find_element(By.CSS_SELECTOR, 'a[href="/add_book"]')
            add_book_link.click()

            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "title"))
            )

            # Randomize ISBN so the test is re-runnable
            isbn = f"{randint(10**12, 10**13 - 1)}"

            # Fill in the form
            driver.find_element(By.NAME, "title").send_keys("Totally Fake Book")
            driver.find_element(By.NAME, "author").send_keys("Some guy")
            driver.find_element(By.NAME, "isbn").send_keys(isbn)
            driver.find_element(By.NAME, "total_copies").send_keys("2")

            # Submit the form
            driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

            # Wait a bit for submission
            time.sleep(2)

            # Check current URL and page
            if "/add_book" in driver.current_url:
                page_source = driver.page_source
                if "flash-error" in page_source:
                    error_elem = driver.find_element(By.CLASS_NAME, "flash-error")
                    print(f"Error message: {error_elem.text}")
                assert False, f"Form did not submit. Still on: {driver.current_url}"

            # Verify book appears in catalog
            table_text = driver.find_element(By.TAG_NAME, "table").text
            assert "Totally Fake Book" in table_text
            assert "Some guy" in table_text

            # Optional success flash
            try:
                flash_message = driver.find_element(By.CLASS_NAME, "flash-success").text
                assert "successfully" in flash_message.lower()
            except Exception:
                pass
        finally:
            driver.quit()


def test_borrow_book_shows_confirmation():
    # Run the app for this test
    with run_app():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get(f"{LIBRARY_URL}/catalog")
            assert "Book Catalog" in driver.page_source

            # Fill in patron ID for first available book
            patron_input = driver.find_element(By.NAME, "patron_id")
            patron_input.send_keys("123456")

            # Click first Borrow button
            borrow_button = driver.find_element(By.CSS_SELECTOR, "button.btn-success")
            borrow_button.click()

            # Wait for table to appear (means page reloaded)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            # Check for success message in page
            page_text = driver.page_source.lower()
            assert "borrowed" in page_text or "success" in page_text, "No success message found after borrowing"
        finally:
            driver.quit()