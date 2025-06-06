import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pdf2image import convert_from_path
import pdfplumber, re, csv

class PDFViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("My Bank Account Monitor")
        self.root.geometry("1680x1024")

        self.pdf_path = None
        self.pdf_pages = []
        self.current_page = 0
        self.original_image = None
        self.zoom_factor = 1.0

        self.create_widgets()

    def create_widgets(self):
        # --- Top Frame with Buttons ---
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        open_btn = tk.Button(top_frame, text="Open PDF", command=self.open_pdf)
        open_btn.pack(side=tk.LEFT, padx=5)

    def open_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            try:
                PDFViewerWindow(self.root, file_path)  # Launch new window
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF: {e}")


class PDFViewerWindow:
    def __init__(self, parent, pdf_path):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Viewing: {pdf_path}")
        self.window.geometry("1680x1024")

        self.pdf_path = pdf_path
        self.pdf_pages = convert_from_path(pdf_path, dpi=150)
        self.current_page = 0
        self.zoom_factor = 1.0
        self.original_image = None

        self.create_widgets()
        self.show_page(0)

    def create_widgets(self):
        top_frame = tk.Frame(self.window)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.prev_btn = tk.Button(top_frame, text="<< Prev", command=self.prev_page)
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(top_frame, text="Next >>", command=self.next_page)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        zoom_in_btn = tk.Button(top_frame, text="Zoom In (+)", command=self.zoom_in)
        zoom_in_btn.pack(side=tk.LEFT, padx=5)

        zoom_out_btn = tk.Button(top_frame, text="Zoom Out (-)", command=self.zoom_out)
        zoom_out_btn.pack(side=tk.LEFT, padx=5)

        export_btn = tk.Button(top_frame, text="Export CSV", command=self.export_operations)
        export_btn.pack(side=tk.LEFT, padx=5)

        self.page_label = tk.Label(top_frame, text="Page: N/A")
        self.page_label.pack(side=tk.LEFT, padx=10)

        canvas_frame = tk.Frame(self.window)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="gray")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scroll = tk.Scrollbar(self.window, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.canvas.bind('<Configure>', self.resize_displayed_image)
        self.canvas.bind_all("<MouseWheel>", self.mouse_wheel)

    def show_page(self, page_num):
        if 0 <= page_num < len(self.pdf_pages):
            self.original_image = self.pdf_pages[page_num]
            self.display_resized_image()
            self.page_label.config(text=f"Page: {page_num + 1} / {len(self.pdf_pages)}")

    def display_resized_image(self):
        if not self.original_image:
            return
        canvas_width = self.canvas.winfo_width()
        if canvas_width < 100:
            return
        zoomed_width = int(self.original_image.width * self.zoom_factor)
        zoomed_height = int(self.original_image.height * self.zoom_factor)
        resized_image = self.original_image.resize((zoomed_width, zoomed_height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def resize_displayed_image(self, event=None):
        self.display_resized_image()

    def next_page(self):
        if self.current_page < len(self.pdf_pages) - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.display_resized_image()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.display_resized_image()

    def mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def export_operations(self):
        extract_operations_from_pdf(self.pdf_path)
        messagebox.showinfo("Success", f"Operations exported to CSV.")


def extract_operations_from_pdf(pdf_path, output_csv="data/operations.csv"):
    operations = []

    # Regex to detect lines that look like operations
    operation_pattern = re.compile(
        r"(\d{2}\.\d{2})\s+(\d{2}\.\d{2})\s+(Carte|Virement|Prlv|Ret DAB|Cotis|Commission d'intervention|Ass\.|Netflix|Steam|Amazon|.*?)(.*?)\s+(\d{1,3}(?:[.,]\d{2}))\s*¨"
    )

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")

            for line in lines:
                match = operation_pattern.search(line)
                if match:
                    date_ope = match.group(1)
                    date_val = match.group(2)
                    type_op = match.group(3).strip()
                    desc = match.group(4).strip()
                    amount = match.group(5).replace(",", ".")
                    
                    # Decide debit/credit from context (assume credit if "De M." or "Vir Inst" has name)
                    is_credit = "De M." in desc or "vers Alice" in desc or "France Travail" in desc

                    operations.append({
                        "Date Opé.": date_ope,
                        "Date Valeur": date_val,
                        "Type": type_op,
                        "Description": desc,
                        "Débit (€)": "" if is_credit else amount,
                        "Crédit (€)": amount if is_credit else ""
                    })

    # Write to CSV
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date Opé.", "Date Valeur", "Type", "Description", "Débit (€)", "Crédit (€)"])
        writer.writeheader()
        writer.writerows(operations)

    print(f"[✓] Extracted {len(operations)} operations to: {output_csv}")


def main():
    root = tk.Tk()
    app = PDFViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()