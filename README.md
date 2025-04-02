# Expediente Status Checker API

## 📌 Overview
This project provides a **FastAPI webhook** that automates the process of checking the status of an **expediente (case file)** from the Spanish consulate website. It uses **Selenium** to extract information and sends the result to an external API using `httpx`. Additionally, the webhook can be integrated with **n8n** to automate notifications (e.g., sending results to a Telegram chat).

---

## 🚀 Features
- **Webhook to receive expediente details dynamically**
- **Selenium automation** for fetching case status
- **Runs headless** for efficient execution
- **Sends results via HTTP POST (`httpx`)** to an external API
- **Error handling** for timeouts, missing elements, and failed API requests
- **Can be integrated with n8n** for workflow automation

---

## 🔧 Installation & Setup

### 1️⃣ Install Dependencies
Make sure you have **Python 3.8+** installed. Then, install the required packages:
```sh
poetry install --no-root
```

The webhook will be available at:
```
http://127.0.0.1:8000/expediente
```

---

#### ✅ Example n8n Workflow
- Webhook → Python Function → Telegram Bot → Notification to User

---

## ⚠️ Error Handling
| Error Type             | HTTP Status | Description                   |
| ---------------------- | ----------- | ----------------------------- |
| TimeoutException       | 408         | Page took too long to load    |
| NoSuchElementException | 404         | Element not found on the page |
| WebDriverException     | 500         | Selenium driver error         |
| httpx.HTTPStatusError  | 400/500     | API request failed            |

---

## 📜 License
This project is licensed under the **MIT License**.

---

## 👨‍💻 Author
Developed by [Dayron Salazar]. Feel free to contribute or report issues!

