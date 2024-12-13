from grobid.grobid_paper_extractor import extract_filtered_sections_from_tei, send_request_to_grobid, extract_tei_from_pdf
import os
HEAD_KEYWORDS = ["evaluation", "methodology", "related work", "conclusion", "baseline"]

count = 0

#for each file in downloaded papers, extract the sections and count the keywords
for file in os.listdir("more_paper_downloads2"):
    if file.endswith(".pdf"):
        pdf_path = os.path.join("more_paper_downloads2", file)
        tei = extract_tei_from_pdf(pdf_path)
        sections = extract_filtered_sections_from_tei(tei, HEAD_KEYWORDS)
       
        if sections == None:
            continue
        if len(sections) > 0:
            count += 1
            
