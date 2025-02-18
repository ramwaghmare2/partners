import os
from reportlab.pdfgen import canvas
from escpos.printer import Usb
from config import Config  

VENDOR_ID = Config.VENDOR_ID
PRODUCT_ID = Config.PRODUCT_ID

BILL_SAVE_PATH = r"C:\Users\Ram\Desktop\PARTNER\order_bills"

os.makedirs(BILL_SAVE_PATH, exist_ok=True)

try:
    printer = Usb(VENDOR_ID, PRODUCT_ID, timeout=0)
except Exception as e:
    printer = None
    print(f"Printer connection error: {e}")

def generate_bill_pdf(order_details):
    filename = f"bill_{order_details['order_id']}.pdf"
    file_path = os.path.join(BILL_SAVE_PATH, filename)

    c = canvas.Canvas(file_path)
    c.setFont("Helvetica", 12)

    c.drawString(100, 800, "Food Delivery Service")
    c.drawString(100, 780, f"Order ID: {order_details['order_id']}")
    c.drawString(100, 760, f"Customer: {order_details['customer_name']}")
    c.drawString(100, 740, f"Address: {order_details['address']}")
    c.drawString(100, 720, f"Date & Time: {order_details['created_at']}")

    y_position = 700
    c.drawString(100, y_position, "Items Ordered:")
    for item in order_details["items"]:
        y_position -= 20
        c.drawString(120, y_position, f"{item['name']} x {item['quantity']} - ₹{item['price']}")

    y_position -= 40
    c.drawString(100, y_position, f"Total Amount: ₹{order_details['total_amount']}")

    c.save()
    return file_path

def generate_bill_txt(order_details):
    filename = f"bill_{order_details['order_id']}.txt"
    file_path = os.path.join(BILL_SAVE_PATH, filename)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n  FOOD DELIVERY SERVICE\n")
        file.write("========================\n")
        file.write(f"Order ID: {order_details['order_id']}\n")
        file.write(f"Customer: {order_details['customer_name']}\n")
        file.write(f"Address: {order_details['address']}\n")
        file.write(f"Date & Time: {order_details['created_at']}\n")
        file.write("------------------------\n")

        for item in order_details["items"]:
            file.write(f"{item['name']} x {item['quantity']}  ₹{item['price']}\n")

        file.write("------------------------\n")
        file.write(f"Total: ₹{order_details['total_amount']}\n")
        file.write("========================\n")
        file.write("\nThank You!\n")

    return file_path

def print_bill_pos(order_details):
    if not printer:
        return "Printer not found or disconnected"

    try:
        printer.text("\n  FOOD DELIVERY SERVICE\n")
        printer.text("========================\n")
        printer.text(f"Order ID: {order_details['order_id']}\n")
        printer.text(f"Customer: {order_details['customer_name']}\n")
        printer.text(f"Address: {order_details['address']}\n")
        printer.text(f"Date & Time: {order_details['created_at']}\n")
        printer.text("------------------------\n")

        for item in order_details["items"]:
            printer.text(f"{item['name']} x {item['quantity']}  ₹{item['price']}\n")

        printer.text("------------------------\n")
        printer.text(f"Total: ₹{order_details['total_amount']}\n")
        printer.text("========================\n")
        printer.text("\nThank You!\n")
        printer.cut()
        return "Bill printed successfully"

    except Exception as e:
        return f"Printing error: {e}"

def generate_and_print_bill(order_details):
    pdf_path = generate_bill_pdf(order_details)  
    txt_path = generate_bill_txt(order_details)  
    print_response = print_bill_pos(order_details)  

    return {
        "pdf_path": pdf_path,
        "txt_path": txt_path,
        "print_status": print_response
    }
