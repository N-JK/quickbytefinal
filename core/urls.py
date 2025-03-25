
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .utils import send_notification, mark_as_read, get_user_notifications




urlpatterns = [




    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),

    path('forget-password/', views.forget_password, name='forget_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),

    path('restaurant_reservations/', views.restaurant_reservations, name='restaurant_reservations'),


    path('customer_register/', views.customer_register, name='customer_register'),
    path('customer_home/', views.customer_home, name='customer_home'),
    path('bookings/', views.customer_bookings, name='customer_bookings'),
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('delete_visit/<int:visit_id>/', views.delete_visit, name='delete_visit'),
#ro
    path('edit_profile/', views.edit_profile, name='edit_profile'),
#ro
#customer
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('customer_profile/', views.customer_profile, name='customer_profile'),
    path('add_address/', views.add_address, name='add_address'),

#customer

   
  



    path('register_restaurant/', views.register_restaurant, name='register_restaurant'),
    path('register_delivery_personnel/', views.register_delivery_personnel, name='register_delivery_personnel'),
    path('restaurant_home/', views.restaurant_home, name='restaurant_home'),
    path('menu_view/', views.menu_view, name='menu_view'),
    path('category_management/', views.category_management, name='category_management'),

    path('edit_category/<int:pk>/', views.edit_category, name='edit_category'),
    path('menu_management/', views.menu_management, name='menu_management'),
    path('manage_food_item/<int:pk>/', views.manage_food_item, name='manage_food_item'),
    path('ingredient_management/', views.ingredient_management, name='ingredient_management'),
    path('edit_ingredient/<int:pk>/', views.edit_ingredient, name='edit_ingredient'),
    path('delivery_home/', views.delivery_home, name='delivery_home'),

    path('event_list/', views.event_list, name='event_list'),
    path('add_event/', views.add_event, name='add_event'),

    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:food_item_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),

    # path('add_to_cart/<int:food_item_id>/', views.add_to_cart, name='add_to_cart'),
    # path('view_cart/', views.view_cart, name='view_cart'),
    # path('remove-cart-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    # path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),


#############################################
    path('orders/<int:order_id>/', views.customer_order_detail, name='order_detail'),
    path('order/', views.my_orders, name='my_orders'),
    path('orders/', views.order_history, name='order_history'),
########################################################
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    # path('customer_orders/', views.customer_orders, name='customer_orders'),
    # path('my-orders/', views.customer_orders, name='customer_orders'),
    path('manage_orders/', views.manage_orders, name='manage_orders'),
    path('edit_event/<int:pk>/', views.edit_event, name='edit_event'),
    path('delete_event/<int:pk>/', views.delete_event, name='delete_event'),
    

    # urls.py


    path('toggle_favorite_restaurant/<int:restaurant_id>/', views.toggle_favorite_restaurant, name='toggle_favorite_restaurant'),
    path('toggle-favorite-food-item/<int:food_item_id>/', views.toggle_favorite_food_item, name='toggle_favorite_food_item'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('delivery/profile/', views.delivery_profile, name='delivery_profile'),
    path('restaurant/order-history/', views.restaurant_order_history, name='restaurant_order_history'),
    path('event/payment/<int:event_id>/', views.event_payment, name='event_payment'),





    path('delivery/home/', views.delivery_home, name='delivery_home'),
    path('delivery/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('delivery/accept-order/<int:order_id>/', views.accept_order, name='accept_order'),
    path('delivery/complete-delivery/<int:order_id>/', views.complete_delivery, name='complete_delivery'),
    path('delivery/accept/<int:order_id>/', views.accept_delivery, name='accept_delivery'),
    path('delivery/reject/<int:order_id>/', views.reject_delivery, name='reject_delivery'),
    path('delivery/update-status/<int:order_id>/', views.update_delivery_status, name='update_delivery_status'),
    path('delivery/password-reset/', views.password_reset, name='password_reset'),
    path('delivery/delete-account/', views.delete_account, name='delete_account'),

    path('restaurant/order/<int:order_id>/', views.restaurant_order_detail, name='restaurant_order_detail'),

    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    




    
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/clear-all/', 
         views.clear_all_notifications, 
         name='clear_all_notifications'),


    path('check-new-notifications/', views.check_new_notifications, name='check_new_notifications'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('check-notifications/', views.check_notifications, name='check_notifications'),

    
    # path('edit-review/<int:order_id>/', views.edit_review, name='edit_review'),
    # path('submit-review/<int:order_id>/', views.submit_review, name='submit_review'),
    path('submit-restaurant-review/<int:order_id>/', views.submit_restaurant_review, name='submit_restaurant_review'),
    path('submit-delivery-review/<int:order_id>/', views.submit_delivery_review, name='submit_delivery_review'),
    path('edit-restaurant-review/<int:order_id>/', views.edit_restaurant_review, name='edit_restaurant_review'),
    path('edit-delivery-review/<int:order_id>/', views.edit_delivery_review, name='edit_delivery_review'),
    path('restaurant/reviews/', views.restaurant_reviews, name='restaurant_reviews'),
    path('search/', views.search_results, name='search_results'),


    # URL for delivery personnel reviews
    path('delivery/reviews/', views.delivery_personnel_reviews, name='delivery_personnel_reviews'),

    path('logout/', views.logout_view, name='logout'),
    path('chatbot/', views.chatbot, name='chatbot'),

    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
         

    


]