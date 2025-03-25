import json
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Sum, F, QuerySet
from .models import Notification, Restaurant, DeliveryPersonnel, Customer, Order, Cart, CartItem, FoodItem, Category, Event, Ingredient, RestaurantVisit, FavoriteRestaurant, FavoriteFoodItem, Reservation, Cart, OrderItem, Order, FoodItem, CartItem, Address, EventPayment, AdminPaymentDetails, Review
from .forms import CustomerRegistrationForm, RestaurantRegistrationForm, DeliveryPersonnelRegistrationForm, IngredientForm, ReservationForm, CustomerProfileForm, AddressForm, EventForm, EventPaymentForm
from datetime import datetime
from decimal import Decimal
from .forms import UserLoginForm
from .forms import FoodItemForm, CategoryForm, RestaurantProfileForm, EventForm, OrderForm, CartItemForm, DeliveryPersonnelProfileForm, PasswordResetForm, DeleteAccountForm
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .utils import send_notification, mark_as_read, get_user_notifications, send_order_notification, send_order_status_notification, notify_delivery_personnel_new_order, notify_delivery_completed
from django.urls import reverse, reverse_lazy

from . import models

  

# Login View
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(username=email, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Login successful!')

                # Determine the user's role and redirect accordingly
                if user and hasattr(user, 'Restaurant'):
                    return redirect('restaurant_home')
                elif user and hasattr(user, 'Delivery_personnel'):
                    return redirect('delivery_home')
                elif user and hasattr(user, 'customer'):
                    return redirect('customer_home')
                else:
                    print("debug-------------------------------------------------------------------------------------------")
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'core/login.html', {'form': form})



# Registration Views

def customer_register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            Customer.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                photograph=form.cleaned_data.get('photograph')
            )
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('customer_home')
        else:
            print(form.errors)  # Debugging: Print form errors
    else:
        form = CustomerRegistrationForm()
    return render(request, 'customer/register.html', {'form': form})



@login_required
def customer_home(request):
    # Start with all food items
    food_items = FoodItem.objects.all()
    
    # Get filter parameters
    food_type = request.GET.get('food_type')
    status = request.GET.get('status')
    price_range = request.GET.get('price_range')
    sort_by = request.GET.get('sort')
    
    # Apply filters
    if food_type:
        food_items = food_items.filter(food_type=food_type)
    
    if status:
        food_items = food_items.filter(status=status)
    
    if price_range:
        try:
            min_price, max_price = map(float, price_range.split('-'))
            food_items = food_items.filter(price__gte=min_price, price__lte=max_price)
        except (ValueError, AttributeError):
            pass
    
    # Apply sorting
    if sort_by:
        if sort_by == 'rating':
            food_items = food_items.order_by('-restaurant__average_rating')
        elif sort_by == 'cost_low_to_high':
            food_items = food_items.order_by('price')
        elif sort_by == 'cost_high_to_low':
            food_items = food_items.order_by('-price')
    
    # If no filters are applied, get latest item from each restaurant
    if not any([food_type, status, price_range, sort_by]):
        restaurants = Restaurant.objects.all()
        latest_items = []
        for restaurant in restaurants:
            latest_item = FoodItem.objects.filter(restaurant=restaurant).order_by('-id').first()
            if latest_item:
                latest_items.append(latest_item.id)
        food_items = FoodItem.objects.filter(id__in=latest_items)
    
    context = {
        'user': request.user,
        'latest_food_items': food_items,
        'filters': {
            'food_type': food_type,
            'status': status,
            'price_range': price_range,
        },
        'sort_by': sort_by,
    }
    return render(request, 'customer/home.html', context)





@login_required
def customer_bookings(request):
    # Get the current date and time
    now = timezone.now()

    # Fetch upcoming reservations for the logged-in user
    upcoming_reservations = Reservation.objects.filter(
        email=request.user.email,
        date__gt=now.date()
    ).order_by('date', 'time')

    # Fetch past reservations for the logged-in user
    past_reservations = Reservation.objects.filter(
        email=request.user.email,
        date__lte=now.date()
    ).order_by('-date', '-time')

    context = {
        'upcoming_reservations': upcoming_reservations,
        'past_reservations': past_reservations,
    }
    return render(request, 'customer/bookings.html', context)












@login_required
def customer_profile(request):
    customer = get_object_or_404(Customer, user=request.user)
    addresses = Address.objects.filter(customer=customer)
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            if form.has_changed():  # Check if any field has been changed
                form.save()
                messages.success(request, 'Profile updated successfully!')
            else:
                messages.info(request, 'No changes were made to your profile.')
            return redirect('customer_profile')
    else:
        form = CustomerProfileForm(instance=customer)

    context = {
        'form': form,
        'addresses': addresses,
        'customer': customer
    }
    return render(request, 'customer/profile.html', context)

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, customer=request.user.customer)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            if form.has_changed():
                form.save()
                messages.success(request, 'Address updated successfully!')
            else:
                messages.info(request, 'No changes were made to the address.')
            return redirect('customer_profile')
    else:
        form = AddressForm(instance=address)

    return render(request, 'customer/edit_address.html', {'form': form, 'address': address})

@login_required
def add_address(request):
    customer = get_object_or_404(Customer, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = customer
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('customer_profile')
    else:
        form = AddressForm()

    return render(request, 'customer/add_address.html', {'form': form})


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, customer=request.user.customer)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    return redirect('customer_profile')


########################################################################

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(customer=request.user)
    if request.method == 'POST':
        for item in cart.items.all():
            form = CartItemForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
        messages.success(request, "Cart updated successfully!")
        return redirect('view_cart')

    context = {
        'cart': cart,
    }
    return render(request, 'customer/view_cart.html', context)





