from fpdf import FPDF
import datetime

def generate_ebdn_receipt(record):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "ELECTRONIC BUNKER DELIVERY NOTE (eBDN)", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Delivery ID: {record.delivery_id}", ln=True)
    pdf.cell(0, 10, f"IMO Number: {record.imo_number}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Bunker Specifications:", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f" - Actual Quantity: {record.actual_qty} MT", ln=True)
    pdf.cell(0, 10, f" - Density @ 15C: {record.density} kg/m3", ln=True)
    pdf.cell(0, 10, f" - Sulphur Content: {record.sulphur_content}%", ln=True)
    pdf.cell(0, 10, f" - Sample Seal ID: {record.sample_id}", ln=True)
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 10, "Blockchain Proofs (ECDSA):", ln=True)
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(0, 5, f"Supplier Signature: {record.sig_supplier.hex() if record.sig_supplier else 'N/A'}")
    pdf.ln(2)
    pdf.multi_cell(0, 5, f"Chief Eng Signature: {record.sig_chief.hex() if record.sig_chief else 'N/A'}")
    
    return pdf.output(dest='S')