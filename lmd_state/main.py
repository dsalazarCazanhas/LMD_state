import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

app = FastAPI()

class ExpedienteRequest(BaseModel):
    no_expediente: str
    apellidos_titular: str

def consultar_expediente(no_expediente, apellidos_titular):
    """Automates the process of checking expediente status and returns the result."""
    
    # Setup headless Chrome
    options = Options()
    options.add_argument("--headless")  # Run without GUI
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None  # Initialize outside try block
    
    try:
        # Initialize WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        page = "https://www.exteriores.gob.es/Consulados/lahabana/es/Consulado/Paginas/Tramites.aspx"
        driver.get(page)

        # Wait for iframe and switch to it
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "MSOPageViewerWebPart_WebPartWPQ1"))
        )
        driver.switch_to.frame(iframe)

        # Find the container with the form
        global_selector = driver.find_element(By.CSS_SELECTOR, "app-login")

        # Select the radio button
        radio_btn = global_selector.find_element(By.ID, "exampleRadios4")
        radio_btn.click()

        # Fill input fields
        global_selector.find_element(By.ID, "no-expediente").send_keys(no_expediente)
        global_selector.find_element(By.ID, "apellidos-titular").send_keys(apellidos_titular)

        # Click the submit button
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
        )
        submit_button.click()

        # Wait for the result and extract text
        estado_expediente = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Estado del expediente')]/following-sibling::p/strong"))
        )
        
        print(f"✅ Estado del expediente: {estado_expediente.text}")

        # Return the extracted information
        return {
            "no_expediente": no_expediente,
            "apellidos_titular": apellidos_titular,
            "estado": estado_expediente.text
        }

    except TimeoutException:
        raise HTTPException(status_code=408, detail="⚠ Timeout: The page took too long to load.")
    except NoSuchElementException:
        raise HTTPException(status_code=404, detail="❌ Error: Unable to locate an element on the page.")
    except WebDriverException as e:
        raise HTTPException(status_code=500, detail=f"🚨 WebDriver Error: {e}")
    finally:
        if driver:
            driver.quit()  # Ensure the driver is closed properly

def send_data_to_api(data, api_url):
    """Sends expediente status data via an HTTP request."""
    try:
        response = httpx.post(api_url, json=data, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        print(f"📨 Data sent successfully! Response: {response.json()}")
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"API Error: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"🚨 Request Error: {e}")

@app.post("/expediente")
def get_expediente_status(request: ExpedienteRequest):
    """Receives expediente details via POST, fetches status, and sends it to another API."""
    expediente_data = consultar_expediente(request.no_expediente, request.apellidos_titular)
    
    if expediente_data:
        API_ENDPOINT = "http://192.168.1.90:5678/webhook-test/39898e23-90cf-43d4-9cc3-2e06a4fe924c"
        api_response = send_data_to_api(expediente_data, API_ENDPOINT)
        return {"expediente_data": expediente_data, "api_response": api_response}
    
    return {"error": "Failed to fetch expediente status"}