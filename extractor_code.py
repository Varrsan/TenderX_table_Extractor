import os
import json
import pdfplumber

# Directory containing PDFs
INPUT_DIR = "set2"
OUTPUT_FILE = "extracted_json.json"  # Single JSON file

# Keywords for table header detection
TABLE_KEYWORDS = ["approved", "makes", "manufacturer"]

def extract_text(pdf_path):
    """Extract text from the PDF to locate relevant table pages."""
    with pdfplumber.open(pdf_path) as pdf:
        full_text = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)

def find_relevant_tables(pdf_path):
    """Find pages containing relevant tables based on keywords."""
    relevant_pages = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_table()
            if tables:
                first_row = tables[0]  # Extract table header
                header_text = " | ".join([str(cell) for cell in first_row if cell])  # Convert to string
                
                # Check if the header contains required keywords
                if any(keyword in header_text.lower() for keyword in TABLE_KEYWORDS):
                    relevant_pages.append(page_num)
    
    return relevant_pages

def extract_approved_makes_table(pdf_path, relevant_pages):
    """Extracts only the 'Approved Makes and Manufacturer' table and structures data correctly."""
    extracted_data = []
    current_item = None  # Store the last detected product category

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in relevant_pages:
            page = pdf.pages[page_num - 1]  # Pages are 0-indexed
            tables = page.extract_table()

            if tables:
                for row in tables:
                    if not row or all(cell is None for cell in row):  # Skip empty rows
                        continue

                    first_cell = str(row[0]).strip() if row[0] else ""

                    # If first cell looks like a product category, update current_item
                    if first_cell and not first_cell.isnumeric():
                        current_item = first_cell
                        extracted_data.append({"itemName": current_item, "approvedMakes": []})

                    # Extract approved makes from the next columns
                    approved_makes = [str(cell).strip() for cell in row[1:] if cell]
                    
                    if current_item and approved_makes:
                        extracted_data[-1]["approvedMakes"].extend(approved_makes)

    return extracted_data if extracted_data else None

def process_pdf(pdf_path):
    """Process a single PDF and extract relevant tables."""
    relevant_pages = find_relevant_tables(pdf_path)

    if not relevant_pages:
        print(f"Table not found in {os.path.basename(pdf_path)}")
        return {
            "fileName": os.path.basename(pdf_path),
            "table_not_found": True
        }

    table_data = extract_approved_makes_table(pdf_path, relevant_pages)

    if table_data:
        return {
            "fileName": os.path.basename(pdf_path),
            "extractedData": table_data
        }
    else:
        print(f"Table not found in {os.path.basename(pdf_path)}")
        return {
            "fileName": os.path.basename(pdf_path),
            "table_not_found": True
        }

def main():
    """Main function to process all PDFs in the input directory and save one JSON file."""
    all_data = {"data": []}  # Store all PDFs in a list

    for pdf_file in os.listdir(INPUT_DIR):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, pdf_file)
            result = process_pdf(pdf_path)
            all_data["data"].append(result)  # Always add to maintain count consistency
    
    # Save all results in a single JSON file
    with open(OUTPUT_FILE, "w") as json_file:
        json.dump(all_data, json_file, indent=4)

    print("\n✅ Extraction Complete! JSON file saved as:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
