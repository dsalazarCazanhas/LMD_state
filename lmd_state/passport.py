from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import sys

START_URL = "https://www.exteriores.gob.es/Consulados/lahabana/es/ServiciosConsulares/Paginas/index.aspx?scco=Cuba&scd=166&scca=Pasaportes+y+otros+documentos&scs=Pasaportes+-+Requisitos+y+procedimiento+para+obtenerlo"
WIDGET_URL = "https://www.citaconsular.es/es/hosteds/widgetdefault/22091b5b8d43b89fb226cabb272a844f9"

NO_HAY_HORAS_TEXT = "No hay horas disponibles"

ART_DIR = Path("artifacts")
ART_DIR.mkdir(exist_ok=True)

@dataclass
class Result:
    status: str          # NO_HAY_HORAS | POSIBLE_DISPONIBILIDAD
    message: str         # texto visible para mostrar / enviar
    url: str             # url donde se obtuvo el resultado

def save_result_to_desktop(text: str):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    output_dir = Path.cwd() / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"passport_status_{timestamp}.txt"

    file_path.write_text(text, encoding="utf-8")

    print(f"\nResultado guardado en: {file_path}")


def dump_artifacts(page, tag: str):
    """Artefactos sólo para errores técnicos (diagnóstico)."""
    try:
        (ART_DIR / f"{tag}.url.txt").write_text(page.url or "", encoding="utf-8")
        (ART_DIR / f"{tag}.html").write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(ART_DIR / f"{tag}.png"), full_page=True)
    except Exception:
        # No dejamos que el diagnóstico rompa el flujo de error.
        pass

def fetch_estado() -> Result:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context()
        page = context.new_page()

        # Manejo del alert('Welcome / Bienvenido')
        page.on("dialog", lambda d: d.accept())

        try:
            # 1) Página madre
            page.goto(START_URL, wait_until="domcontentloaded", timeout=30000)

            # 2) Click link widget (abre popup)
            link = page.locator(f"a.btn.natural[href='{WIDGET_URL}']").first

            try:
                with page.expect_popup(timeout=15000) as pop:
                    link.click()
                widget = pop.value
            except PWTimeout:
                # Fallback: si no abre popup, seguimos en la misma pestaña
                widget = page

            widget.wait_for_load_state("domcontentloaded", timeout=30000)

            # 3) Botón Continue / Continuar
            widget.locator("#idCaptchaButton").wait_for(state="visible", timeout=20000)
            widget.locator("#idCaptchaButton").click()

            # 4) Contenedor final
            container = widget.locator("#idDivBktServicesContainer")
            container.wait_for(state="visible", timeout=60000)

            # 5) Texto del contenedor (estado visible)
            estado_texto = container.inner_text().strip()
            current_url = widget.url

            browser.close()

            if NO_HAY_HORAS_TEXT in estado_texto:
                return Result(status="NO_HAY_HORAS", message=estado_texto, url=current_url)

            return Result(status="POSIBLE_DISPONIBILIDAD", message=estado_texto, url=current_url)

        except PWTimeout as e:
            # Error técnico: timeouts de Playwright (navegación/selector/carga)
            dump_artifacts(page, "playwright_timeout")
            browser.close()
            raise RuntimeError(f"Playwright timeout: {e}") from e

        except Exception as e:
            # Error técnico general: Python/Playwright inesperado
            dump_artifacts(page, "unexpected_error", e)
            browser.close()
            raise

def main() -> int:
    try:
        result = fetch_estado()
        print("ESTADO:")
        print(result.message)
        print("\nCLASIFICACIÓN:", result.status)
        print("URL:", result.url)

        save_result_to_desktop(result.message)

        # Exit codes opcionales (útil para n8n / CI)
        # 0 = ejecución OK sin disponibilidad
        # 2 = posible disponibilidad (para alertar)
        return 0 if result.status == "NO_HAY_HORAS" else 2

    except Exception as e:
        # Error técnico real (no relacionado a "no hay horas")
        print(f"ERROR TÉCNICO: {e}", file=sys.stderr)
        print("Revisa ./artifacts (html/png/url) para diagnóstico.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
