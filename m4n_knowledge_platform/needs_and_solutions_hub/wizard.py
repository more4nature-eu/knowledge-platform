from formtools.wizard.views import SessionWizardView
from django.shortcuts import render

class QuestionWizard(SessionWizardView):

    template_name = "needs_and_solutions_hub/wizard_step.html"

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context["page"] = self.kwargs.get("wagtail_page")

        step_name = self.steps.current
        context["current_question"] = self.kwargs["question_map"].get(step_name)
        context["total_questions"] = self.steps.count

        return context

    def done(self, form_list, form_dict, **kwargs):
        """
        Correlate each step's answer back to its Question object,
        then run your result logic.
        """
        question_map = self.kwargs["question_map"]
        answers = []

        for step_name, form in form_dict.items():
            question = question_map[step_name]
            chosen_option_pk = form.cleaned_data["answer"]

            option = question.options.get(pk=chosen_option_pk)
            answers.append({
                "question": question,
                "option": option,
            })

        result = self.compute_result(answers)

        return render(
            self.request,
            "needs_and_solutions_hub/wizard_result.html",
            {
                "page": self.kwargs.get("wagtail_page"),
                "answers": answers,
                "result": result,
            },
        )

    def compute_result(self, answers):
        return {
            "summary": f"You answered {len(answers)} question(s).",
            "answers": answers,
        }
