from flask_wtf import FlaskForm
from wtforms import FileField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

class UploadForm(FlaskForm):
    image = FileField('Image', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'png', 'jpeg', 'jfif'], 'Images only!')
    ])
    model = SelectField('Model', choices=[
        ('pest', 'Pest Recognition'),
        ('disease', 'Disease Recognition')
    ], validators=[DataRequired()])
    submit = SubmitField('Predict')


