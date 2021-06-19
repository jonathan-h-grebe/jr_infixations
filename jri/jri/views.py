from django.views import generic
from django.core.paginator import Paginator
from db_builder.models import Infixation, Checked_Vids
from django.http import HttpResponse

PAGINATE_NUMBER = 14

def add_field_to_inf(infixation):
    infixation.only_text_field = infixation.only_infixation()
    return infixation

class jriListView(generic.ListView):
    model = Infixation
    paginate_by = PAGINATE_NUMBER
    template_name = 'jri/all_jris.html'

    def get_queryset(self):
        infixations_modified = list(map(add_field_to_inf, Infixation.objects.all().order_by('-likes')))
        print(f'NUMBER IN QUERY : {str(len(infixations_modified))}')
        return infixations_modified

class checkedVideosListView(generic.ListView):
    model = Checked_Vids
    paginate_by = PAGINATE_NUMBER
    template_name = 'jri/all_checked_vids.html'

class singleInfixation(generic.DetailView):
    model = Infixation
    template_name='jri/one_infixation.html'

    def get_object(self, queryset=None):
        inf = super().get_object(queryset=queryset)
        return add_field_to_inf(inf)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inf = context['object']
        context['inf_vid_obj'] = Checked_Vids.objects.get(vid_id=inf.vid_id)
        return context