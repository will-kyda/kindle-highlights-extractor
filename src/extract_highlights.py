import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from bs4 import BeautifulSoup
import re
import os
import unicodedata
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter

# --- Functions for extracting Kindle highlights ---

def load_html(file_path):
    """Loads the HTML file and returns a BeautifulSoup object."""
    with open(file_path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file.read(), "lxml")

def extract_highlights(soup):
    """
    Extracts the book title and highlights.
    Returns a list of tuples (title, identifier (page or location), text).
    """
    book_title_elem = soup.find("div", class_="bookTitle")
    book_title = book_title_elem.text.strip() if book_title_elem else "Unknown Title"

    # Normalize text to avoid display issues
    book_title = unicodedata.normalize("NFKC", book_title).encode("utf-8").decode("utf-8")
    book_title = book_title.replace("’", "'")  # Replace typographic apostrophe

    highlights = []
    note_headings = soup.find_all("div", class_="noteHeading")
    note_texts = soup.find_all("div", class_="noteText")

    for heading, text in zip(note_headings, note_texts):
        # Check if it is a page or a location
        page_match = re.search(r'Page (\d+)', heading.text)
        location_match = re.search(r'Location (\d+)', heading.text)

        if page_match:
            identifier = f"Page {page_match.group(1)}"
        elif location_match:
            identifier = f"Location {location_match.group(1)}"
        else:
            identifier = "N/A"

        highlights.append((book_title, identifier, text.text.strip()))
    
    return highlights

def save_to_pdf(highlights, output_path):
    """
    Generates a PDF file displaying the book title and highlights.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()

    # Book title style
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontName='Times-Roman',
        fontSize=24,
        alignment=1,  # Centered
        spaceAfter=20
    )

    # Highlight text style
    body_style = ParagraphStyle(
        name='BodyStyle',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=12,
        leading=14,
        spaceAfter=6
    )

    # Page or location identifier style
    id_style = ParagraphStyle(
        name='IdStyle',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor='#33658A'  # Custom color
    )

    elements = []

    if highlights:
        # Book title
        book_title = highlights[0][0]
        elements.append(Paragraph(book_title, title_style))
        elements.append(Spacer(1, 20))

        # Add highlights
        for _, identifier, text in highlights:
            elements.append(Paragraph(f'<font color="#33658A"><b>{identifier}</b></font>', id_style))
            elements.append(Paragraph(text, body_style))
            elements.append(Spacer(1, 18))
    else:
        elements.append(Paragraph("No highlights found.", body_style))

    doc.build(elements)
    return output_path

def process_file(input_file, output_file):
    """Processes the HTML file and generates a PDF."""
    soup = load_html(input_file)
    highlights = extract_highlights(soup)
    save_to_pdf(highlights, output_file)
    return output_file

# --- Graphical User Interface (Tkinter) ---

# Create main window
root = tk.Tk()
root.title("Kindle Highlights Extractor")
root.geometry("450x250")
root.resizable(False, False)

selected_file = None

def select_file():
    """Opens a dialog to select the Kindle highlights HTML file."""
    global selected_file
    filetypes = [("HTML Files", "*.html"), ("All Files", "*.*")]
    selected_file = filedialog.askopenfilename(
        title="Select Kindle highlights file",
        filetypes=filetypes
    )
    if selected_file:
        file_label.config(text=f"Selected File: {selected_file}")
        transform_button.config(state=tk.NORMAL)
    else:
        file_label.config(text="No file selected")
        transform_button.config(state=tk.DISABLED)

def transform_file():
    """Processes the selected file and saves as a PDF."""
    if selected_file:
        base_name = os.path.splitext(os.path.basename(selected_file))[0]
        output_file = filedialog.asksaveasfilename(
            title="Save PDF File",
            initialfile=f"{base_name}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if output_file:
            try:
                process_file(selected_file, output_file)
                messagebox.showinfo("Success", f"File generated: {output_file}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        else:
            messagebox.showinfo("Cancelled", "Save cancelled.")
    else:
        messagebox.showwarning("Warning", "Please select a file first.")

# UI Elements

title_label = tk.Label(root, text="Kindle Highlights Extractor", font=("Helvetica", 18, "bold"))
title_label.pack(pady=15)

select_button = tk.Button(root, text="Add Kindle Highlights File", font=("Helvetica", 12), command=select_file)
select_button.pack(pady=10)

file_label = tk.Label(root, text="No file selected", font=("Helvetica", 10))
file_label.pack(pady=5)

transform_button = tk.Button(root, text="Convert", font=("Helvetica", 12), state=tk.DISABLED, command=transform_file)
transform_button.pack(pady=15)

root.mainloop()
