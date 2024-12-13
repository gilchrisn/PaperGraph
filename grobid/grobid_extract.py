from grobid_paper_extractor import extract_filtered_sections_from_tei, send_request_to_grobid, extract_tei_from_pdf, extract_metadata, format_extracted_data
import os

HEAD_KEYWORDS = [
    "evaluation", "methodology", "related work", "conclusion", "baseline"
]

directory = "downloads"

for filename in os.listdir(directory):
    pdf_path = os.path.join(directory, filename)
    print(f"Processing: {pdf_path}")

    tei_xml = extract_tei_from_pdf(pdf_path)

    if tei_xml:
        # Extract filtered sections
        filtered_sections = extract_filtered_sections_from_tei(tei_xml, HEAD_KEYWORDS)
        
    formatted_data = []

    if filtered_sections:
        for section_title, content in filtered_sections.items():
            formatted_data.append(f"\n{section_title}:\n{content[len(section_title):]}")  # Truncate content for brevity
    with open(f"results2.txt", "a") as f:
        f.write("\n".join(formatted_data))


       
    
        