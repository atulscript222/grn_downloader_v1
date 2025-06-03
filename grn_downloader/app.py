from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from pyngrok import ngrok

app = Flask(__name__)
DEFAULT_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DEFAULT_DIR, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    logs = []
    if request.method == 'POST':
        grns = request.form['grns'].split(',')
        grns = [g.strip() for g in grns if g.strip().isdigit()]
        download_dir = request.form.get('path') or DEFAULT_DIR
        os.makedirs(download_dir, exist_ok=True)

        logs.append(f"📁 Download path: {download_dir}")

        options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": download_dir,
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False,
        }
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)

        for challan in grns:
            try:
                logs.append(f"\n📄 Processing GRN: {challan}")
                driver.get("https://egrashry.nic.in/VerifyChallan?verification-type=by-challan&challan-num=")

                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#RadioButton1"))).click()
                input_box = wait.until(EC.presence_of_element_located((By.ID, "txt_stmp")))
                input_box.clear()
                input_box.send_keys(str(challan))

                wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='View Stamp Paper/Challan']"))).click()
                print_buttons = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@id='btnprint']")))
                logs.append(f"🔢 Found {len(print_buttons)} print button(s)")

                before = set(os.listdir(download_dir))
                downloaded = []

                for i, btn in enumerate(print_buttons, 1):
                    start = time.time()
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(6)
                    after = set(os.listdir(download_dir))
                    diff = list(after - before)
                    duration = round(time.time() - start, 2)

                    if diff:
                        logs.append(f"  ✅ Print {i} downloaded in {duration}s: {diff[0]}")
                        downloaded.append(diff[0])
                        before = after
                    else:
                        logs.append(f"  ❌ Print {i} failed (after {duration}s)")

                for i, f in enumerate(downloaded, 1):
                    new_name = f"{challan}_{i}.pdf"
                    os.rename(os.path.join(download_dir, f), os.path.join(download_dir, new_name))
                    logs.append(f"  🗂️  Renamed: {f} ➝ {new_name}")

            except Exception as e:
                logs.append(f"❌ Error with GRN {challan}: {e}")

        driver.quit()
        logs.append(f"\n✅ All done. Files saved at: {download_dir}")
    return render_template("index.html", logs=logs)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
