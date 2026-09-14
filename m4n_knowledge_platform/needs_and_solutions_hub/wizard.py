from collections import Counter, OrderedDict, defaultdict

from django.db.models import Case, When, IntegerField
from django.shortcuts import render
from formtools.wizard.views import SessionWizardView
from taggit.models import TaggedItem

from ..knowledgeplatform.models import KnowledgeArticlePage, KnowledgeArticleTag

class QuestionWizard(SessionWizardView):

    template_name = "needs_and_solutions_hub/wizard_step.html"

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context["page"] = self.kwargs.get("wagtail_page")

        step_name = self.steps.current
        context["current_question"] = self.kwargs["question_map"].get(step_name)
        context["total_questions"] = self.steps.count

        previous = []
        question_map = self.kwargs["question_map"]
        for step_name in self.steps.all[:self.steps.index]:
            step_data = self.get_cleaned_data_for_step(step_name)
            if step_data:
                question = question_map[step_name]
                chosen_pk = step_data["answer"]
                option = question.options.get(pk=chosen_pk)
                previous.append({
                    "step_name": step_name,
                    "question": question,
                    "option": option,
                })
            context["previous_answers"] = previous
        return context

    def done(self, _form_list, form_dict, **_kwargs):
        question_map = self.kwargs["question_map"]
        answers = []

        for step_name, form in form_dict.items():
            question = question_map[step_name]
            chosen_option_pk = form.cleaned_data["answer"]

            option = question.options.get(pk=chosen_option_pk)
            answers.append({
                "step_name": step_name,
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
        from .models import OptionTag  # Avoid circular import

        options = [answer["option"] for answer in answers]
        if not options:
            return {"articles": KnowledgeArticlePage.objects.none(), "tags": set()}

        option_ids = [o.pk for o in options]

        option_tags_qs = OptionTag.objects.filter(
            content_object_id__in=option_ids,
        ).values_list("content_object_id", "tag_id")

        option_tag_ids = defaultdict(set)
        all_tag_ids = set()
        for option_id, tag_id in option_tags_qs:
            option_tag_ids[option_id].add(tag_id)
            all_tag_ids.add(tag_id)

        article_tags_qs = KnowledgeArticleTag.objects.filter(
            tag_id__in=all_tag_ids,
        ).values_list("tag_id", "content_object_id")

        tag_to_articles = defaultdict(set)
        for tag_id, article_id in article_tags_qs:
            tag_to_articles[tag_id].add(article_id)

        all_articles = Counter()
        for option in options:
            related_article_ids = set()
            for tag_id in option_tag_ids.get(option.pk, ()):
                related_article_ids |= tag_to_articles.get(tag_id, set())
            if related_article_ids:
                weight = 1 / len(related_article_ids)
                all_articles.update({aid: weight for aid in related_article_ids})

        all_tags = set(OptionTag._meta.get_field("tag").related_model.objects.filter(pk__in=all_tag_ids))

        if not all_articles:
            articles_qs = KnowledgeArticlePage.objects.none()
        else:
            ranked_ids = [aid for aid, _ in all_articles.most_common()]
            preserved_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(ranked_ids)],
                output_field=IntegerField(),
            )
            articles_qs = KnowledgeArticlePage.objects.filter(pk__in=ranked_ids).order_by(preserved_order)

        return {
            "articles": articles_qs,
            "tags": all_tags,
        }

    def render_next_step(self, form, **kwargs):
        """
        Override this to skip to the end if all questions are answered.
        This allows users to go back and change individual answers then
        skip straight back to the results page rather than paging through.
        """
        for step in self.steps.all[self.steps.index + 1:]:
            if not self.storage.get_step_data(step):
                return super().render_next_step(form, **kwargs)
            else:
                return self.render_done(form, **kwargs)

    def render_done(self, form, **kwargs):
        """
        This is copied and modified from the implementation in the superclass,
        in order to ensure we do NOT clear the wizard sstate in the session on
        completion of the wizard. This allows users to go back and modify their
        answers to change their results.
        """
        final_forms = OrderedDict()
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            if not form_obj.is_valid():
                return self.render_revalidation_failure(form_key, form_obj, **kwargs)
            final_forms[form_key] = form_obj

        done_response = self.done(list(final_forms.values()), form_dict=final_forms, **kwargs)
        # THIS IS WHERE STORAGE WOULD BE RESET IN THE ORIGINAL:
        # self.storage.reset()
        return done_response
