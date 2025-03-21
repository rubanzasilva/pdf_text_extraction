import re
import pandas as pd
import PyPDF2

def extract_disease_data(pdf_path):
    # Read the PDF file
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    
    # Define regex patterns for extracting section headers
    disease_pattern = r"(\d+\.\d+\.\d+|\d+\.\d+)\s+([^\n]+?)\s+ICD10\s+CODE:\s+([^\n]+)"
    
    # Find all diseases in the text
    disease_matches = list(re.finditer(disease_pattern, text, re.DOTALL))
    
    # Initialize lists to store extracted data
    diseases = []
    
    # Process each disease match
    for i, match in enumerate(disease_matches):
        section_num = match.group(1)
        disease_name = match.group(2).strip()
        icd10_code = match.group(3).strip()
        
        # Extract text for this disease (up to the next disease or end of text)
        start_idx = match.end()
        if i < len(disease_matches) - 1:
            end_idx = disease_matches[i+1].start()
        else:
            end_idx = len(text)
        
        disease_text = text[start_idx:end_idx]
        
        # Extract individual sections using more specific patterns
        def extract_section(section_name, text):
            pattern = rf"{section_name}(.*?)(?=\n[A-Z][a-z]+|\n\d+\.\d+|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return ""
        
        # Extract specific sections
        description = ""
        # Extract the description which is usually the first paragraph after ICD code
        desc_match = re.search(r"^(.*?)(?=\nCauses|\nCause)", disease_text, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()
        
        # Extract other sections using safer approach
        try:
            causes = extract_section("Causes|Cause", disease_text)
        except:
            causes = ""
            
        try:
            clinical_features = extract_section("Clinical features", disease_text)
        except:
            clinical_features = ""
            
        try:
            differential_diagnosis = extract_section("Differential diagnosis", disease_text)
        except:
            differential_diagnosis = ""
            
        try:
            investigations = extract_section("Investigations", disease_text)
        except:
            investigations = ""
            
        try:
            management = extract_section("Management", disease_text)
        except:
            management = ""
            
        try:
            prevention = extract_section("Prevention", disease_text)
        except:
            prevention = ""
            
        # Check for classification section
        classification = ""
        try:
            class_match = re.search(r"Classification of.*?(?=\n[A-Z][a-z]+|\n\d+\.\d+|\Z)", disease_text, re.DOTALL)
            if class_match:
                classification = class_match.group(0).strip()
        except:
            classification = ""
        
        # Extract treatment details
        treatment_details = ""
        try:
            treatment_match = re.search(r"TREATMENT\s+LOC.*?(?=\nNotes|\nPrevention|\n\d+\.\d+|\Z)", disease_text, re.DOTALL)
            if treatment_match:
                treatment_details = treatment_match.group(0).strip()
        except:
            treatment_details = ""
        
        # Clean up extracted text
        def clean_text(text):
            if not text:
                return ""
            text = re.sub(r'\s*~\s*', '\n- ', text)  # Replace ~ with bullet points
            text = re.sub(r'\s+', ' ', text)         # Normalize whitespace
            text = text.replace('\n ', '\n')         # Fix newlines
            return text.strip()
        
        # Create a dictionary for this disease
        disease_data = {
            'Section': section_num,
            'Disease_Name': disease_name,
            'ICD10_Code': icd10_code,
            'Description': clean_text(description),
            'Causes': clean_text(causes),
            'Clinical_Feature': clean_text(clinical_features),
            'Differential_Diag': clean_text(differential_diagnosis),
            'Investigations': clean_text(investigations),
            'Management': clean_text(management),
            'Prevention': clean_text(prevention),
            'Classification': clean_text(classification),
            'Treatment_Details': clean_text(treatment_details)
        }
        
        # Add to our list
        diseases.append(disease_data)
    
    # Create DataFrame
    df = pd.DataFrame(diseases)
    
    return df

# Example usage
pdf_path = "ug_23_sample.pdf"  # Update with your PDF path
diseases_df = extract_disease_data(pdf_path)

# Display the DataFrame info
print(f"Extracted {len(diseases_df)} diseases")
print(diseases_df.columns)

# Save to CSV
diseases_df.to_csv("ucg_sample.csv", index=False)

# Print summary of data extraction
print("\nExtracted data summary:")
for col in diseases_df.columns:
    non_empty = diseases_df[col].astype(str).str.strip().str.len() > 0
    print(f"{col}: {non_empty.sum()} non-empty entries out of {len(diseases_df)}")

print("\nDataset saved to uganda_clinical_guidelines_diseases.csv")