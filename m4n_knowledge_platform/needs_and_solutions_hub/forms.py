from django import forms


def make_question_form(question):
    """
    Dynamically create a Form class for a single Question.
    Each call returns a *new* class with a unique name.
    """
    choices = [
        (str(option.pk), option.text)
        for option in question.options.all()
    ]

    fields = {
        "answer": forms.ChoiceField(
            label=question.text,
            choices=choices,
            widget=forms.RadioSelect,
            error_messages={"required": "Please select an option to continue."},
        ),
        "question_id": forms.IntegerField(
            widget=forms.HiddenInput,
            initial=question.pk,
        ),
    }

    return type(
        f"QuestionForm_{question.pk}",
        (forms.Form,),
        fields,
    )
