from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

START_URL = "https://www.exteriores.gob.es/Consulados/lahabana/es/ServiciosConsulares/Paginas/index.aspx?scco=Cuba&scd=166&scca=Pasaportes+y+otros+documentos&scs=Pasaportes+-+Requisitos+y+procedimiento+para+obtenerlo"
WIDGET_URL = "https://www.citaconsular.es/es/hosteds/widgetdefault/22091b5b8d43b89fb226cabb272a844f9"

def fetch_estado() -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Acepta automáticamente alert('Welcome / Bienvenido')
        page.on("dialog", lambda d: d.accept())

        # 1) Abrir página madre
        page.goto(START_URL, wait_until="domcontentloaded")

        # 2) Click link del widget (abre popup)
        link = page.locator(f"a.btn.natural[href='{WIDGET_URL}']").first
        with page.expect_popup() as pop:
            link.click()

        widget_page = pop.value
        widget_page.wait_for_load_state("domcontentloaded")

        # 3) Click en Continue / Continuar
        widget_page.locator("#idCaptchaButton").wait_for(state="visible", timeout=20000)
        widget_page.locator("#idCaptchaButton").click()

        # 4) Esperar el contenedor donde aparece el estado (tarda 15-20s)
        container = widget_page.locator("#idDivBktServicesContainer")
        container.wait_for(state="visible", timeout=45000)

        # 5) Leer el div visible (hay uno display:none y otro visible)
        status_div = container.locator("div").filter(has_not=container.locator("[style*='display: none']")).first

        # Alternativa aún más directa: localizar por texto
        # status_div = container.locator("div", has_text="No hay horas disponibles").first

        status_div.wait_for(state="visible", timeout=45000)

        estado = status_div.inner_text().strip()

        browser.close()
        return estado

if __name__ == "__main__":
    try:
        estado = fetch_estado()
        print("ESTADO:", estado)
    except PWTimeout:
        print("ERROR: Timeout esperando el estado (posible cambio en la página o bloqueo).")
