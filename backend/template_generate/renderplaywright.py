from playwright.sync_api import sync_playwright

def generate_pdf(html_path, output_pdf):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Load local HTML file
        page.goto(f"file://{html_path}")

        # Generate PDF
        page.pdf(path=output_pdf, width="2000px", height="1414px", print_background=True)

        browser.close()

# Example usage
generate_pdf("/Users/ankushagarwal/Documents/dearDonor/DearDonorFrontendRevamp/DearDonor/backend/template_generate/receipt.html", "receipt_output_playwright.pdf")