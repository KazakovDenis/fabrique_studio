from django.shortcuts import redirect
from rest_framework import permissions, generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .generics import GetPatchAPIView
from .serializers import *


@api_view(['GET'])
def api_v1_root(request, format=None):
    """API endpoint корневой директории APIv1"""
    return Response({
        'admin': {
            'doc': reverse('api-v1-doc', request=request, format=format),
            'schemes': reverse('scheme-list', request=request, format=format),
            'participants': reverse('participant-list', request=request, format=format),
        },
        'participant': reverse('survey-list', request=request, format=format),
    })


class ParticipantAPIViewMixin:
    queryset = Participant.objects.all()


class ParticipantListAPIView(ParticipantAPIViewMixin, generics.ListAPIView):
    """API endpoint списка участников опроса"""
    serializer_class = ParticipantListSerializer
    permission_classes = [
        permissions.IsAdminUser
    ]


class ParticipantDetailAPIView(ParticipantAPIViewMixin, GetPatchAPIView):
    """API endpoint информации об участнике опроса"""
    serializer_class = ParticipantDetailSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]


class SchemeAPIViewMixin:
    queryset = Scheme.objects.all()
    permission_classes = [
        permissions.IsAdminUser
    ]

    def convert_request_data(self, request):
        """Преобразовать данные запроса в вид, пригодный для сериализации"""
        view_field = self.serializer_class.view_field
        # todo: не через _mutable
        if not isinstance(request.data, dict):
            request.data._mutable = True
        questions = request.data.pop(view_field, [])
        for q in questions:
            options = q.get('answer_options')
            if options:
                if not isinstance(options, list):
                    raise serializers.ValidationError('Options should be a list')
                q['answer_options'] = [{'text': opt} for opt in options]

        field = self.serializer_class.questions_field
        request.data[field] = [{'question': q} for q in questions]
        # todo: почему не пропускает без question?
        # request.data[field] = questions
        return request


class SchemeListAPIView(SchemeAPIViewMixin, generics.ListCreateAPIView):
    """API endpoint для просмотра и редактирования списка опросов"""
    serializer_class = SchemeListSerializer

    def create(self, request, *args, **kwargs):
        request = self.convert_request_data(request)
        return super().create(request, *args, **kwargs)


class SchemeDetailAPIView(SchemeAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    """API endpoint для просмотра и редактирования конкретного опроса"""
    serializer_class = SchemeSerializer

    def update(self, request, *args, **kwargs):
        request = self.convert_request_data(request)
        return super().update(request, *args, **kwargs)


class SurveyListAPIView(generics.ListAPIView):
    """API endpoint для просмотра списка опросов участником"""
    serializer_class = SurveyListSerializer

    def get_queryset(self):
        return Scheme.objects.filter(date_to__gte=date.today())


@api_view(['GET'])
def scheme_take(request, *, pk):
    """API endpoint для создания формы опроса"""
    participant_id = request.GET.get('participant_id')
    if participant_id:
        participant = Participant.objects.get(pk=participant_id)
    else:
        participant = Participant.objects.create()

    scheme = Scheme.objects.get(pk=pk)
    survey = Survey.objects.create(scheme=scheme, participant=participant)
    return redirect('survey-detail', pk=survey.id)


class SurveyDetailAPIView(GetPatchAPIView):
    """API endpoint для заполнения опроса участником"""
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer

    def update(self, request, *args, **kwargs):
        answers = []
        for answer_data in request.data.pop('answers'):
            try:
                answer = Answer.objects.select_for_update().get(id=answer_data['id'])
                answer.content = validate_answer(answer, answer_data['answer'])
                answers.append(answer)
            except ObjectDoesNotExist:
                return Response(
                    data={'id': 'No such answer: %s' % answer_data['id']},
                    status=status.HTTP_404_NOT_FOUND
                )

        Answer.objects.bulk_update(answers, fields=['content'])
        return super().update(request, *args, **kwargs)
