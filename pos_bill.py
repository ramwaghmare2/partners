import os
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from escpos.printer import Usb
from config import Config  

# Printer Configuration
VENDOR_ID = Config.VENDOR_ID
PRODUCT_ID = Config.PRODUCT_ID

# Directory for Saving Bills
BILL_SAVE_PATH = r"C:\Users\tiwar\Desktop\Restaurant_Bills"
os.makedirs(BILL_SAVE_PATH, exist_ok=True)

# Initialize Printer
try:
    printer = Usb(VENDOR_ID, PRODUCT_ID, timeout=0)
except Exception as e:
    printer = None
    print(f"Printer connection error: {e}")

def generate_bill_pdf(order_details):
    """ Generates a small-sized receipt (80mm x 150mm) with the given order details. """

    # Set custom page size for 80mm x 150mm thermal receipt
    width, height = 80 * mm, 150 * mm  
    order_id = order_details.get("order_id", "N/A")
    filename = f"bill_{order_id}.pdf"
    file_path = os.path.join(BILL_SAVE_PATH, filename)

    c = canvas.Canvas(file_path, pagesize=(width, height))
    c.setFont("Helvetica-Bold", 10)

    # Header
    y = height - 20  # Start from top
    kitchen_name = order_details.get("kitchen_name", "Unknown Kitchen")
    c.drawCentredString(width / 2, y, kitchen_name)

    c.setFont("Helvetica", 8)
    y -= 12
    c.drawCentredString(width / 2, y, f"Invoice: {order_id}")
    
    y -= 12
    created_at = order_details.get("created_at", "Unknown Date")
    c.drawCentredString(width / 2, y, f"Date: {created_at}")

    y -= 12
    customer_name = order_details.get("customer_name", "Guest")
    c.drawCentredString(width / 2, y, f"Customer: {customer_name}")

    y -= 12
    # Handle Long Address Wrapping (Max 32 characters per line)
    address = order_details.get("address", "")
    address_lines = textwrap.wrap(f"Address: {address}", width=40)
    for line in address_lines:
        c.drawCentredString(width / 2, y, line)
        y -= 10

    y -= 5
    c.setDash(3, 1)
    c.line(5, y - 3, 215, y - 3)  # Line above total
    c.setDash()
    
    # Table Headers
    y -= 20
    c.setFont("Helvetica-Bold", 8)
    c.drawString(10, y, "Item")
    c.drawString(120, y, "Qty")
    c.drawString(150, y, "Price")
    c.drawString(180, y, "Total")
    y -= 12
    c.setDash(3, 1)
    c.line(5, y - 3, 215, y - 3)  # Line above total
    c.setDash()

    # Table Data
    y -= 12
    c.setFont("Helvetica", 8)
    total_amount = 0

    items = order_details.get("items", [])  # Default to empty list if no items
    for item in items:
        name = item.get("name", "Unknown Item")[:30]  # Limit item name length
        quantity = item.get("quantity", 0)
        price = item.get("price", 0.0)
        total_price = quantity * price
        total_amount += total_price

        c.drawString(10, y, name)
        c.drawString(122, y, str(quantity))
        c.drawString(150, y, f"{price:.2f}")
        c.drawString(180, y, f"{total_price:.2f}")
        y -= 12

    # Summary
    discount_percentage = 5
    discount_amount = (total_amount * discount_percentage) / 100
    payable_amount = total_amount - discount_amount

    c.setDash(3, 1)
    c.line(5, y - 3, 215, y - 3)  # Line above total
    c.setDash()
    
    y -= 12
    c.drawString(10, y, "Total:")
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(200, y, f"{total_amount:.2f}")

    y -= 12
    c.setFont("Helvetica-Bold", 8)
    c.drawString(10, y, f"Discount ({discount_percentage}%):")
    c.drawRightString(200, y, f"- {discount_amount:.2f}")

    y -= 12
    c.setFont("Helvetica-Bold", 8)
    c.drawString(10, y, "Payable:")
    c.drawRightString(200, y, f"{payable_amount:.2f}")

    y -= 12
    payment_method = order_details.get("payment_method", "None")
    c.drawCentredString(width / 2, y, f"Payment Mode: {payment_method}")


    # Footer
    y -= 10
    c.setDash(3, 1)
    c.line(5, y - 3, 215, y - 3)  # Line above total
    c.setDash()  # Line before footer
    y -= 10
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width / 2, y, "Thank you for visiting!")

    c.save()
    return file_path    

