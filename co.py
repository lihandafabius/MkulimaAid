@m.route('/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    image_filename = None
    prediction = None
    trending_diseases = Diseases.query.filter_by(is_trending=True).all()

    if form.validate_on_submit():
        if form.image.data and allowed_file(form.image.data.filename):
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)

            # Save uploaded image to the uploads folder
            form.image.data.save(file_path)

            try:
                # Open the uploaded image and convert it to RGB
                image = Image.open(file_path).convert("RGB")

                # Prepare the image for the model
                inputs = Config.disease_processor(images=image, return_tensors="pt")

                # Make prediction using the model
                with torch.no_grad():
                    outputs = Config.disease_model(**inputs)

                # Get the predicted class index
                predicted_label_idx = torch.argmax(outputs.logits, dim=-1).item()

                # Map the predicted class index to its corresponding label
                predicted_class = Config.disease_model.config.id2label[predicted_label_idx]
                prediction = predicted_class

                # Save the image filename for display
                image_filename = filename

            except Exception as e:
                flash(f"Error processing the image: {e}", 'danger')
        else:
            flash("Invalid file type. Please upload a valid image (jpg, jpeg, png, jfif).", 'warning')

    return render_template('home.html', form=form, image_filename=image_filename, prediction=prediction, diseases=trending_diseases)