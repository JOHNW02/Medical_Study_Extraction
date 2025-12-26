# Medical Study Extraction
This project provides a command-line tool for extracting structured study information from biomedical research articles in PDF format using a large language model (LLM). The system is designed to support batch processing, strict handling of missing information, and basic post-extraction validation to ensure research-grade reliability.


## Overview

Given one or more biomedical research PDFs, the tool:
- Uploads each PDF directly to the OpenAI API
- Extracts structured study metadata
- Validates extracted fields for missing or malformed values
- Saves valid and invalid results into separate output directories

This project uses OpenAI’s large language models due to their strong performance in long-document understanding, biomedical text comprehension, and structured information extraction. In particular, the GPT-5-mini model was selected as a practical trade-off between extraction accuracy, computational efficiency, and cost. GPT-5-mini provides sufficient reasoning capability to identify explicitly reported study details while enabling scalable batch processing of multiple research articles, making it well-suited for research pipelines and exploratory evidence synthesis workflows.

## Requirements
- Python ≥ 3.9.2
- OpenAI Python SDK
  
Install dependencies with:
```
pip install -r requirements.txt
```

## Usage
The tool is executed from the command line and requires two inputs:
- An OpenAI API key for authentication
- One or more PDF files containing biomedical research articles

Run the tool from the command line:
```
python main.py --api_key <YOUR_API_KEY> <paper1.pdf> <paper2.pdf>
```

If the API key is not provided, the program will terminate with an error message before processing any files.

## Output

For each input PDF, the system generates exactly one JSON file containing the extracted study information. After execution, the main function returns a list of JSON objects. Output files are always saved to disk, regardless of whether the extraction passes validation.

### Output Directories

The tool organizes results into two separate directories:

- `output/`  
  Contains JSON files for extractions that pass all validation checks.

- `invalid_output/`  
  Contains JSON files for extractions that fail one or more validation checks, such as missing required fields or invalid numeric values.

Both directories are automatically created if they do not already exist. The output names are the same with the input PDF names.

## Validation Logic

After structured information is extracted from each PDF, the system applies a post-extraction validation step to assess the basic correctness and consistency of the generated output. This validation layer operates independently of the language model and is intended to detect missing fields, type mismatches, and simple numeric inconsistencies.

### Validation Scope

The validation logic performs the following checks:

- **Field Presence**  
  Verifies that all required top-level fields (e.g., `title`, `study_design`, `population`, `sample_size`, `outcome`, and `effect_size`) are present in the extracted JSON object.

- **Type Checking**  
  Ensures that values conform to expected data types, such as integers for `sample_size` and numeric values for effect size estimates and confidence interval bounds.

- **Numeric Sanity Checks**  
  Applies lightweight consistency checks to numeric fields, including:
  - `sample_size` must be greater than zero if provided
  - Confidence interval lower bounds must not exceed upper bounds
  - Effect size point estimates must lie within reported confidence intervals when all values are present


