import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pdfplumber, re

class TableauLikeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Dashboard (Tableau-style)")
        self.root.geometry("1000x700")

        self.create_widgets()

    def create_widgets(self):
        #Load Buttons
        buttons_frame = tk.Frame(self.root).pack(side=tk.TOP, pady=10)
        load_pdf_btn = tk.Button(buttons_frame, text="Load PDF", command=self.load_pdf)
        load_csv_btn = tk.Button(buttons_frame, text="Load CSV", command=self.load_csv)
        load_csv_btn.pack(side="left")
        load_pdf_btn.pack(side="left")

        # Table view
        self.tree = ttk.Treeview(self.root)
        self.tree.pack(fill="both", expand=True)

        # Plot buttons
        plot_frame = tk.Frame(self.root)
        plot_frame.pack(pady=10)

        tk.Button(plot_frame, text="Bar Chart", command=self.plot_bar).pack(side="left", padx=5)
        tk.Button(plot_frame, text="Pie Chart", command=self.plot_pie).pack(side="left", padx=5)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        self.df = pd.read_csv(file_path)
        self.display_table(self.df)

    def load_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            try:
                self.df = extract_operations_from_pdf(file_path)
                self.display_table(self.df)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def display_table(self, df):
        # Clear previous table
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"

        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))

    def plot_bar(self):
        if hasattr(self, 'df'):
            column = self.df.columns[0]  # use first column
            counts = self.df[column].value_counts()

            fig, ax = plt.subplots(figsize=(6,4))
            counts.plot(kind="bar", ax=ax)
            ax.set_title(f"Bar Chart of {column}")

            self.show_plot(fig)

    def plot_pie(self):
        if hasattr(self, 'df'):
            column = self.df.columns[0]  # use first column
            counts = self.df[column].value_counts()

            fig, ax = plt.subplots(figsize=(6,4))
            counts.plot(kind="pie", autopct="%1.1f%%", ax=ax)
            ax.set_ylabel("")
            ax.set_title(f"Pie Chart of {column}")

            self.show_plot(fig)

    def show_plot(self, fig):
        plot_window = tk.Toplevel(self.root)
        plot_window.title("Plot")

        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def extract_operations_from_pdf(pdf_path):
    operations = []

    # Regex to detect lines that look like operations
    operation_pattern = re.compile(
        r"(\d{2}\.\d{2})\s+(\d{2}\.\d{2})\s+(Carte|Virement|Prlv|Ret DAB|Cotis|Commission d'intervention|Ass\.|Netflix|Steam|Amazon|.*?)(.*?)\s+((\d{1,3}(?:\s\d{3})*)(?:[.,]\d{2}))\s*"
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
                    if type_op == "Virement":
                        is_credit = "De" in desc or "France Travail" in desc
                    else:
                        is_credit = False

                    operations.append({
                        "Date Opé.": date_ope,
                        "Date Valeur": date_val,
                        "Type": type_op,
                        "Description": desc,
                        "Débit (€)": "" if is_credit else amount,
                        "Crédit (€)": amount if is_credit else ""
                    })

    print(f"[✓] Extracted {len(operations)} operations")
    return pd.DataFrame(operations)

if __name__ == "__main__":
    root = tk.Tk()
    app = TableauLikeApp(root)
    root.mainloop()
