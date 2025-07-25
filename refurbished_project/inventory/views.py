from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db.models import Count
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from .models import Phone, Listing, Platform, Brand, Query, Order, Review
from .forms import ReviewForm
from django.contrib.auth.decorators import user_passes_test, login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def is_staff(user):
    return user.is_staff

@method_decorator(user_passes_test(is_staff), name='dispatch')
class BrandCreateView(CreateView):
    model = Brand
    template_name = 'inventory/add_brand.html'
    fields = ['name', 'logo']
    success_url = reverse_lazy('home')

class BrandDetailView(DetailView):
    model = Brand
    template_name = 'inventory/brand_detail.html'
    context_object_name = 'brand'

class FeatureView(TemplateView):
    template_name = 'inventory/features.html'

class HomeView(TemplateView):
    template_name = 'inventory/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.annotate(phone_count=Count('phone'))
        return context

class PhoneListView(ListView):
    model = Phone
    template_name = 'inventory/phone_list.html'
    context_object_name = 'phones'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        memory = self.request.GET.get('memory')
        if memory:
            queryset = queryset.filter(memory=memory)
            
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
            
        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
            
        condition = self.request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
            
        color = self.request.GET.get('color')
        if color:
            queryset = queryset.filter(color__icontains=color)
            
        return queryset

class PhoneDetailView(DetailView):
    model = Phone
    template_name = 'inventory/phone_details.html'
    context_object_name = 'phone'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all().order_by('-created_at')
        context['review_form'] = ReviewForm()
        # Get related products (other phones from the same brand)
        context['related_phones'] = Phone.objects.filter(brand=self.object.brand).exclude(pk=self.object.pk)[:4]
        return context

@method_decorator(user_passes_test(is_staff), name='dispatch')
class PhoneCreateView(CreateView):
    model = Phone
    template_name = 'inventory/phone_form.html'
    fields = ['name', 'base_price', 'condition', 'stock', 'memory', 'image']

    def form_valid(self, form):
        form.instance.brand = get_object_or_404(Brand, pk=self.kwargs['brand_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('brand_detail', kwargs={'pk': self.kwargs['brand_pk']})

@method_decorator(user_passes_test(is_staff), name='dispatch')
class PhoneUpdateView(UpdateView):
    model = Phone
    template_name = 'inventory/phone_form.html'
    fields = ['name', 'base_price', 'condition', 'stock', 'memory', 'image']
    success_url = reverse_lazy('phone_list')

@method_decorator(user_passes_test(is_staff), name='dispatch')
class PhoneDeleteView(DeleteView):
    model = Phone
    template_name = 'inventory/phone_confirm_delete.html'
    success_url = reverse_lazy('phone_list')

def create_or_update_listing(request, phone_pk):
    phone = get_object_or_404(Phone, pk=phone_pk)
    platform_id = request.POST.get('platform')
    if platform_id:
        platform = get_object_or_404(Platform, pk=platform_id)
        listing, created = Listing.objects.get_or_create(phone=phone, platform=platform)
        
        listing.platform_price = listing.calculate_platform_price()
        listing.platform_condition_category = listing.map_condition_to_platform()
        listing.is_listed = True
        listing.save()
    return redirect('phone_detail', pk=phone_pk)

def delist_phone(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    phone_pk = listing.phone.pk
    listing.is_listed = False
    listing.save()
    return redirect('phone_detail', pk=phone_pk)

def create_order(request, phone_pk):
    phone = get_object_or_404(Phone, pk=phone_pk)
    if request.method == 'POST':
        order_type = request.POST.get('order_type')
        camera_quality = request.POST.get('camera_quality')
        color = request.POST.get('color')
        memory = request.POST.get('memory')

        if order_type == 'BUY':
            if phone.stock > 0:
                phone.stock -= 1
                phone.save()
                Order.objects.create(
                    phone=phone,
                    order_type='BUY',
                    quantity=1,
                    total_price=phone.base_price,
                    status='COMPLETED'
                )
        elif order_type == 'SELL':
            phone.stock += 1
            phone.save()
            Order.objects.create(
                phone=phone,
                order_type='SELL',
                quantity=1,
                total_price=phone.base_price, # Assuming sell price is base price for now
                status='COMPLETED'
            )
    return redirect('phone_detail', pk=phone_pk)

@csrf_exempt
@require_POST
def submit_query(request):
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if not all([name, email, message]):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        Query.objects.create(
            name=name,
            email=email,
            message=message
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@method_decorator(user_passes_test(is_staff), name='dispatch')
class QueryListView(ListView):
    model = Query
    template_name = 'inventory/query_list.html'
    context_object_name = 'queries'
    ordering = ['-created_at']

@method_decorator(user_passes_test(is_staff), name='dispatch')
class QueryDeleteView(DeleteView):
    model = Query
    success_url = reverse_lazy('query_list')
    template_name = 'inventory/query_confirm_delete.html'

@require_POST
@login_required
def add_review(request, pk):
    phone = get_object_or_404(Phone, pk=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.phone = phone
        review.user = request.user
        review.save()
        return redirect('phone_detail', pk=pk)
    return redirect('phone_detail', pk=pk)

def sell_new_model(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_name = request.POST.get('phone_name')
        brand = request.POST.get('brand')
        condition = request.POST.get('condition')
        comments = request.POST.get('comments')

        message = f"New phone submission:\n\n" \
                  f"Phone Name: {phone_name}\n" \
                  f"Brand: {brand}\n" \
                  f"Condition: {condition}\n" \
                  f"Comments: {comments}"

        Query.objects.create(
            name=name,
            email=email,
            message=message
        )
        return redirect('home') # Or a 'thank you' page
    return render(request, 'inventory/sell_new_model.html')

@login_required
def add_to_cart(request, pk):
    phone = get_object_or_404(Phone, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, phone=phone)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'inventory/cart.html', {'cart': cart})

@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    cart_item.delete()
    return redirect('cart')
