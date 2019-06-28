from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,FileField

class EarthForm(FlaskForm):
    time = StringField(
        label="time",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "please input time！"
        }
    )
    latitude = StringField(
        label="litatude",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "please input litatude！"
        }
    )
    longitude = StringField(
        label="longitude",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "please input longitude！"
        }
    )
    depth = StringField(
        label="depth",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "please input depth！"
        }
    )
    mag = StringField(
        label="mag",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "please input mag！"
        }
    )
    rms = StringField(
        label="rms",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "please input rms！"
        }
    )
    place = StringField(
        label="place",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "please input place！"
        }
    )

    submit = SubmitField(
        'submit',
        render_kw={
            "class": "btn btn-primary",
        }
    )