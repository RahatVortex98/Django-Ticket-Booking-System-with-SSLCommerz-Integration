from django.db import models
import uuid

class TicketType(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., Silver, Gold, Platinum
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    booking_time = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=200, blank=True, null=True) # From SSLCommerz

    def __str__(self):
        return f"Booking {self.unique_id} - {self.customer_name}"

class BookedTicket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booked_tickets')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.ticket_type.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.ticket_type.name} for Booking {self.booking.unique_id}"