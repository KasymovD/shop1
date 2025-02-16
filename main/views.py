from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404, redirect

from .forms import RecipeForm, ImageForm
from .models import *

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
# Create your views here.
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, DeleteView

from .permissions import UserHasPremissionMixin


def index(request):
    return render(request, 'index.html')

def blog(request):
    return render(request, 'blog.html')

def blog_single(request):
    return render(request, 'blog-single.html')

def cart(request):
    return render(request, 'cart.html')

def checkout(request):
    return render(request, 'checkout.html')

def contact_us(request):
    return render(request, 'contact-us.html')

def login(request):
    return render(request, 'login.html')

def product_detail(request, slug):
    category = Category.objects.get(slug=slug)
    recipes = Recipe.objects.filter(category_id=slug)
    return render(request, 'product-detail.html', locals())

def shop(request):
    return render(request, 'shop.html')


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    image = recipe.get_image
    images = recipe.images.exclude(id=image.id)
    return render(request, 'recipe-detail.html', locals())

def add_recipe(request):
    ImageFormSet = modelformset_factory(Image, form=ImageForm)
    if request.method == 'POST':
        recipe_form = RecipeForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
        if recipe_form.is_valid() and formset.is_valid():
            recipe = recipe_form.save(commit=False)
            recipe.user = request.user
            recipe.save()

            for form in formset.cleaned_data:
                image = form['image']
                Image.objects.create(image=image, recipe=recipe)

                return redirect(recipe.get_absolute_url())
    else:
        recipe_form = RecipeForm()
        formset = ImageFormSet(queryset=Image.objects.none())
    return render(request, 'add-recipe.html', locals())

class MainPageView(ListView):
    model = Recipe
    template_name = 'index.html'
    context_object_name = 'recipes'
    paginate_by = 2

    def get_template_names(self):
        template_name = super(MainPageView, self).get_template_names()
        search = self.request.GET.get('query')
        filter = self.request.GET.get('filter')
        if search:
            template_name = 'search.html'
        elif filter:
            template_name = 'new.html'
        return template_name

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(MainPageView, self).get_context_data()
        search = self.request.GET.get('query')
        filter = self.request.GET.get('filter')
        if search:
            context['recipes'] = Recipe.objects.filter(Q(title__icontains=search)|
                                                       Q(description__icontains=search))
        elif filter:
            start_date = timezone.now() - timedelta(days=1)
            context['recipes'] = Recipe.objects.filter(created__gte=start_date)
        else:
            context['recipes'] = Recipe.objects.all()
        return context


def category_detail(request, slug):
    category = Category.objects.get(slug=slug)
    recipes = Recipe.objects.filter(category_id=slug)
    return render(request, 'category-detail.html', locals())

class Category_detail_view(DetailView):
    model = Category
    template_name = 'category-detail.html'
    context_object_name = 'category'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.slug = kwargs.get('slug', None)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recipes'] = Recipe.objects.filter(category_id=self.slug)
        return context

# def recipe_detail(request, pk):
#     recipe = get_object_or_404(Recipe, pk=pk)
#     image = recipe.get_image
#     images = recipe.images.exclude(id=image.id)
#     return render(request,'recipe-detail.html', locals())

class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipe-detail.html'
    context_object_name = 'recipe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        image = self.get_object().get_image
        context['images'] = self.get_object().images.exclude(id=image.id)
        return context



@login_required(login_url='login')
def add_recipe(request):
    ImageFormSet = modelformset_factory(Image, form=ImageForm)
    if request.method == 'POST':
        recipe_form = RecipeForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
        if recipe_form.is_valid() and formset.is_valid():
            recipe = recipe_form.save(commit=False)
            recipe.user = request.user
            recipe.save()

            for form in formset.cleaned_data:
                image = form['image']
                Image.objects.create(image=image, recipe=recipe)

                return redirect(recipe.get_absolute_url())
    else:
        recipe_form = RecipeForm()
        formset = ImageFormSet(queryset=Image.objects.none())
    return render(request, 'add-recipe.html', locals())


def update_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.user == recipe.user:
        ImageFormSet = modelformset_factory(Image, form=ImageForm, max_num=5)
        recipe_form = RecipeForm(request.POST or None, instance=recipe)
        formset = ImageFormSet(request.POST or None, request.FILES or None, queryset=Image.objects.filter(recipe=recipe))
        if recipe_form.is_valid() and formset.is_valid():
            recipe = recipe_form.save()

            for form in formset:
                image = form.save(commit=False)
                image.recipe = recipe
                image.save()
            return redirect(recipe.get_absolute_url())
        return render(request, 'update-recipe.html', locals())
    else:
        return HttpResponse('<h1>Вы не можете удалить или изменять Рецепты....!!! </h1>')#'<br>'
                            # "<button><a href='{% url 'template/add-recipe' %}'>Добавить свой рецепт</a></button>")


# def delete_recipe(request, pk):
#     recipe = get_object_or_404(Recipe, pk=pk)
#     if request.method == 'POST':
#         recipe.delete()
#         messages.add_message(request, messages.SUCCESS, 'Successfully deleted')
#         return redirect('home')
#     return render(request, 'delete-recipe.html')




class DeleteRecipeView(UserHasPremissionMixin, DeleteView):
    model = Recipe
    template_name = 'delete-recipe.html'
    success_url = reverse_lazy('home')

    def delete(self, request, *args, **kwargs):

        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.add_message(request, messages.SUCCESS, 'Successfully deleted')
        return HttpResponseRedirect(success_url)






# 11