@login_required
@require_POST
def update_cart_item(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))  # Convert to integer
        if quantity < 1:
            quantity = 1
        cart_item.quantity = quantity
        cart_item.save()

        # Update cart total
        cart = cart_item.cart
        cart.total = sum(item.total_price for item in cart.items.all())
        cart.save()

        return JsonResponse({
            'success': True,
            'item_total_price': float(cart_item.total_price),
            'cart_total': float(cart.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
        
    



@login_required
@require_POST
def remove_cart_item(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
        cart = cart_item.cart
        cart_item.delete()

        # Update cart total
        cart.total = sum(item.total_price for item in cart.items.all())
        cart.save()

        return JsonResponse({
            'success': True,
            'cart_total': float(cart.total)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    




@login_required
def add_to_cart(request, food_item_id):
    food_item = get_object_or_404(FoodItem, id=food_item_id)
    cart, created = Cart.objects.get_or_create(customer=request.user, restaurant=food_item.restaurant)

    # Check if the item is already in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, food_item=food_item)
    if not created:
        # If the item is already in the cart, increase the quantity
        cart_item.quantity += 1
    cart_item.save()

    # Update the cart total
    cart.total = sum(item.total_price for item in cart.items.all())
    cart.save()

    messages.success(request, f"{food_item.name} added to cart.")
    return redirect('view_cart')


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, customer=request.user)
    addresses = Address.objects.filter(customer=request.user.customer)

    if request.method == 'POST':
        
        # Get form data directly from POST
        selected_address_id = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        order_type = request.POST.get('order_type')

        # Basic validation
        if not selected_address_id or not payment_method:
            return JsonResponse({
                'status': 'error',
                'message': 'Please select both address and payment method'
            }, status=400)

        try:
            with transaction.atomic():
                # Create the order without form validation
                order = Order(
                    customer=request.user,
                    restaurant=cart.restaurant,
                    total_price=cart.total,
                    delivery_address=Address.objects.get(id=selected_address_id),
                    payment_method=payment_method,
                    order_type=order_type, 
                    status='pending',
                    payment_status='unpaid'
                )
                order.save()

                # Create order items
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        food_item=item.food_item,
                        quantity=item.quantity,
                        total_price=item.total_price
                    )

                # Clear the cart
                cart.items.all().delete()

                # Send notification to restaurant
                send_order_notification(order)

                # Store order ID in session for payment processing
                request.session['order_id'] = order.id

                # Return appropriate response
                if payment_method == 'prepaid':
                    return JsonResponse({
                        'status': 'success',
                        'redirect_url': reverse('payment_page', args=[order.id])
                    })
                else:
                    return JsonResponse({
                        'status': 'success',
                        'redirect_url': reverse('order_history')
                    })

        except Exception as e:
            import traceback
            print("Error processing order:", traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': f"Error processing your order: {str(e)}"
            }, status=400)

    # GET request handling
    context = {
        'cart': cart,
        'addresses': addresses,
        'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID,
        'order_type_choices': Order.ORDER_TYPE_CHOICES
    }
    return render(request, 'customer/checkout.html', context)




@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'customer/order_history.html', context)



@login_required
def my_orders(request):
    # Fetch all orders for the current user
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    # Define the statuses that allow reviews
    reviewable_statuses = ['completed', 'delivered']
    
    # Separate orders into active and history based on status
    active_orders = orders.exclude(status__in=reviewable_statuses)
    order_history = orders.filter(status__in=reviewable_statuses)
    
    # Get all reviews by the user
    reviews = Review.objects.filter(user=request.user)
    
    # Create a dictionary of order IDs that have reviews
    order_reviews = {}
    for review in reviews:
        if review.order_id not in order_reviews:
            order_reviews[review.order_id] = {'restaurant': False, 'delivery': False}
        
        if review.restaurant:
            order_reviews[review.order_id]['restaurant'] = True
        if review.delivery_personnel:
            order_reviews[review.order_id]['delivery'] = True
    
    context = {
        'active_orders': active_orders,
        'order_history': order_history,
        'reviewable_statuses': reviewable_statuses,
        'order_reviews': order_reviews,
        'active_tab': request.GET.get('tab', 'active'),
    }
    return render(request, 'customer/my_orders.html', context)











@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    if order.status != 'pending':
        messages.error(request, "Order cannot be canceled at this stage.")
        return redirect('my_orders')

    # No deduction if canceled while pending
    order.status = 'canceled'
    order.save()
    
    messages.success(request, "Order canceled.")
    return redirect('my_orders')




@login_required
def restaurant_detail(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    # Handle reservation form submission
    if request.method == 'POST':
            form = ReservationForm(request.POST, restaurant=restaurant)
            if form.is_valid():
                reservation = form.save(commit=False)
                number_of_persons = reservation.number_of_persons
                if number_of_persons > restaurant.dining_capacity:
                    messages.warning(request, f"Number of persons exceeds the dining capacity of {restaurant.dining_capacity}.")
                else:
                    reservation.restaurant = restaurant
                    reservation.save()
                    messages.success(request, 'Reservation made successfully!')
                    return redirect('restaurant_list')
    else:
        form = ReservationForm(restaurant=restaurant)

    # Update the visit timestamp or create a new visit
    visit, created = RestaurantVisit.objects.get_or_create(
        user=request.user, 
        restaurant=restaurant,
        defaults={'visited_at': timezone.now()}
    )
    if not created:
        visit.visited_at = timezone.now()
        visit.save()

    food_type_filter = request.GET.get('food_type')
    if food_type_filter:
        menu_items = FoodItem.objects.filter(restaurant=restaurant, food_type=food_type_filter)
    else:
        menu_items = FoodItem.objects.filter(restaurant=restaurant)
    
    events = Event.objects.filter(restaurant=restaurant)

    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'events': events,
        'food_type_filter': food_type_filter,
        'form': form,
        'opening_time': restaurant.opening_time.strftime('%H:%M'),
        'closing_time': restaurant.closing_time.strftime('%H:%M'),
    }
    return render(request, 'customer/restaurant_access.html', context)



@login_required
def restaurant_list(request):
    try:
        visits = RestaurantVisit.objects.filter(
            user=request.user
        ).select_related('restaurant').order_by('-visited_at')[:5]
        
        all_restaurants = Restaurant.objects.all().order_by('closing_time')
        
        # Get user's favorite restaurants
        favorite_restaurants = set(FavoriteRestaurant.objects.filter(
            user=request.user
        ).values_list('restaurant_id', flat=True))
        
        context = {
            'all_restaurants': all_restaurants,
            'visits': visits,
            'favorite_restaurants': favorite_restaurants,
        }
        return render(request, 'customer/restaurant_listing.html', context)
    
    except Exception as e:
        print(f"Error fetching restaurant list: {str(e)}")
        messages.error(request, "Error loading restaurants.")
        return render(request, 'customer/restaurant_listing.html', {
            'all_restaurants': [],
            'visits': [],
            'favorite_restaurants': set(),
        })

@login_required
def delete_visit(request, visit_id):
    try:
        visit = get_object_or_404(RestaurantVisit, id=visit_id, user=request.user)
        visit.delete()
        messages.success(request, 'Restaurant removed from recently visited.')
    except Exception as e:
        print(f"Error deleting visit: {str(e)}")
        messages.error(request, "Error removing restaurant from recently visited.")
    
    return redirect('restaurant_list')




###########################################################################################

@login_required
def manage_orders(request):
    """View for active/ongoing orders"""
    if not hasattr(request.user, 'Restaurant'):
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    restaurant = request.user.Restaurant
    
    # Get status filter from query parameters
    status_filter = request.GET.get('status', None)
    
    # Base queryset for all active orders
    base_orders = Order.objects.filter(
        restaurant=restaurant,
        status__in=['pending', 'preparing', 'out_for_delivery', 'delivered', 'ready_for_pickup']
    )

    # Apply status filter if specified
    if status_filter:
        orders = base_orders.filter(status=status_filter)
    else:
        orders = base_orders

    # Order by created_at
    orders = orders.order_by('-created_at')

    # Calculate counts for each status
    status_counts = {
        'all': base_orders.count(),  # Count of all active orders
        'pending': base_orders.filter(status='pending').count(),
        'preparing': base_orders.filter(status='preparing').count(),
        'out_for_delivery': base_orders.filter(status='out_for_delivery').count(),
        'delivered': base_orders.filter(status='delivered').count(),
        'ready_for_pickup': base_orders.filter(status='ready_for_pickup').count(),
    }

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id, restaurant=restaurant)

        # Update order status
        if new_status in ['pending', 'preparing', 'ready_for_pickup', 'completed']:
            # For delivery orders, check if it can be marked as completed
            if order.order_type == 'delivery' and new_status == 'completed':
                if order.status != 'delivered':
                    messages.error(request, "Delivery orders must be delivered before marking as completed.")
                    return redirect('manage_orders')
            
            order.status = new_status
            order.save()
            
            # Send notifications
            if new_status == 'preparing' and order.order_type == 'delivery':
                # Notify customer and delivery personnel
                customer_notification = send_order_status_notification(order)
                delivery_notification = notify_delivery_personnel_new_order(order)
                if customer_notification and delivery_notification:
                    messages.success(request, "Order status updated and all notifications sent.")
                else:
                    messages.warning(request, "Order status updated but some notifications failed.")
            else:
                # Just notify customer
                if send_order_status_notification(order):
                    messages.success(request, f"Order status updated to {new_status} and customer notified.")
                else:
                    messages.warning(request, f"Order status updated to {new_status} but notification failed.")
        else:
            messages.error(request, "Invalid status update.")

        return redirect('manage_orders')

    context = {
        'orders': orders,
        'status_counts': status_counts,
        'current_status': status_filter or 'all'
    }
    return render(request, 'restaurant/manage_orders.html', context)

############################################################################################


@login_required
def restaurant_order_history(request):
    """View for completed orders with filtering"""
    if not hasattr(request.user, 'Restaurant'):
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    restaurant = request.user.Restaurant
    
    # Get filter parameters
    date = request.GET.get('date')
    time = request.GET.get('time')
    order_type = request.GET.get('order_type')

    # Base queryset
    orders = Order.objects.filter(
        restaurant=restaurant,
        status='completed'
    )

    # Apply filters
    if date:
        orders = orders.filter(created_at__date=date)
    if time:
        orders = orders.filter(created_at__time__hour=time.split(':')[0])
    if order_type:
        orders = orders.filter(order_type=order_type)

    # Order by created_at
    orders = orders.order_by('-created_at')

    # Calculate total earnings
    total_earnings = orders.aggregate(total=Sum('total_price'))['total'] or 0

    context = {
        'orders': orders,
        'total_earnings': total_earnings,
        'date': date,
        'time': time,
        'order_type': order_type,
    }
    return render(request, 'restaurant/order_history.html', context)













@login_required
@require_POST
def toggle_favorite_restaurant(request, restaurant_id):
    try:
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        favorite = FavoriteRestaurant.objects.filter(
            user=request.user,
            restaurant=restaurant
        ).first()
        
        if favorite:
            favorite.delete()
            is_favorite = False
            message = f"{restaurant.name} removed from favorites"
        else:
            FavoriteRestaurant.objects.create(
                user=request.user,
                restaurant=restaurant
            )
            is_favorite = True
            message = f"{restaurant.name} added to favorites"
        
        return JsonResponse({
            'is_favorite': is_favorite,
            'message': message,
            'status': 'success'
        })
    except Exception as e:
        print(f"Error in toggle_favorite_restaurant: {str(e)}")  # For debugging
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=400)



