from concurrent.futures import ThreadPoolExecutor
import pytesseract
from PIL import Image
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# Add ThreadPoolExecutor with max_workers
executor = ThreadPoolExecutor(max_workers=8)

def query_ingredients_single(collection, ingredient, field):
    query = {"Ingredient": str(ingredient), field: {"$exists": True}}
    result = collection.find_one(query)

    non_friendly_ingredients = []
    friendly_ingredients = []

    if result:
        if result[field] and result[field].startswith('-') and str(result[field]) != '-HD':
            non_friendly_ingredients.append(result['Ingredient'])
        elif result[field] and result[field].startswith('+') and str(result[field]) != '+HD':
            friendly_ingredients.append(result['Ingredient'])
        elif result[field] and str(result[field]) == '-HD':
            friendly_ingredients.append(result['Ingredient'])
        elif result[field] and str(result[field]) == '+HD':
            non_friendly_ingredients.append(result['Ingredient']) 

    return non_friendly_ingredients, friendly_ingredients

def query_ingredients_parallel(collection, ingredients, field):
    with ThreadPoolExecutor(max_workers=8) as e:
        futures = [e.submit(query_ingredients_single, collection, ingredient, field) for ingredient in ingredients]
    results = [future.result() for future in futures]
    non_friendly_ingredients = [item for sublist in results for item in sublist[0]]
    friendly_ingredients = [item for sublist in results for item in sublist[1]]
    return non_friendly_ingredients, friendly_ingredients

def perform_ocr(image_path, collection, collection2):
    # Open the image file
    img = Image.open(image_path)

    # Use pytesseract to do OCR on the image
    extracted_text = pytesseract.image_to_string(img)
    # Process the extracted text
    processed_list = re.split(r',|:', extracted_text)
    processed_list_tokens = [item for item in processed_list if item]
    processed_list_tabs = [string.replace("\n", "").replace("INGREDIENTS","") for string in processed_list_tokens]
    processed_list_empty_strings = list(filter(None, processed_list_tabs))
    processed_list_no_leading_spaces = [item.lstrip() for item in processed_list_empty_strings]
    
    missing_ingredients = set(processed_list_no_leading_spaces) - set(collection.distinct("Ingredient"))
    print(missing_ingredients)
    for i in missing_ingredients:
        if collection2.find_one({"Ingredient": i}) is None:
            # Ingredient is not present in collection2, so insert it
            collection2.insert_one({"Ingredient": i})
        else:
            # Ingredient is already present in collection2, handle accordingly
            print(f"Ingredient '{i}' already exists in collection2.")

    print("OCR done.")

    return processed_list_no_leading_spaces