def generate_bill_txt(order_details):
    """Generates a text file receipt with the given order details."""
    order_id = order_details.get("order_id", "N/A")
    filename = f"bill_{order_id}.txt"
    file_path = os.path.join(BILL_SAVE_PATH, filename)

    total_amount = sum(item["quantity"] * item["price"] for item in order_details.get("items", []))
    discount_percentage = 5
    discount_amount = (total_amount * discount_percentage) / 100
    payable_amount = total_amount - discount_amount

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(f"{order_details.get('kitchen_name', 'Guest')}\n")
        file.write("========================\n")
        file.write(f"Invoice: {order_id}\n")
        file.write(f"Date: {order_details.get('created_at', 'Unknown Date')}\n")
        file.write(f"Customer: {order_details.get('customer_name', 'Guest')}\n")
        
        # Address wrapping
        address = order_details.get("address", "")
        address_lines = textwrap.wrap(f"Address: {address}", width=40)
        for line in address_lines:
            file.write(line + "\n")
        
        file.write("------------------------\n")
        for item in order_details.get("items", []):
            file.write(f"{item['name']} x {item['quantity']}  ₹{item['price']:.2f} = ₹{item['quantity'] * item['price']:.2f}\n")
        
        file.write("------------------------\n")
        file.write(f"Total: ₹{total_amount:.2f}\n")
        file.write(f"Discount ({discount_percentage}%): ₹{discount_amount:.2f}\n")
        file.write(f"Payable Amount: ₹{payable_amount:.2f}\n")
        file.write("========================\n")
        file.write(f"Payment Mode: {order_details.get('payment_method', 'None')}\n")
        file.write("\nThank You for Visiting!\n")
    
    return file_path

def print_bill_pos(order_details):
    """Sends the bill to an ESC/POS receipt printer."""
    try:
        printer = Usb(0x04b8, 0x0e15)  # Adjust vendor and product ID for your printer
        total_amount = sum(item["quantity"] * item["price"] for item in order_details.get("items", []))
        discount_percentage = 5
        discount_amount = (total_amount * discount_percentage) / 100
        payable_amount = total_amount - discount_amount

        printer.text("\n  VEG RESTAURANT\n")
        printer.text("========================\n")
        printer.text(f"Invoice: {order_details.get('order_id', 'N/A')}\n")
        printer.text(f"Date: {order_details.get('created_at', 'Unknown Date')}\n")
        printer.text(f"Customer: {order_details.get('customer_name', 'Guest')}\n")
        
        # Address wrapping
        address = order_details.get("address", "")
        address_lines = textwrap.wrap(f"Address: {address}", width=40)
        for line in address_lines:
            printer.text(line + "\n")
        
        printer.text("------------------------\n")
        for item in order_details.get("items", []):
            printer.text(f"{item['name']} x {item['quantity']}  ₹{item['price']:.2f} = ₹{item['quantity'] * item['price']:.2f}\n")
        
        printer.text("------------------------\n")
        printer.text(f"Total: ₹{total_amount:.2f}\n")
        printer.text(f"Discount ({discount_percentage}%): ₹{discount_amount:.2f}\n")
        printer.text(f"Payable Amount: ₹{payable_amount:.2f}\n")
        printer.text("========================\n")
        printer.text(f"Payment Mode: {order_details.get('payment_method', 'None')}\n")
        printer.text("\nThank You for Visiting!\n")
        printer.cut()
        return "Bill printed successfully"
    
    except Exception as e:
        return f"Printing error: {e}"

def generate_and_print_bill(order_details):
    """ Generates a bill (PDF, TXT) and prints it. """
    pdf_path = generate_bill_pdf(order_details)  
    txt_path = generate_bill_txt(order_details)  
    print_response = print_bill_pos(order_details)  

    return {
        "pdf_path": pdf_path,
        "txt_path": txt_path,
        "print_status": print_response
    }
