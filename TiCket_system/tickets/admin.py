from django.contrib import admin
from .models import TicketType, Booking, BookedTicket

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available_quantity', 'is_active')
    list_editable = ('price', 'available_quantity', 'is_active')

class BookedTicketInline(admin.TabularInline):
    model = BookedTicket
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'customer_name', 'customer_email', 'booking_time', 'is_paid', 'transaction_id')
    list_filter = ('is_paid', 'booking_time')
    search_fields = ('customer_name', 'customer_email', 'unique_id', 'transaction_id')
    inlines = [BookedTicketInline]
    readonly_fields = ('unique_id', 'booking_time', 'transaction_id') # These should not be editable manually