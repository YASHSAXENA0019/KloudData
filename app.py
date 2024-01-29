import os
import tempfile
from datetime import datetime
from flask import Flask, render_template, request
from utils import perform_ocr, query_ingredients_parallel
from main import connection

def create_app():
    app = Flask(__name__)
    

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            # Get the uploaded image file
            uploaded_file = request.files['image']

            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Generate a folder name based on the current date and time within the temporary directory
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                upload_folder = os.path.join(temp_dir, timestamp)

                # Ensure the folder exists
                os.makedirs(upload_folder, exist_ok=True)

                # Save the uploaded image to the generated folder
                image_filename = os.path.join(upload_folder, 'uploaded_image.png')
                uploaded_file.save(image_filename)

                # Get the selected fields from the form
                selected_fields = request.form.getlist('fields[]')
                collection, collection2 = connection()
                # Perform OCR and MongoDB query for each selected field
                results_by_field = {}
                processed_list_tokens = perform_ocr(image_filename, collection, collection2)

                # Use parallel processing for database queries for each selected field
                for field in selected_fields:
                    non_friendly_ingredients, friendly_ingredients = query_ingredients_parallel(collection, processed_list_tokens, field)
                    if non_friendly_ingredients:
                        # Custom result string for non-friendly ingredients
                        if field in ['Vegan', 'Vegetarian', 'Kosher', 'Halal']:
                            results_by_field[field] = f"Scanned product is not {field} because it contains {', '.join(non_friendly_ingredients)}."
                        elif field in ['Nuts', 'Gluten', 'Lactose']:
                            results_by_field[field] = f"Scanned product is not {field}-free because it contains {', '.join(non_friendly_ingredients)}."
                        elif field in ['Diabetes' , 'HeartDisease']:
                            results_by_field[field] = f"Scanned product may contribute to {field} because of {', '.join(non_friendly_ingredients)}."

                    elif friendly_ingredients:
                        # Custom result string for friendly ingredients
                        if field in ['Vegan', 'Vegetarian', 'Lactose', 'Kosher', 'Halal']:
                            results_by_field[field] = f"Scanned product is {field} because it contains {', '.join(friendly_ingredients)}."
                        elif field in ['Nuts', 'Gluten', 'Lactose']:
                            results_by_field[field] = f"Scanned product is {field}-free because it contains {', '.join(friendly_ingredients)}."
                        elif field in ['Diabetes' , 'HeartDisease']:
                            results_by_field[field] = f"Scanned product does not contribute to {field} because of {', '.join(friendly_ingredients)}."

                # Combine the results for MongoDB query and OCR
                result_from_ocr = " ".join(processed_list_tokens)

                # Dynamically generate the fields_to_check list based on your needs
                fields_to_check = ['Vegan', 'Nuts', 'Vegetarian', 'HeartDisease', 'Gluten', 'Diabetes', 'Lactose', 'Kosher', 'Halal']

                # Pass the valid list to the template
                return render_template('index.html', results_by_field=results_by_field, ocr_result=result_from_ocr, fields_to_check=fields_to_check)

        # Dynamically generate the fields_to_check list based on your needs
        fields_to_check = ['Vegan', 'Nuts', 'Vegetarian', 'HeartDisease', 'Gluten', 'Diabetes', 'Lactose', 'Kosher', 'Halal']

        # Pass the valid list to the template
        return render_template('index.html', results_by_field=None, ocr_result=None, fields_to_check=fields_to_check)
    return app
# ...

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)