@login_required
@require_POST
def toggle_favorite_food_item(request, food_item_id):
    try:
        food_item = get_object_or_404(FoodItem, id=food_item_id)
        favorite, created = FavoriteFoodItem.objects.get_or_create(
            user=request.user,
            food_item=food_item
        )
        
        if not created:
            favorite.delete()
            is_favorite = False
            message = f"{food_item.name} removed from favorites"
        else:
            is_favorite = True
            message = f"{food_item.name} added to favorites"
        
        return JsonResponse({
            'is_favorite': is_favorite,
            'message': message,
            'status': 'success'
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=400)
    

@login_required
def favorites_list(request):
    favorite_restaurants = FavoriteRestaurant.objects.filter(user=request.user)
    favorite_food_items = FavoriteFoodItem.objects.filter(user=request.user)
    
    context = {
        'favorite_restaurants': favorite_restaurants,
        'favorite_food_items': favorite_food_items,
    }
    return render(request, 'customer/favorites.html', context)











def register_restaurant(request):
    if request.method == 'POST':
        form = RestaurantRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            Restaurant.objects.create(
                owner=user,
                name=form.cleaned_data['restaurant_name'],
                description=form.cleaned_data['description'],
                cuisine_type=form.cleaned_data['cuisine_type'],
                street=form.cleaned_data['street'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                postal_code=form.cleaned_data['postal_code'],
                country=form.cleaned_data['country'],
                phone_number=form.cleaned_data['phone_number'],
                opening_time=form.cleaned_data['opening_time'],
                closing_time=form.cleaned_data['closing_time'],
                dining_capacity=form.cleaned_data['dining_capacity']
            )
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('restaurant_home')
        else:
            print(form.errors)  # Debugging: Print form errors
    else:
        form = RestaurantRegistrationForm()
    return render(request, 'restaurant/register.html', {'form': form})


@login_required
def restaurant_home(request):
    # You can add more context data as needed
    context = {
        'user': request.user,
    }
    return render(request, 'restaurant/home.html', context)


@login_required
def category_management(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    categories = Category.objects.filter(restaurant=restaurant)

    if request.method == 'POST':
        if 'add_category' in request.POST:
            category_form = CategoryForm(request.POST)
            if category_form.is_valid():
                category = category_form.save(commit=False)
                category.restaurant = restaurant
                try:
                    category.save()
                    messages.success(request, 'Category added successfully!')
                except IntegrityError:
                    messages.warning(request, 'Category with this name already exists.')
                return redirect('category_management')
        elif 'edit_category' in request.POST:
            category = get_object_or_404(Category, pk=request.POST.get('category_id'), restaurant=restaurant)
            category_form = CategoryForm(request.POST, instance=category)
            if category_form.is_valid():
                try:
                    category_form.save()
                    messages.success(request, 'Category updated successfully!')
                except IntegrityError:
                    messages.warning(request, 'Category with this name already exists.')
                return redirect('category_management')
        elif 'delete_category' in request.POST:
            category = get_object_or_404(Category, pk=request.POST.get('category_id'), restaurant=restaurant)
            category.delete()
            messages.success(request, 'Category deleted successfully!')
            return redirect('category_management')
    else:
        category_form = CategoryForm()

    return render(request, 'restaurant/category_management.html', {
        'category_form': category_form,
        'categories': categories
    })




@login_required
def edit_category(request, pk):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    category = get_object_or_404(Category, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            # Check if changes are made
            if form.has_changed():
                try:
                    form.save()
                    messages.success(request, 'Category updated successfully!')
                except IntegrityError:
                    messages.warning(request, 'Category with this name already exists.')
            else:
                messages.info(request, 'No changes to apply.')
            return redirect('category_management')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'restaurant/edit_category.html', {'form': form})




@login_required
def ingredient_management(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    ingredients = Ingredient.objects.filter(restaurant=restaurant)

    if request.method == 'POST':
        if 'add_ingredient' in request.POST:
            ingredient_form = IngredientForm(request.POST)
            if ingredient_form.is_valid():
                ingredient = ingredient_form.save(commit=False)
                ingredient.restaurant = restaurant
                try:
                    ingredient.save()
                    messages.success(request, 'Ingredient added successfully!')
                except IntegrityError:
                    messages.warning(request, 'Ingredient with this name already exists.')
                return redirect('ingredient_management')
        elif 'delete_ingredient' in request.POST:
            ingredient = get_object_or_404(Ingredient, pk=request.POST.get('ingredient_id'), restaurant=restaurant)
            ingredient.delete()
            messages.success(request, 'Ingredient deleted successfully!')
            return redirect('ingredient_management')
    else:
        ingredient_form = IngredientForm()

    return render(request, 'restaurant/ingredient_management.html', {
        'ingredient_form': ingredient_form,
        'ingredients': ingredients
    })



@login_required
def edit_ingredient(request, pk):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    ingredient = get_object_or_404(Ingredient, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            # Check if changes are made
            if form.has_changed():
                try:
                    form.save()
                    messages.success(request, 'Ingredient updated successfully!')
                except IntegrityError:
                    messages.warning(request, 'Ingredient with this name already exists.')
            else:
                messages.info(request, 'No changes to apply.')
            return redirect('ingredient_management')
    else:
        form = IngredientForm(instance=ingredient)

    return render(request, 'restaurant/edit_ingredient.html', {'form': form})




@login_required
def menu_view(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    menu_items = FoodItem.objects.filter(restaurant=restaurant)

    if request.method == 'POST':
        if 'delete' in request.POST:
            food_item = get_object_or_404(FoodItem, pk=request.POST.get('food_item_id'), restaurant=restaurant)
            food_item.delete()
            messages.success(request, 'Food item deleted successfully!')
            return redirect('menu_view')

    return render(request, 'restaurant/menu.html', {
        'menu_items': menu_items
    })



@login_required
def manage_food_item(request, pk):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    food_item = get_object_or_404(FoodItem, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        if 'edit' in request.POST:
            form = FoodItemForm(request.POST, request.FILES, instance=food_item)
            if form.is_valid():
                form.save()
                messages.success(request, 'Food item updated successfully!')
                return redirect('menu_view')
        elif 'delete' in request.POST:
            food_item.delete()
            messages.success(request, 'Food item deleted successfully!')
            return redirect('menu_view')
    else:
        form = FoodItemForm(instance=food_item)

    return render(request, 'restaurant/manage_food_item.html', {'form': form, 'food_item': food_item})




@login_required
def menu_management(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    menu_items = FoodItem.objects.filter(restaurant=restaurant)

    if request.method == 'POST':
        food_form = FoodItemForm(request.POST, request.FILES, restaurant=restaurant)
        if 'add_food' in request.POST and food_form.is_valid():
            food_item = food_form.save(commit=False)
            food_item.restaurant = restaurant
            food_item.save()
            food_form.save_m2m()
            messages.success(request, 'Food item added successfully!')
            return redirect('menu_view')
    else:
        food_form = FoodItemForm(restaurant=restaurant)

    return render(request, 'restaurant/menu_management.html', {
        'food_form': food_form,
        'menu_items': menu_items
    })


@login_required
def edit_profile(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    if request.method == 'POST':
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('edit_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RestaurantProfileForm(instance=restaurant)

    return render(request, 'restaurant/edit_profile.html', {'form': form, 'restaurant': restaurant})



@login_required
def event_list(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    events = Event.objects.filter(restaurant=restaurant)
    return render(request, 'restaurant/event_list.html', {'events': events})


@login_required
def add_event(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    admin_payment = AdminPaymentDetails.objects.first()  # Get admin payment details

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                event = form.save(commit=False)
                event.restaurant = restaurant

                # Check which submit button was clicked
                if 'create_and_notify' in request.POST:
                    # If promotional event
                    if not admin_payment:
                        messages.error(request, 'Promotional event creation is temporarily unavailable.')
                        return redirect('event_list')
                    
                    event.is_promotional = True
                    event.promotion_status = 'payment_pending'
                    event.save()
                    
                    messages.info(request, 'Please complete the payment to promote your event.')
                    return redirect('event_payment', event_id=event.id)
                else:
                    # Regular event creation
                    event.save()
                    messages.success(request, 'Event added successfully!')
                    return redirect('event_list')

            except Exception as e:
                messages.error(request, f'Error creating event: {str(e)}')
                return render(request, 'restaurant/edit_event.html', {
                    'form': form,
                    'admin_payment': admin_payment
                })
    else:
        form = EventForm()

    return render(request, 'restaurant/edit_event.html', {
        'form': form,
        'admin_payment': admin_payment,
        'promotion_price': admin_payment.promotion_price if admin_payment else None
    })

@login_required
def edit_event(request, pk):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    event = get_object_or_404(Event, pk=pk, restaurant=restaurant)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'restaurant/edit_event.html', {'form': form})

@login_required
def delete_event(request, pk):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    event = get_object_or_404(Event, pk=pk, restaurant=restaurant)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('event_list')
    return render(request, 'restaurant/delete_event.html', {'event': event})



@login_required
def restaurant_reservations(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)

    # Handle accept/reject actions
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        action = request.POST.get('action')
        reservation = get_object_or_404(Reservation, id=reservation_id, restaurant=restaurant)

        if action == 'accept':
            reservation.status = 'accepted'
            messages.success(request, f"Reservation for {reservation.name} has been accepted.")
        elif action == 'reject':
            reservation.status = 'rejected'
            messages.success(request, f"Reservation for {reservation.name} has been rejected.")
        
        reservation.save()
        return redirect('restaurant_reservations')

    # Fetch reservations for this restaurant
    reservations = Reservation.objects.filter(restaurant=restaurant).order_by('date', 'time')

    context = {
        'restaurant': restaurant,
        'reservations': reservations,
    }
    return render(request, 'restaurant/reservations.html', context)
   























def register_delivery_personnel(request):
    if request.method == 'POST':
        form = DeliveryPersonnelRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            DeliveryPersonnel.objects.create(
                user=user,
                id_proof=form.cleaned_data['id_proof'],
                driving_license=form.cleaned_data['driving_license'],
                dob=form.cleaned_data['dob'],
                vehicle_registration_certificate=form.cleaned_data['vehicle_registration_certificate'],
                pan_card=form.cleaned_data['pan_card'],
                account_number=form.cleaned_data['account_number'],
                ifsc_code=form.cleaned_data['ifsc_code'],
                photograph=form.cleaned_data.get('photograph')
            )
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('delivery_home')
        else:
            print(form.errors)  # Debugging: Print form errors
    else:
        form = DeliveryPersonnelRegistrationForm()
    return render(request, 'delivery/register.html', {'form': form})

@login_required
def delivery_home(request):
    try:
        delivery_personnel = request.user.Delivery_personnel
        
        # Get current deliveries (accepted orders that are either preparing or out_for_delivery)
        current_deliveries = Order.objects.filter(
            delivery_personnel=delivery_personnel,
            delivery_acceptance='accepted',
            status__in=['preparing', 'out_for_delivery']
        ).order_by('-created_at')

        # Get available orders (not yet accepted by any delivery personnel)
        available_orders = Order.objects.filter(
            delivery_personnel__isnull=True,
            order_type='delivery',
            status='preparing',
            delivery_acceptance='pending'
        ).order_by('-created_at')

        # Get completed deliveries
        completed_orders = Order.objects.filter(
            delivery_personnel=delivery_personnel,
            status__in=['delivered', 'completed']
        ).order_by('-created_at')[:5]

        # Calculate earnings
        today_earnings = Order.objects.filter(
            delivery_personnel=delivery_personnel,
            status='completed',
            created_at__date=timezone.now().date()
        ).aggregate(total=Sum('total_price'))['total'] or 0

        monthly_earnings = Order.objects.filter(
            delivery_personnel=delivery_personnel,
            status='completed',
            created_at__month=timezone.now().month
        ).aggregate(total=Sum('total_price'))['total'] or 0

        context = {
            'delivery_personnel': delivery_personnel,
            'current_deliveries': current_deliveries,
            'available_orders': available_orders,
            'completed_orders': completed_orders,
            'today_earnings': today_earnings,
            'monthly_earnings': monthly_earnings,
            'is_available': delivery_personnel.is_available,
        }
        return render(request, 'delivery/home.html', context)
    except DeliveryPersonnel.DoesNotExist:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    

@login_required
def toggle_availability(request):
    if request.method == 'POST':
        delivery_personnel = request.user.Delivery_personnel
        delivery_personnel.is_available = not delivery_personnel.is_available
        delivery_personnel.save()
        status = 'available' if delivery_personnel.is_available else 'unavailable'
        messages.success(request, f'You are now {status} for deliveries.')
    return redirect('delivery_home')

@login_required
def accept_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, status='preparing')
        delivery_personnel = request.user.Delivery_personnel
        
        if delivery_personnel.is_available:
            order.delivery_personnel = delivery_personnel
            order.status = 'out_for_delivery'
            order.save()
            messages.success(request, f'You have accepted the order #{order.id}')
        else:
            messages.warning(request, 'You need to be available to accept orders.')
    return redirect('delivery_home')

@login_required
def complete_delivery(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, 
                                 id=order_id, 
                                 delivery_personnel=request.user.Delivery_personnel,
                                 status='out_for_delivery')
        order.status = 'delivered'
        order.save()
        messages.success(request, f'Order #{order.id} marked as delivered.')
    return redirect('delivery_home')





@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

def home(request):
    # Fetch the latest food item for each restaurant
    latest_food_items = []
    restaurants = Restaurant.objects.all()

    for restaurant in restaurants:
        latest_item = FoodItem.objects.filter(restaurant=restaurant).order_by('-id').first()
        if latest_item:
            latest_food_items.append(latest_item)

    context = {
        'latest_food_items': latest_food_items,
    }
    return render(request, 'home.html', context)




# views.py

@login_required
def delivery_profile(request):
    try:
        delivery_personnel = request.user.Delivery_personnel
        
        if request.method == 'POST':
            form = DeliveryPersonnelProfileForm(
                request.POST, 
                request.FILES, 
                instance=delivery_personnel
            )
            if form.is_valid():
                if form.has_changed():
                    form.save()
                    messages.success(request, 'Profile updated successfully!')
                else:
                    messages.info(request, 'No changes were made to your profile.')
                return redirect('delivery_profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = DeliveryPersonnelProfileForm(instance=delivery_personnel)

        # Get earnings information
        today_earnings = Order.objects.filter(
            delivery_personnel=delivery_personnel,
            status='completed',
            created_at__date=timezone.now().date()
        ).aggregate(total=Sum('total_price'))['total'] or 0

        monthly_earnings = Order.objects.filter(
            delivery_personnel=delivery_personnel,
            status='completed',
            created_at__month=timezone.now().month
        ).aggregate(total=Sum('total_price'))['total'] or 0

        # Get recent deliveries
        recent_deliveries = Order.objects.filter(
            delivery_personnel=delivery_personnel,
            status__in=['delivered', 'completed']
        ).order_by('-created_at')[:5]

        context = {
            'form': form,
            'delivery_personnel': delivery_personnel,
            'today_earnings': today_earnings,
            'monthly_earnings': monthly_earnings,
            'recent_deliveries': recent_deliveries,
            'is_available': delivery_personnel.is_available
        }
        
        return render(request, 'delivery/profile.html', context)
    
    except DeliveryPersonnel.DoesNotExist:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')









#testing notification



@login_required
def notification_list(request):
    """
    Universal notification view that handles notifications for all user types.
    """
    try:
        # Initialize variables
        notifications = None
        user_type = None
        template = None

        # Check if user is a restaurant owner by checking Restaurant model
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            notifications = Notification.objects.filter(
                user=request.user,
                notification_type__in=['new_order', 'new_reservation', 'order_canceled']
            ).order_by('-created_at')
            user_type = 'restaurant'
            template = 'restaurant/notification.html'

        # Check if user is a customer by checking Customer model
        except Restaurant.DoesNotExist:
            try:
                customer = Customer.objects.get(user=request.user)
                notifications = Notification.objects.filter(
                    user=request.user,
                    notification_type__in=['order_status', 'reservation_status']
                ).order_by('-created_at')
                user_type = 'customer'
                template = 'customer/notifications.html'

            # Check if user is a delivery personnel by checking DeliveryPersonnel model
            except Customer.DoesNotExist:
                try:
                    delivery_personnel = DeliveryPersonnel.objects.get(user=request.user)
                    notifications = Notification.objects.filter(
                        user=request.user,
                        notification_type__in=['new_delivery', 'order_ready', 'delivery_canceled']
                    ).order_by('-created_at')
                    user_type = 'delivery'
                    template = 'delivery/notifications.html'

                except DeliveryPersonnel.DoesNotExist:
                    messages.error(request, "User role not found.")
                    return redirect('home')

        if notifications is not None and template is not None:
            context = {
                'notifications': notifications,
                'user_type': user_type,
                'unread_count': notifications.filter(is_read=False).count(),
            }

            # Add role-specific context
            if user_type == 'restaurant':
                context['restaurant'] = restaurant
            elif user_type == 'customer':
                context['customer'] = customer
            elif user_type == 'delivery':
                context['delivery_personnel'] = delivery_personnel

            return render(request, template, context)
        else:
            messages.error(request, "Invalid user configuration.")
            return redirect('home')

    except Exception as e:
        print(f"Error in notification_list: {str(e)}")
        messages.error(request, "Error loading notifications. Please try again.")
        return redirect('home')

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    try:
        # Verify user role and get the notification
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        
        # Check if user has permission to mark this notification
        user_role = None
        if hasattr(request.user, 'Restaurant'):
            user_role = 'restaurant'
        elif hasattr(request.user, 'customer'):
            user_role = 'customer'
        elif hasattr(request.user, 'Delivery_personnel'):
            user_role = 'delivery'
            
        if not user_role:
            return JsonResponse({
                'success': False,
                'error': 'Invalid user role'
            }, status=403)

        # Mark notification as read
        if not notification.is_read:
            notification.is_read = True
            notification.save()

        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read.'
        })

    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notification not found'
        }, status=404)
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error processing request'
        }, status=500)

@login_required
def clear_all_notifications(request):
    """Clear all notifications for the current user."""
    try:
        # Verify user role
        user_role = None
        if hasattr(request.user, 'Restaurant'):
            user_role = 'restaurant'
        elif hasattr(request.user, 'customer'):
            user_role = 'customer'
        elif hasattr(request.user, 'Delivery_personnel'):
            user_role = 'delivery'

        if not user_role:
            messages.error(request, "Invalid user role.")
            return redirect('home')

        # Get unread notifications count
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        if unread_count == 0:
            messages.info(request, "No unread notifications.")
            return redirect('notification_list')

        # Mark all notifications as read
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        messages.success(request, f"{unread_count} notification(s) marked as read.")

    except Exception as e:
        print(f"Error clearing notifications: {str(e)}")
        messages.error(request, "Error clearing notifications. Please try again.")

    return redirect('notification_list')

























@login_required
def check_new_notifications(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        if hasattr(request.user, 'Restaurant'):
            # Get unread notifications
            notifications = Notification.objects.filter(
                user=request.user,
                is_read=False,
                notification_type='new_order'
            ).order_by('-created_at')

            latest_notification = None
            if notifications.exists():
                latest_notification = {
                    'title': notifications[0].title,
                    'message': notifications[0].message,
                }

            return JsonResponse({
                'new_notifications': notifications.exists(),
                'unread_count': notifications.count(),
                'latest_notification': latest_notification
            })

        return JsonResponse({'error': 'Invalid user type'}, status=403)

    except Exception as e:
        print(f"Error checking notifications: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)
    

###########################################################################################################




# views.py

@login_required
def update_order_status(request, order_id):
    """Update order status and notify customer"""
    try:
        # Verify restaurant owner
        if not hasattr(request.user, 'Restaurant'):
            messages.error(request, "Permission denied.")
            return redirect('home')

        restaurant = request.user.Restaurant
        order = get_object_or_404(Order, id=order_id, restaurant=restaurant)

        if request.method == 'POST':
            new_status = request.POST.get('status')
            
            # For delivery orders, 'completed' status can only be set after 'delivered'
            if order.order_type == 'delivery' and new_status == 'completed' and order.status != 'delivered':
                messages.error(request, "Order must be delivered before marking as completed.")
                return redirect('manage_orders')

            # Validate status based on order type
            valid_statuses = {
                'pickup': ['pending', 'preparing', 'ready_for_pickup', 'completed'],
                'delivery': ['pending', 'preparing', 'completed']
            }

            if new_status in valid_statuses[order.order_type]:
                order.status = new_status
                order.save()

                # Send customer notification
                customer_notification = send_order_status_notification(order)

                if new_status == 'preparing' and order.order_type == 'delivery':
                    # Also notify delivery personnel for delivery orders
                    delivery_notification = notify_delivery_personnel_new_order(order)
                    if customer_notification and delivery_notification:
                        messages.success(request, "Order status updated and all notifications sent.")
                    else:
                        messages.warning(request, "Order status updated but some notifications failed.")
                else:
                    messages.success(request, f"Order status updated to {new_status}.")
            else:
                messages.error(request, "Invalid status for this order type.")

        return redirect('manage_orders')

    except Exception as e:
        print(f"Error updating order status: {str(e)}")
        messages.error(request, "Error updating order status.")
        return redirect('manage_orders')
    
@login_required
def check_notifications(request):
    """Check for new notifications"""
    try:
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')

        return JsonResponse({
            'has_notifications': notifications.exists(),
            'count': notifications.count()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    ##########################################################################################


@login_required
def restaurant_order_detail(request, order_id):
    """View for restaurant owners to see order details"""
    try:
        # Ensure user is restaurant owner
        if not hasattr(request.user, 'Restaurant'):
            messages.error(request, "Permission denied.")
            return redirect('restaurant_home')

        restaurant = request.user.Restaurant
        order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
        order_items = OrderItem.objects.filter(order=order).select_related('food_item')

        # Mark related notifications as read
        Notification.objects.filter(
            user=request.user,
            notification_type='new_order',
            link__contains=str(order_id)
        ).update(is_read=True)

        context = {
            'order': order,
            'order_items': order_items,
            'customer': order.customer,
        }
        
        return render(request, 'restaurant/order_detail.html', context)

    except Exception as e:
        print(f"Error viewing order detail: {str(e)}")
        messages.error(request, "Error loading order details.")
        return redirect('')





        #customer


@login_required
def customer_order_detail(request, order_id):
    """View for customers to see their order details"""
    print(f"Accessing order detail view with order_id: {order_id}")  # Debug print
    try:
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        print(f"Found order: {order}")  # Debug print

        order_items = OrderItem.objects.filter(order=order).select_related('food_item')
        print(f"Found {order_items.count()} order items")  # Debug print

        # Mark related notifications as read
        notifications_updated = Notification.objects.filter(
            user=request.user,
            notification_type='order_status',
            link__contains=str(order_id)
        ).update(is_read=True)
        print(f"Updated {notifications_updated} notifications")  # Debug print

        # Determine if the customer can submit a review
        can_submit_review = order.status in ['completed', 'delivered'] and not Review.objects.filter(order=order).exists()

        context = {
            'order': order,
            'order_items': order_items,
            'can_submit_review': can_submit_review,
        }
        
        return render(request, 'customer/order_detail.html', context)

    except Exception as e:
        print(f"Error viewing order detail: {str(e)}")  # Debug print
        messages.error(request, "Error loading order details.")
        return redirect('customer_orders')
    

@login_required
def accept_delivery(request, order_id):
    """Accept a delivery order"""
    try:
        if not hasattr(request.user, 'Delivery_personnel'):
            messages.error(request, "Permission denied.")
            return redirect('home')

        delivery_personnel = request.user.Delivery_personnel
        order = get_object_or_404(
            Order,
            id=order_id,
            order_type='delivery',
            status='preparing',
            delivery_acceptance='pending'
        )

        if request.method == 'POST':
            if delivery_personnel.is_available:
                order.delivery_personnel = delivery_personnel
                order.delivery_acceptance = 'accepted'
                order.save()
                messages.success(request, f"Order #{order.id} accepted.")
            else:
                messages.error(request, "You need to be available to accept orders.")

        return redirect('delivery_home')
    except Exception as e:
        messages.error(request, "Error accepting delivery.")
        return redirect('delivery_home')

@login_required
def reject_delivery(request, order_id):
    """Reject a delivery order"""
    try:
        if not hasattr(request.user, 'Delivery_personnel'):
            messages.error(request, "Permission denied.")
            return redirect('home')

        order = get_object_or_404(
            Order,
            id=order_id,
            order_type='delivery',
            status='preparing',
            delivery_acceptance='pending'
        )

        if request.method == 'POST':
            order.delivery_acceptance = 'rejected'
            order.save()
            messages.success(request, f"Order #{order.id} rejected.")

        return redirect('delivery_home')
    except Exception as e:
        messages.error(request, "Error rejecting delivery.")
        return redirect('delivery_home')

@login_required
def update_delivery_status(request, order_id):
    """Update delivery status"""
    try:
        if not hasattr(request.user, 'Delivery_personnel'):
            messages.error(request, "Permission denied.")
            return redirect('home')

        delivery_personnel = request.user.Delivery_personnel
        order = get_object_or_404(
            Order,
            id=order_id,
            delivery_personnel=delivery_personnel,
            order_type='delivery',
            delivery_acceptance='accepted'
        )

        if request.method == 'POST':
            new_status = request.POST.get('status')
            if new_status in ['out_for_delivery', 'delivered']:
                order.status = new_status
                order.save()

                if new_status == 'delivered':
                    if notify_delivery_completed(order):
                        messages.success(request, "Order marked as delivered and notifications sent.")
                    else:
                        messages.warning(request, "Order marked as delivered but notifications failed.")
                else:
                    messages.success(request, "Delivery status updated.")
            else:
                messages.error(request, "Invalid status.")

        return redirect('delivery_home')
    except Exception as e:
        messages.error(request, "Error updating delivery status.")
        return redirect('delivery_home')
    


@login_required
def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.user, request.POST)
        if form.is_valid():
            # Set new password
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            
            # Log out user and redirect to login
            messages.success(request, 'Password updated successfully. Please log in with your new password.')
            logout(request)
            return redirect('login')
    else:
        form = PasswordResetForm(request.user)
    
    return render(request, 'delivery/password_reset.html', {'form': form})

@login_required
def delete_account(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            try:
                # Get delivery personnel instance
                delivery_personnel = request.user.Delivery_personnel
                
                # Delete account
                if delivery_personnel.delete_account(form.cleaned_data['password']):
                    messages.success(request, 'Your account has been deleted successfully.')
                    return redirect('home')
                else:
                    messages.error(request, 'Error deleting account. Please try again.')
            except Exception as e:
                messages.error(request, f'Error deleting account: {str(e)}')
    else:
        form = DeleteAccountForm(request.user)
    
    return render(request, 'delivery/delete_account.html', {'form': form})



@login_required
def event_payment(request, event_id):
    event = get_object_or_404(Event, 
                             id=event_id, 
                             restaurant__owner=request.user,
                             is_promotional=True)
    admin_payment = AdminPaymentDetails.objects.first()
    
    if request.method == 'POST':
        form = EventPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.event = event
            payment.amount = admin_payment.promotion_price
            payment.save()
            
            event.promotion_status = 'payment_verification'
            event.save()
            
            messages.success(request, 'Payment details submitted successfully! Waiting for admin verification.')
            return redirect('event_list')
    else:
        form = EventPaymentForm()
    
    context = {
        'event': event,
        'form': form,
        'admin_payment': admin_payment
    }
    return render(request, 'restaurant/event_payment.html', context)




from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()

def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            # Use the template from the core app's template directory
            message = render_to_string('core/forget_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist.')
            return redirect('forget_password')
    # Use the template from the core app's template directory
    return render(request, 'core/forget_password.html')

def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password == confirm_password:
                user.set_password(password)
                user.save()
                messages.success(request, 'Password reset successful. Please login with your new password.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('reset_password', uidb64=uidb64, token=token)
        # Use the template from the core app's template directory
        return render(request, 'core/reset_password.html', {'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, 'The reset link is invalid.')
        return redirect('forget_password')
    


@login_required
def restaurant_reviews(request):
    """View for restaurant owners to see their reviews"""
    try:
        restaurant = get_object_or_404(Restaurant, owner=request.user)
        reviews = Review.objects.filter(restaurant=restaurant).select_related(
            'order', 'user', 'order__customer'
        ).order_by('-created_at')

        context = {
            'restaurant': restaurant,
            'reviews': reviews,
            'average_rating': restaurant.average_rating
        }
        return render(request, 'restaurant/reviews.html', context)
    except Exception as e:
        print(f"Error viewing restaurant reviews: {str(e)}")
        messages.error(request, "Error loading reviews.")
        return redirect('restaurant_home')

@login_required
def delivery_personnel_reviews(request):
    """View for delivery personnel to see their reviews"""
    try:
        delivery_personnel = get_object_or_404(DeliveryPersonnel, user=request.user)
        reviews = Review.objects.filter(delivery_personnel=delivery_personnel).select_related(
            'order', 'user'
        ).order_by('-created_at')

        context = {
            'delivery_personnel': delivery_personnel,
            'reviews': reviews,
            'average_rating': delivery_personnel.average_rating
        }
        return render(request, 'delivery/reviews.html', context)
    except Exception as e:
        print(f"Error viewing delivery personnel reviews: {str(e)}")
        messages.error(request, "Error loading reviews.")
        return redirect('delivery_home')
    




@login_required
def submit_restaurant_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    if order.status not in ['completed', 'delivered']:
        messages.error(request, "You can only submit a review for completed orders.")
        return redirect('order_detail', order_id=order_id)

    if request.method == 'POST':
        restaurant_rating = float(request.POST.get('restaurant_rating', 0))
        restaurant_comment = request.POST.get('restaurant_comment', '')

        if restaurant_rating and restaurant_comment:
            restaurant_review, created = Review.objects.get_or_create(
                user=request.user,
                restaurant=order.restaurant,
                order=order,
                defaults={'rating': restaurant_rating, 'comment': restaurant_comment}
            )
            if not created:
                restaurant_review.rating = restaurant_rating
                restaurant_review.comment = restaurant_comment
                restaurant_review.save()
            order.restaurant.update_average_rating()

        messages.success(request, "Your restaurant review has been submitted successfully.")
        return redirect('order_detail', order_id=order_id)

    context = {
        'order': order,
    }
    return render(request, 'customer/submit_restaurant_review.html', context)

@login_required
def submit_delivery_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    if order.status not in ['completed', 'delivered']:
        messages.error(request, "You can only submit a review for completed orders.")
        return redirect('order_detail', order_id=order_id)

    if request.method == 'POST':
        delivery_rating = float(request.POST.get('delivery_rating', 0))
        delivery_comment = request.POST.get('delivery_comment', '')

        if delivery_rating and delivery_comment:
            delivery_review, created = Review.objects.get_or_create(
                user=request.user,
                delivery_personnel=order.delivery_personnel,
                order=order,
                defaults={'rating': delivery_rating, 'comment': delivery_comment}
            )
            if not created:
                delivery_review.rating = delivery_rating
                delivery_review.comment = delivery_comment
                delivery_review.save()
            order.delivery_personnel.update_average_rating()

        messages.success(request, "Your delivery review has been submitted successfully.")
        return redirect('order_detail', order_id=order_id)

    context = {
        'order': order,
    }
    return render(request, 'customer/submit_delivery_review.html', context)




################


@login_required
def edit_restaurant_review(request, order_id):
    """View for editing an existing restaurant review"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return_tab = request.GET.get('return_tab', 'history')
    
    try:
        review = Review.objects.get(
            order=order,
            user=request.user,
            restaurant=order.restaurant  # Explicitly filter by the restaurant
        )
    except Review.DoesNotExist:
        messages.error(request, "Restaurant review not found.")
        return redirect('my_orders')
    except Review.MultipleObjectsReturned:
        messages.error(request, "Multiple restaurant reviews found. Please contact support.")
        return redirect('my_orders')

    if request.method == 'POST':
        new_rating = float(request.POST.get('rating', 0))
        new_comment = request.POST.get('comment', '')

        if new_rating and new_comment:
            review.rating = new_rating
            review.comment = new_comment
            review.save()

            # Update restaurant's average rating
            review.restaurant.update_average_rating()

            messages.success(request, "Restaurant review updated successfully!")
            return redirect(f'/home/order/?tab={return_tab}')  # Use the return tab parameter
        else:
            messages.error(request, "Please provide both rating and comment.")

    context = {
        'order': order,
        'review': review,
        'return_tab': return_tab,
        'review_type': 'restaurant',
    }
    return render(request, 'customer/edit_restaurant_review.html', context)




@login_required
def edit_delivery_review(request, order_id):
    """View for editing an existing delivery review"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return_tab = request.GET.get('return_tab', 'history')
    
    try:
        review = Review.objects.get(
            order=order,
            user=request.user,
            delivery_personnel=order.delivery_personnel  # Explicitly filter by the delivery personnel
        )
    except Review.DoesNotExist:
        messages.error(request, "Delivery review not found.")
        return redirect('my_orders')
    except Review.MultipleObjectsReturned:
        messages.error(request, "Multiple delivery reviews found. Please contact support.")
        return redirect('my_orders')

    if request.method == 'POST':
        new_rating = float(request.POST.get('rating', 0))
        new_comment = request.POST.get('comment', '')

        if new_rating and new_comment:
            review.rating = new_rating
            review.comment = new_comment
            review.save()

            # Update delivery personnel's average rating
            review.delivery_personnel.update_average_rating()

            messages.success(request, "Delivery review updated successfully!")
            return redirect(f'/home/order/?tab={return_tab}')  # Use the return tab parameter
        else:
            messages.error(request, "Please provide both rating and comment.")

    context = {
        'order': order,
        'review': review,
        'return_tab': return_tab,
        'review_type': 'delivery',
    }
    return render(request, 'customer/edit_delivery_review.html', context)





########################################################################




# @login_required
# def submit_review(request, order_id):
#     order = get_object_or_404(Order, id=order_id, customer=request.user)
    
#     if order.status not in ['completed', 'delivered']:
#         messages.error(request, "You can only submit a review for completed orders.")
#         return redirect('order_detail', order_id=order_id)

#     if request.method == 'POST':
#         restaurant_rating = float(request.POST.get('restaurant_rating', 0))
#         restaurant_comment = request.POST.get('restaurant_comment', '')
        
#         if order.order_type == 'delivery' and order.delivery_personnel:
#             delivery_rating = float(request.POST.get('delivery_rating', 0))
#             delivery_comment = request.POST.get('delivery_comment', '')
            
#             if delivery_rating and delivery_comment:
#                 # Check if a delivery review already exists
#                 delivery_review, created = Review.objects.get_or_create(
#                     user=request.user,
#                     delivery_personnel=order.delivery_personnel,
#                     order=order,
#                     defaults={'rating': delivery_rating, 'comment': delivery_comment}
#                 )
#                 if not created:
#                     # Update existing review
#                     delivery_review.rating = delivery_rating
#                     delivery_review.comment = delivery_comment
#                     delivery_review.save()
#                 order.delivery_personnel.update_average_rating()
        
#         if restaurant_rating and restaurant_comment:
#             # Check if a restaurant review already exists
#             restaurant_review, created = Review.objects.get_or_create(
#                 user=request.user,
#                 restaurant=order.restaurant,
#                 order=order,
#                 defaults={'rating': restaurant_rating, 'comment': restaurant_comment}
#             )
#             if not created:
#                 # Update existing review
#                 restaurant_review.rating = restaurant_rating
#                 restaurant_review.comment = restaurant_comment
#                 restaurant_review.save()
#             order.restaurant.update_average_rating()

#         messages.success(request, "Your review has been submitted successfully.")
#         return redirect('order_detail', order_id=order_id)

#     context = {
#         'order': order,
#     }
#     return render(request, 'customer/submit_review.html', context)



# @login_required
# def edit_review(request, order_id):
#     """View for editing an existing review"""
#     order = get_object_or_404(Order, id=order_id, customer=request.user)
    
#     # Get the review type and return tab from query parameters
#     review_type = request.GET.get('type', 'restaurant')
#     return_tab = request.GET.get('return_tab', 'history')
    
#     try:
#         if review_type == 'restaurant':
#             review = Review.objects.get(
#                 order=order,
#                 user=request.user,
#                 restaurant=order.restaurant  # Explicitly filter by the restaurant
#             )
#         elif review_type == 'delivery':
#             review = Review.objects.get(
#                 order=order,
#                 user=request.user,
#                 delivery_personnel=order.delivery_personnel  # Explicitly filter by the delivery personnel
#             )
#         else:
#             messages.error(request, "Invalid review type.")
#             return redirect('my_orders')

#     except Review.DoesNotExist:
#         messages.error(request, "Review not found.")
#         return redirect('my_orders')
#     except Review.MultipleObjectsReturned:
#         messages.error(request, "Multiple reviews found. Please contact support.")
#         return redirect('my_orders')

#     if request.method == 'POST':
#         new_rating = float(request.POST.get('rating', 0))
#         new_comment = request.POST.get('comment', '')

#         if new_rating and new_comment:
#             review.rating = new_rating
#             review.comment = new_comment
#             review.save()

#             # Update average rating
#             if review.restaurant:
#                 review.restaurant.update_average_rating()
#             if review.delivery_personnel:
#                 review.delivery_personnel.update_average_rating()

#             messages.success(request, "Review updated successfully!")
#             return redirect(f'/home/order/?tab={return_tab}')  # Use the return tab parameter
#         else:
#             messages.error(request, "Please provide both rating and comment.")

#     context = {
#         'order': order,
#         'review': review,
#         'review_type': review_type,
#         'return_tab': return_tab
#     }
#     return render(request, 'customer/edit_review.html', context)




def search_results(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    food_type = request.GET.get('food_type', 'all')
    sort = request.GET.get('sort', 'relevance')
    status = request.GET.get('status', 'available')

    restaurants = Restaurant.objects.none()
    categories = Category.objects.none()
    food_items = FoodItem.objects.none()

    if query:
        if search_type in ['all', 'restaurant']:
            restaurants = Restaurant.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            ).distinct()

        if search_type in ['all', 'category']:
            categories = Category.objects.filter(name__icontains=query)

        if search_type in ['all', 'food']:
            food_items_query = Q(name__icontains=query) | Q(description__icontains=query)
            
            # Filter by food type
            if food_type != 'all':
                food_items_query &= Q(food_type=food_type)

            # Filter by status
            if status != 'all':
                food_items_query &= Q(status=status)

            food_items = FoodItem.objects.filter(food_items_query)

            # Apply sorting
            if sort == 'price_low':
                food_items = food_items.order_by('price')
            elif sort == 'price_high':
                food_items = food_items.order_by('-price')
            elif sort == 'name':
                food_items = food_items.order_by('name')

    context = {
        'query': query,
        'restaurants': restaurants,
        'categories': categories,
        'food_items': food_items,
        'search_type': search_type,
        'food_type': food_type,
        'sort': sort,
        'status': status,
    }

    return render(request, 'customer/search_results.html', context)




from .models import User, Customer, Restaurant, DeliveryPersonnel
from django.conf import settings  # Import settings


from groq import Groq

groq_client = Groq(
    api_key=settings.GROQ_API_KEY  # Get the API key from settings.py
)


def chatbot(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')

        # Get chat history from session
        chat_history = request.session.get('chat_history', [])
        # Add user input to chat history
        chat_history.append({"role": "user", "content": user_input})
        
        
        # Initialize user data string
        user_data_str = ""

        if request.user.is_authenticated:
          user = request.user
          try:
              customer = Customer.objects.get(user=user)
              mobile_number = customer.phone_number if customer.phone_number else "Not Available"
          except Customer.DoesNotExist:
              mobile_number = "Not Available"
          user_data_str += f"User details: username: {user.username}, email: {user.email}, mobile number: {mobile_number}. \n"
            
          try:
              delivery_personnel = DeliveryPersonnel.objects.get(user=user)
              user_data_str += f"Delivery personnel details: driving license: {delivery_personnel.driving_license}, vehicle registration certificate: {delivery_personnel.vehicle_registration_certificate}, account balance: {delivery_personnel.balance}. \n"
          except DeliveryPersonnel.DoesNotExist:
            user_data_str += "Delivery personnel details: Not registered as a delivery personnel. \n"

        else:
            user_data_str = "User not logged in. Please log in to access personalized data."


        INITIAL_PROMPT = f"""You are a helpful and friendly chatbot specifically designed to assist users with QuickBite, a food delivery app. 
        Quickbite provides online food delivery services in India. The app was developed in 2025 by Nibin John and headquartered in Kerala, India.
        You should focus on queries related to food delivery, foods, app features, or the company information. 
        If the user asks a general question outside these topics, respond with "I can't answer that." If the user asks for irrelevant questions respond "I cant answer that".
        If the user says hi or hello or introduces themselves, then greet them.
        For the first message, you should respond with "Welcome to QuickBite! How can I help you?". Remember previous interactions.
        give proper next line break after every sentence.
        dont give * in the response.
        
        {user_data_str}
        note that username is same as my name.
        and note that the  DeliveryPersonnel model is for - delivery personnel details
        and if the user is not registered as delivery personnel, then reply "Not registered as a delivery personnel"
        note that dont provide any ids in reponses like  delivery personnel id etc. but you can provide email id, username, mobile number etc.
        give these informations if the user asks it only.
        """
        # construct prompt
        messages=[
                {"role": "system", "content": INITIAL_PROMPT},
            ]
        messages.extend(chat_history)
        
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama3-70b-8192",
            )
            response = chat_completion.choices[0].message.content

            # Add line breaks to the response
            response_with_breaks = response.replace(". ", ".<br>")


            # Add bot's response to chat history
            chat_history.append({"role":"assistant", "content":response_with_breaks})

            # update session with new chat history
            request.session['chat_history'] = chat_history

        except Exception as e:
            response = f"Error during API call: {e}"

        return JsonResponse({'response': response_with_breaks})

    request.session['chat_history'] = []
    return render(request, 'customer/chatbot.html')






#payment
import logging

logger = logging.getLogger(__name__)

@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    # Redirect to order detail if payment is already completed
    if order.payment_status == 'paid':
        return redirect('order_detail', order_id=order_id)

    context = {
        'order': order,
        'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID
    }
    return render(request, 'customer/payment.html', context)



from django.http import JsonResponse
import razorpay
from django.conf import settings

@login_required
def initiate_payment(request):
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            order = get_object_or_404(Order, id=order_id, customer=request.user)

            if order.payment_status == 'paid':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment already completed'
                })

            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Create Razorpay order
            payment_data = {
                'amount': int(float(order.total_price) * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f'order_{order.id}',
                'payment_capture': 1
            }

            # Create Razorpay order
            razorpay_order = client.order.create(data=payment_data)

            # Save Razorpay order ID to our order
            order.razorpay_order_id = razorpay_order['id']
            order.save()

            # Return success response with order details
            return JsonResponse({
                'status': 'success',
                'order_id': razorpay_order['id'],
                'amount': payment_data['amount'],
                'currency': payment_data['currency']
            })

        except Exception as e:
            logger.error(f"Payment initialization error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to initialize payment. Please try again.'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })



from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
import razorpay
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        try:
            # Get payment details from POST data
            payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            # Validate required parameters
            if not all([payment_id, razorpay_order_id, signature]):
                logger.error("Missing payment parameters in callback")
                messages.error(request, 'Invalid payment response received')
                return redirect('payment_failed')

            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify signature
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': signature
            }

            try:
                # Verify the payment signature
                client.utility.verify_payment_signature(params_dict)
                
                # Get and update the order
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                
                # Update order details
                order.payment_id = payment_id
                order.payment_status = 'paid'
                
                # Set appropriate order status based on order type
                if order.order_type == 'pickup':
                    order.status = 'ready_for_pickup'
                else:
                    order.status = 'preparing'
                
                order.save()

                # Clear session data
                if 'order_id' in request.session:
                    del request.session['order_id']

                # Send confirmation email (optional)
                # send_payment_confirmation_email(order)

                messages.success(request, 'Payment successful! Your order is being processed.')
                return redirect('order_detail', order_id=order.id)

            except razorpay.errors.SignatureVerificationError as e:
                logger.error(f"Payment signature verification failed: {str(e)}")
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.payment_status = 'unpaid'
                order.save()
                messages.error(request, 'Payment verification failed. Please contact support.')
                return redirect('payment_failed')

            except Order.DoesNotExist:
                logger.error(f"Order not found for Razorpay ID: {razorpay_order_id}")
                messages.error(request, 'Invalid order reference. Please contact support.')
                return redirect('payment_failed')

        except Exception as e:
            logger.error(f"Error in payment callback: {str(e)}", exc_info=True)
            messages.error(request, 'Error processing your payment. Please contact support.')
            return redirect('payment_failed')

    # Handle non-POST requests
    messages.warning(request, 'Invalid request method')
    return redirect('order_history')


@login_required
def payment_failed(request):
    messages.error(request, 'Payment failed. Please try again or choose a different payment method.')
    return redirect('order_history')