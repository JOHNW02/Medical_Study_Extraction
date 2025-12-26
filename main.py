import json
import sys
from openai import OpenAI
import os
import argparse


# This function extracts text output from the response from OpenAI API.
# Input: 
#   response: Raw response from OpenAI API.
# Output: Result in given JSON format in text.
def extract_output_text(response):

    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    for item in response.output:
        for content in getattr(item, "content", []):
            if content.type in ("output_text", "text"):
                return content.text

    raise RuntimeError("Could not extract model output text.")

# This function uploads pdf to OpenAI client, extracts and returns JSON output.
# Input: 
#   client: OpenAI API client object.
#   pdf_path: Path of the medical study PDF.
# Output: result in formatted JSON object.
def process_pdf(client, pdf_path):

    # Upload PDF to OPENAI Client
    uploaded_file = client.files.create(
        file=open(pdf_path, "rb"),
        purpose="assistants"
    )

    # Call model with PDF input
    response = client.responses.create(
        model="gpt-5-mini",
    # Forced response format through prompt
        input=[
            {
                "role": "system",
                "content": (
                "You extract structured information from biomedical research papers.\n"
                "Rules:\n"
                "- Use ONLY the provided PDF.\n"
                "- Do NOT guess or infer.\n"
                "- If information is not explicitly stated, set it to null.\n"
                "- Return EXACTLY one JSON object.\n"
                "- Do NOT include any text outside the JSON.\n\n"
                "JSON schema:\n"
                "{\n"
                "  title: string | null,\n"
                "  study_design: string | null,\n"
                "  population: string | null,\n"
                "  sample_size: integer | null,\n"
                "  outcome: string | null,\n"
                "  effect_size: {\n"
                "    type: string | null,\n"
                "    value: number | null,\n"
                "    lower_ci: number | null,\n"
                "    upper_ci: number | null\n"
                "  }\n"
                "}"
            )
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Extract the required study information."},
                    {"type": "input_file", "file_id": uploaded_file.id}
                ]
            }
        ]
    )

    # Extract output
    output_text = extract_output_text(response)
    parsed = json.loads(output_text)

    return parsed

# This function validates the output from OpenAI API. The function checks if all required fields present,
# if data types are correct, and if the values are nuerically plausible.
# Input:
#   data: The JSON object from function process_pdf.
# Output: List of errors that the output encounters. If no error occurs, the function will return an empty list.
def validate_extraction(data):
    errors = []

    REQUIRED_FIELDS = [
        "title",
        "study_design",
        "population",
        "sample_size",
        "outcome",
        "effect_size"
    ]

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing field: {field}")

    # Check sample size
    sample_size = data.get("sample_size")
    if sample_size is not None:
        if not isinstance(sample_size, int):
            errors.append("sample_size must be an integer or null")
        elif sample_size <= 0:
            errors.append("sample_size must be > 0")

    # Check effect size
    effect = data.get("effect_size")
    if not isinstance(effect, dict):
        errors.append("effect_size must be an object")
    else:
        for key in ["type", "value", "lower_ci", "upper_ci"]:
            if key not in effect:
                errors.append(f"Missing effect_size field: {key}")

        value = effect.get("value")
        lower = effect.get("lower_ci")
        upper = effect.get("upper_ci")

        for name, v in [("value", value), ("lower_ci", lower), ("upper_ci", upper)]:
            if v is not None and not isinstance(v, (int, float)):
                errors.append(f"effect_size.{name} must be numeric or null")

        if lower is not None and upper is not None:
            if lower > upper:
                errors.append("lower_ci cannot be greater than upper_ci")

        if value is not None and lower is not None and upper is not None:
            if not (lower <= value <= upper):
                errors.append("effect_size.value must be between lower_ci and upper_ci")

    return errors

# The main function parses the command line input to retrieve input OPENAI API Key and paths of pdf files.
# Valid outputs will be saved to output directory, while invalid outputs will be saved to invalid_output directory.
def main():
    parser = argparse.ArgumentParser(
        description="Extract study information from multiple PDFs"
    )
    parser.add_argument(
        "--api_key",
        help="OpenAI API key"
    )

    parser.add_argument(
        "pdfs",
        nargs="+",
        help="One or more PDF files"
    )

    args = parser.parse_args()

    api_key = args.api_key
    if not api_key:
        print("ERROR: OpenAI API key not provided.")
        sys.exit(1)

    os.makedirs('output', exist_ok=True)
    os.makedirs('invalid_output', exist_ok=True)

    client = OpenAI(api_key=api_key)

    results = []

    for pdf in args.pdfs:
        print(f"[INFO] Processing {pdf}...")
        try:
            result = process_pdf(client, pdf)
            error_check = validate_extraction(result)

            # -------- Path handling (IMPORTANT PART) --------
            pdf_filename = os.path.basename(pdf)  
            base_name, _ = os.path.splitext(pdf_filename)
            valid_output_path = os.path.join(
                'output',
                base_name + ".json"
            )
            invalid_output_path = os.path.join(
                'invalid_output',
                base_name + ".json"
            )
            results.append(result)

            if len(error_check) == 0:
                with open(valid_output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                print(f"[OK] Saved → {valid_output_path}")
            else:
                with open(invalid_output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                print(f"[Invalid] Saved → {invalid_output_path}")

        except Exception as e:
            print(f"[ERROR] Failed on {pdf}: {e}")
    return results

if __name__ == "__main__":

    results = main()
    for r in results:
        print(r)

    