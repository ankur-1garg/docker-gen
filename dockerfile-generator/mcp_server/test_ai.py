# mcp_server/test_ai.py (Adapted for Gemini)

# Note: Google library doesn't strictly require asyncio for basic generate_content
# Import Gemini function
from app.core.ai_service import get_gemini_dockerfile_suggestion, create_dockerfile_prompt, AIServiceError


def main():  # Can be sync now
    print("Testing Google Gemini Dockerfile suggestion...")

    # Example request details
    language = "python"
    version = "3.11"
    dependencies = ["fastapi", "uvicorn[standard]"]  # Changed deps example
    port = 8000
    generic_image = "python:3.11-slim"  # Use the generic name

    # Construct the prompt using the example helper
    test_prompt = create_dockerfile_prompt(
        language=language,
        version=version,
        dependencies=dependencies,
        port=port,
        generic_base_image=generic_image,
        additional_instructions="Use Uvicorn as the server for FastAPI."
    )

    print("\n--- Generated Prompt ---")
    print(test_prompt)
    print("------------------------\n")

    try:
        # Call the Gemini function
        ai_suggestion = get_gemini_dockerfile_suggestion(test_prompt)

        print("--- AI Suggestion (Gemini) ---")
        print(ai_suggestion)
        print("------------------------------\n")

        # Check if the suggestion contains the generic base image
        if generic_image in ai_suggestion:
            print(
                f"SUCCESS: AI suggestion includes the requested generic base image '{generic_image}'.")
        else:
            print(
                f"WARNING: AI suggestion might not contain the exact generic base image '{generic_image}'. Manual check needed.")
            print(
                "This might be okay if the AI chose a compatible variant, but Day 7 logic relies on finding it.")

    except AIServiceError as e:
        print(f"ERROR: AI Service failed: {e}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        
        # Inside test_ai.py, in the main function
    # --- BEFORE calling get_gemini_dockerfile_suggestion ---

    # print("\n--- Listing Available Models (supporting generateContent) ---")
    # try:
    #     import google.generativeai as genai # Ensure import is here
    #     # Remove the 'if is_configured:' check for this temporary code
    #     for m in genai.list_models():
    #         # Check if 'generateContent' is a supported method for the model
    #         if 'generateContent' in m.supported_generation_methods:
    #             print(m.name) # Print the model name (e.g., models/gemini-1.0-pro)
    # except Exception as list_err:
    #     print(f"Error listing models: {list_err}") # This will likely show config errors if any
    # print("----------------------------------------------------------\n")

    # --- CONTINUE with the rest of the main function ---
    # Construct the prompt...
    # try: Call get_gemini_dockerfile_suggestion...
    # except...

if __name__ == "__main__":
    main()
