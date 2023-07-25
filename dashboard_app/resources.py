from import_export import resources
from .models import QuestionList


class QuestionListResource(resources.ModelResource):

    class Meta:
        model = QuestionList
        # import_id_fields = ['my_id']