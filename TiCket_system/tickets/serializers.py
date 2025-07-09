from rest_framework import serializers
from .models import TicketType, Booking, BookedTicket

# tickets/serializers.py
from rest_framework import serializers
from .models import TicketType, Booking, BookedTicket

class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = ['id', 'name', 'price', 'available_quantity']

class BookedTicketSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    ticket_price = serializers.DecimalField(source='ticket_type.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = BookedTicket
        # Add 'subtotal' to read_only_fields
        fields = ['ticket_type', 'ticket_type_name', 'quantity', 'ticket_price', 'subtotal']
        read_only_fields = ['subtotal'] # <--- ADD THIS LINE
        extra_kwargs = {'ticket_type': {'write_only': True}}

class BookingSerializer(serializers.ModelSerializer):
    booked_tickets = BookedTicketSerializer(many=True)

    class Meta:
        model = Booking
        fields = ['unique_id', 'customer_name', 'customer_email', 'booked_tickets', 'is_paid', 'transaction_id']
        read_only_fields = ['unique_id', 'is_paid', 'transaction_id']

   
    def create(self, validated_data):
        booked_tickets_data = validated_data.pop('booked_tickets')
        booking = Booking.objects.create(**validated_data)

        for ticket_data in booked_tickets_data:
            ticket_type = ticket_data.pop('ticket_type')
            quantity = ticket_data.get('quantity', 1)

            # Validate available quantity
            if quantity > ticket_type.available_quantity:
                raise serializers.ValidationError({
                    'booked_tickets': [f"Only {ticket_type.available_quantity} tickets available for {ticket_type.name}."]
                })

            subtotal = ticket_type.price * quantity
            BookedTicket.objects.create(
                booking=booking,
                ticket_type=ticket_type,
                quantity=quantity,
                subtotal=subtotal
            )

        return booking
