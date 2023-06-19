from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,EmailField,TextAreaField,SubmitField
from wtforms.validators import InputRequired,NumberRange,EqualTo,Length,Email


class RegistorForm(FlaskForm):
    email=EmailField("Email",validators=[InputRequired(),Email()])
    password=PasswordField("Password",validators=[InputRequired(),Length(min=4,message="Password must be at least 4 characters long.")])
    confirm_password=PasswordField("Confirm Password",validators=[InputRequired(),EqualTo("password",message="Password do not match")])
    submit=SubmitField("Register")

class LoginForm(FlaskForm):
    email=EmailField("Email",validators=[InputRequired(),Email()])
    password=PasswordField("Password",validators=[InputRequired(),Length(min=4,message="Password must be at least 4 characters long.")])
    submit=SubmitField("Login")

class AddNote(FlaskForm):
    title=StringField("Title")
    content=TextAreaField("Content",validators=[InputRequired()])
    submit=SubmitField("Add Note")

class EditNote(FlaskForm):
    title=StringField("Title")
    content=TextAreaField("Content",validators=[InputRequired()])
    submit=SubmitField("Save")