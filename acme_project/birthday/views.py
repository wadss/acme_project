from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import BirthdayForm, CongratulationForm
from .utils import calculate_birthday_countdown
from .models import Birthday
from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy


def birthday(request, pk=None):
    if pk is not None:
        instance = get_object_or_404(Birthday, pk=pk)
    else:
        instance = None
    form = BirthdayForm(
        request.POST or None,
        files=request.FILES or None,
        instance=instance
        )
    context = {'form': form}
    if form.is_valid():
        form.save()
        birthday_countdown = calculate_birthday_countdown(
            form.cleaned_data['birthday']
        )
        context.update({'birthday_countdown': birthday_countdown})
    return render(request, 'birthday/birthday.html', context)


def birthday_list(request):
    birthdays = Birthday.objects.order_by('id')
    paginator = Paginator(birthdays, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'birthday/birthday_list.html', context)


def delete_birthday(request, pk):
    instance = get_object_or_404(Birthday, pk=pk)
    form = BirthdayForm(instance=instance)
    context = {'form': form}
    if request.method == 'POST':
        instance.delete()
        return redirect('birthday:list')
    return render(request, 'birthday/birthday.html', context)

###


class BirthdayListView(ListView):
    model = Birthday
    queryset = Birthday.objects.prefetch_related(
        'tags'
        ).select_related('author')
    ordering = 'id'
    paginate_by = 10


class BirthdayCreateView(LoginRequiredMixin, CreateView):
    model = Birthday
    form_class = BirthdayForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class BirthdayUpdateView(LoginRequiredMixin, UpdateView):
    model = Birthday
    form_class = BirthdayForm

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Birthday, pk=kwargs['pk'], author=request.user)
        return super().dispatch(request, *args, **kwargs)


class BirthdayDeleteView(LoginRequiredMixin, DeleteView):
    model = Birthday
    success_url = reverse_lazy('birthday:list')

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Birthday, pk=kwargs['pk'], author=request.user)
        return super().dispatch(request, *args, **kwargs)


class BirthdayDetailView(DetailView):
    model = Birthday

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['birthday_countdown'] = calculate_birthday_countdown(
            self.object.birthday
        )
        context['form'] = CongratulationForm()
        context['congratulations'] = (
            self.object.congratulations.select_related('author')
        )
        return context


@login_required
def simple_view(request):
    return HttpResponse('Страница для залогиненных пользователей!')


@login_required
def add_comment(request, pk):
    birthday = get_object_or_404(Birthday, pk=pk)
    form = CongratulationForm(request.POST)
    if form.is_valid():
        congratulation = form.save(commit=False)
        congratulation.author = request.user
        congratulation.birthday = birthday
        congratulation.save()
    return redirect('birthday:detail', pk=pk)