from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

# Create your models here.


# class User(AbstractUser):
#     ROLE_CHOICES = (
#         ('customer', 'Customer'),
#         ('restaurant_owner', 'Restaurant Owner'),
#         ('delivery_personnel', 'Delivery Personnel')
#     )
    
#     fullname = models.CharField(max_length=255)
#     phone_number = models.CharField(max_length=15)
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
#     profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"{self.fullname} - {self.role}"



class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    role = models.CharField(max_length=20, default='Customer')
    phone_number = models.CharField(max_length=15)
    photograph = models.ImageField(upload_to='photographs/', null=True, blank=True)
    

    def __str__(self):
        return f"{self.user.username} - Customer"

class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}"
    

    
class Restaurant(models.Model):
    role = models.CharField(max_length=20, default='Restaurent_owner')
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='Restaurant')
    name = models.CharField(max_length=255)
    description = models.TextField()
    cuisine_type = models.CharField(max_length=100)
    street = models.CharField(max_length=255, default="street")
    city = models.CharField(max_length=100, default="city")
    state = models.CharField(max_length=100, default="state")
    postal_code = models.CharField(max_length=10, default="000000")
    country = models.CharField(max_length=100, default="country")
    phone_number = models.CharField(max_length=15)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    status_choices = (
        ('open', 'Open'),
        ('close', 'Close'),
        )
    status = models.CharField(max_length=5, choices=status_choices, default='open')
    profile_picture = models.ImageField(upload_to='restaurant_pics/')
    instagram_link = models.URLField(blank=True, null=True)
    twitter_link = models.URLField(blank=True, null=True)
    dining_capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=50)
    average_rating = models.FloatField(default=0.0)

    def update_average_rating(self):
        reviews = Review.objects.filter(restaurant=self)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
        else:
            self.average_rating = 0.0
        self.save()


    def __str__(self):
        return f"{self.name} - {self.role}"
    







class RestaurantVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visits')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='visits')
    visited_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-visited_at']

    def __str__(self):
        return f"{self.user.username} visited {self.restaurant.name}"

















class DeliveryPersonnel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='Delivery_personnel')
    role = models.CharField(max_length=20, default='Delivery_personnel')
    id_proof = models.ImageField(upload_to='id_proofs/')
    driving_license = models.CharField(max_length=50, unique=True)
    dob = models.DateField()
    vehicle_registration_certificate = models.CharField(max_length=50, unique=True, default="AXYKR7410852963")
    pan_card = models.CharField(max_length=10, unique=True)
    account_number = models.CharField(max_length=20, unique=True)
    ifsc_code = models.CharField(max_length=11)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)
    working_timings = models.CharField(max_length=255, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    photograph = models.ImageField(upload_to='photographs/', null=True, blank=True)
    average_rating = models.FloatField(default=0.0)

    def update_average_rating(self):
        reviews = Review.objects.filter(delivery_personnel=self)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
        else:
            self.average_rating = 0.0
        self.save()

    def delete_account(self, password):
        """Delete the delivery personnel account and associated user"""
        if self.user.check_password(password):
            # Delete associated files
            if self.id_proof:
                self.id_proof.delete()
            if self.photograph:
                self.photograph.delete()
            
            # Delete the user (this will cascade delete the delivery personnel)
            self.user.delete()
            return True
        return False

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('restaurant', 'name')

    def __str__(self):
        return self.name
    

class Ingredient(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('restaurant', 'name')

    def __str__(self):
        return self.name
    
    

class FoodItem(models.Model):
    FOOD_TYPE_CHOICES = (
        ('veg', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
        ('seasonal', 'Seasonal')
    )
    
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('out_of_stock', 'Out of Stock')
    )
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(Ingredient)
    image = models.ImageField(upload_to='food_pics/')
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    
    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"

class Event(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='event_pics/')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    is_promotional = models.BooleanField(default=False)
    promotion_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('payment_pending', 'Payment Pending'),
            ('payment_verification', 'Payment Verification'),
            ('promoted', 'Promoted')
        ],
        default='pending'
    )

    def send_promotional_notification(self):
        customers = Customer.objects.all()
        for customer in customers:
            Notification.objects.create(
                user=customer.user,
                title=f"New Event: {self.name}",
                message=f"Check out this new event at {self.restaurant.name}: {self.description}",
                notification_type='promotional',
                category='promotional',
                link=f'/restaurant/{self.restaurant.id}/#events'
            )

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"
    


