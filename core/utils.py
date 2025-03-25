

from .models import Notification, DeliveryPersonnel
from django.shortcuts import get_object_or_404
from django.urls import reverse

def send_notification(user, title, message, notification_type, link=None):
    """Create and send a notification to a user."""
    try:
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
        return notification
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return None

def mark_as_read(notification_id):
    """Mark a notification as read."""
    try:
        notification = get_object_or_404(Notification, id=notification_id)
        notification.is_read = True
        notification.save()
        return True
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        return False

def get_user_notifications(user, unread_only=False):
    """Get notifications for a user."""
    notifications = Notification.objects.filter(user=user)
    if unread_only:
        notifications = notifications.filter(is_read=False)
    return notifications.order_by('-created_at')


    

def send_order_notification(order):
    """
    Send notification to restaurant when a new order is placed
    """
    try:
        restaurant = order.restaurant
        notification = Notification.objects.create(
            user=restaurant.owner,
            title="New Order Received",
            message=f"New order #{order.id} received from {order.customer.username}. "
                   f"Total amount: ${order.total_price}",
            notification_type='new_order',
            link=reverse('restaurant_order_detail', args=[order.id])  # Use reverse to generate correct URL
            
        )
        return notification
    except Exception as e:
        print(f"Error sending order notification: {str(e)}")
        return None


def send_order_status_notification(order):
    """
    Send notification to customer when order status changes
    """
    try:
        # Status-specific messages
        status_messages = {
            'preparing': {
                'title': "Order is Being Prepared",
                'message': f"Restaurant has started preparing your order #{order.id}."
            },
            'out_for_delivery': {
                'title': "Order Out for Delivery",
                'message': f"Your order with orderid {order.id} is on the way!"
            },
            'delivered': {
                'title': "Order Delivered",
                'message': f"Your order with orderid {order.id} has been delivered. Enjoy!"
            },
            'completed': {
                'title': "Order Completed",
                'message': f"Your order with orderid {order.id} has been completed. Thank you for ordering!"
            },
            'canceled': {
                'title': "Order Canceled",
                'message': f"Your order with orderid {order.id} has been canceled."
            },
            'ready_for_pickup': {
                'title': "Order Ready for Pickup",
                'message': f"Your order with orderid {order.id} is ready for pickup at {order.restaurant.name}!"
            }
        }

        # Get message details based on status
        status_info = status_messages.get(order.status, {
            'title': "Order Status Update",
            'message': f"Your order with orderid {order.id} status has been updated to {order.get_status_display()}"
        })

        # Generate the correct URL
        try:
            link = reverse('order_detail', args=[order.id])
            print(f"Generated link: {link}")  # Debug print
        except Exception as e:
            print(f"Error generating URL: {str(e)}")
            link = f'/home/orders/{order.id}/'  # Fallback URL

        # Create notification
        notification = Notification.objects.create(
            user=order.customer,
            title=status_info['title'],
            message=status_info['message'],
            notification_type='order_status',
            link=link
        )

        print(f"Notification created successfully: {notification.id}")  # Debug print
        return notification

    except Exception as e:
        print(f"Error sending order status notification: {str(e)}")
        return None





def notify_delivery_personnel_new_order(order):
    """Notify available delivery personnel about new delivery order"""
    try:
        if order.order_type == 'delivery':
            available_personnel = DeliveryPersonnel.objects.filter(is_available=True)
            for personnel in available_personnel:
                Notification.objects.create(
                    user=personnel.user,
                    title="New Delivery Order Available",
                    message=f"New order #{order.id} from {order.restaurant.name} is ready for pickup.",
                    notification_type='new_delivery',
                    link=reverse('delivery_home')
                )
            return True
        return None
    except Exception as e:
        print(f"Error notifying delivery personnel: {str(e)}")
        return None

def notify_delivery_completed(order):
    """Notify customer and restaurant when delivery is completed"""
    try:
        # Notify customer
        Notification.objects.create(
            user=order.customer,
            title="Order Delivered",
            message=f"Your order #{order.id} has been delivered.",
            notification_type='order_status',
            link=reverse('order_detail', args=[order.id])
        )

        # Notify restaurant
        Notification.objects.create(
            user=order.restaurant.owner,
            title="Order Delivered",
            message=f"Order #{order.id} has been delivered. Please mark as completed.",
            notification_type='order_status',
            link=reverse('restaurant_order_detail', args=[order.id])
        )
        return True
    except Exception as e:
        print(f"Error sending delivery completed notifications: {str(e)}")
        return False

    ######################################