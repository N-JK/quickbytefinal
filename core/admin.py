from django.contrib import admin

# Register your models here.

from .models import *


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'role')  # Customize this list as per your requirements

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Restaurant)
admin.site.register(Category)
admin.site.register(FoodItem)
admin.site.register(FavoriteFoodItem)
admin.site.register(FavoriteRestaurant)
admin.site.register(RestaurantVisit)
admin.site.register(DeliveryPersonnel)
admin.site.register(Order)
admin.site.register(OrderItem)






@admin.register(AdminPaymentDetails)
class AdminPaymentDetailsAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'account_holder_name', 'promotion_price']

@admin.register(EventPayment)
class EventPaymentAdmin(admin.ModelAdmin):
    list_display = ['event', 'transaction_id', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    actions = ['approve_payment', 'reject_payment']

    def approve_payment(self, request, queryset):
        for payment in queryset:
            payment.status = 'completed'
            payment.save()
            
            # Update event status and send notifications
            event = payment.event
            event.promotion_status = 'promoted'
            event.save()
            event.send_promotional_notification()
        
        self.message_user(request, f"Selected payments have been approved and notifications sent.")
    
    def reject_payment(self, request, queryset):
        queryset.update(status='failed')
        for payment in queryset:
            payment.event.promotion_status = 'pending'
            payment.event.save()
        
        self.message_user(request, f"Selected payments have been rejected.")

    approve_payment.short_description = "Approve selected payments and send notifications"
    reject_payment.short_description = "Reject selected payments"