class FavoriteRestaurant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_restaurants')
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'restaurant')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.restaurant.name}"

class FavoriteFoodItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_food_items')
    food_item = models.ForeignKey('FoodItem', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(default=timezone.now)  # Add default here

    class Meta:
        unique_together = ('user', 'food_item')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.food_item.name}"
    




class Reservation(models.Model):
   STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled')
    )
   restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reservation')
   name = models.CharField(max_length=255)
   email = models.EmailField()
   phone1 = models.CharField(max_length=15)
   phone2 = models.CharField(max_length=15, blank=True, null=True) 
   date = models.DateField()
   time = models.TimeField()
   number_of_persons = models.PositiveIntegerField(validators=[MinValueValidator(1)])
   status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

   def __str__(self):
       return f"Reservation for {self.name} on {self.date} at {self.time}"
   
    

   
   
    

class Cart(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ingredients = models.ManyToManyField(Ingredient)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.food_item.price * self.quantity
        super().save(*args, **kwargs)

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
        ('ready_for_pickup', 'Ready for Pickup')
    )
    DELIVERY_ACCEPTANCE_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    )
    delivery_acceptance = models.CharField(
        max_length=10,
        choices=DELIVERY_ACCEPTANCE_CHOICES,
        default='pending'
    )
    
    ORDER_TYPE_CHOICES = (
        ('pickup', 'Pickup'),
        ('delivery', 'Home Delivery')
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('prepaid', 'Prepaid'),
        ('cod', 'Cash on Delivery')
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid')
      #  ('failed', 'Failed'),
     #   ('refunded', 'Refunded')
    )
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    delivery_personnel = models.ForeignKey(DeliveryPersonnel, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.CharField(max_length=255, default="street")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='prepaid')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure that cash on delivery is only available for delivery orders
        if self.payment_method == 'cod' and self.order_type != 'delivery':
            raise ValidationError("Cash on Delivery is only available for delivery orders.")
        
        # Ensure that the status is valid for the order type
        if self.order_type == 'pickup' and self.status not in ['pending', 'preparing', 'ready_for_pickup', 'completed', 'canceled']:
            raise ValidationError("Invalid status for pickup orders.")
        if self.order_type == 'delivery' and self.status not in ['pending', 'preparing', 'out_for_delivery', 'delivered', 'completed', 'canceled']:
            raise ValidationError("Invalid status for delivery orders.")
        
        

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    ingredients = models.ManyToManyField(Ingredient)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    delivery_personnel = models.ForeignKey(DeliveryPersonnel, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return f"Review by {self.user.username} for {self.restaurant.name if self.restaurant else self.delivery_personnel.user.username}"

















#testing notification


# models.py
from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('new_order', 'New Order'),
        ('new_reservation', 'New Reservation'),
        ('order_canceled', 'Order Canceled'),
        
        # Customer notifications
        ('order_status', 'Order Status Update'),
        ('reservation_status', 'Reservation Status'),
        
        # Delivery personnel notifications
        ('new_delivery', 'New Delivery Assignment'),
        ('order_ready', 'Order Ready for Pickup'),
        ('delivery_canceled', 'Delivery Canceled'),
         ('promotional', 'Promotional Event')
    )
    CATEGORY_CHOICES = (
        ('order', 'Order Related'),
        ('promotional', 'Promotional'),
        ('other', 'Other')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)  # Optional link to relevant page

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"





class AdminPaymentDetails(models.Model):
    upi_id = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=255)
    promotion_price = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    
    class Meta:
        verbose_name = 'Admin Payment Detail'
        verbose_name_plural = 'Admin Payment Details'

    def __str__(self):
        return f"Admin Payment Details - {self.bank_name}"


class EventPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=255)
    payment_screenshot = models.ImageField(upload_to='payment_screenshots/')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for {self.event.name}"










   