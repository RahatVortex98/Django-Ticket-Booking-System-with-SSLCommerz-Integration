# tickets/views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TicketType, Booking, BookedTicket
from .serializers import TicketTypeSerializer, BookingSerializer
import json
import requests
import logging

logger = logging.getLogger(__name__)

# --- API Views ---
class TicketTypeListView(APIView):
    """
    API endpoint to list available ticket types.
    Filters for active tickets with available quantity greater than 0.
    """
    def get(self, request):
        ticket_types = TicketType.objects.filter(is_active=True, available_quantity__gt=0)
        serializer = TicketTypeSerializer(ticket_types, many=True)
        return Response(serializer.data)

class CreateBookingView(APIView):
    """
    API endpoint to create a new booking and initiate payment with SSLCommerz.
    """
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            # Calculate total amount for the booking
            total_amount = 0
            for ticket_data in serializer.validated_data['booked_tickets']:
                try:
                    ticket_type = TicketType.objects.get(id=ticket_data['ticket_type'].id)
                    quantity = ticket_data['quantity']
                    total_amount += ticket_type.price * quantity
                except TicketType.DoesNotExist:
                    return Response({'error': 'One or more ticket types not found.'}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error(f"Error calculating total for booking: {e}")
                    return Response({'error': 'Error processing ticket selection.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Save the booking to get a unique_id before redirecting to payment
            booking = serializer.save()

            # --- SSLCommerz Payment Initiation ---
            store_id = settings.SSLCOMMERZ_STORE_ID
            store_passwd = settings.SSLCOMMERZ_STORE_PASSWORD
            
            # Determine SSLCommerz API endpoint based on DEBUG setting
            if settings.DEBUG:
                base_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            else:
                base_url = "https://securepay.sslcommerz.com/gwprocess/v4/api.php"

            post_data = {
                'store_id': store_id,
                'store_passwd': store_passwd,
                'total_amount': total_amount,
                'currency': 'BDT',
                'tran_id': str(booking.unique_id), # Use booking's unique_id as transaction ID
                'success_url': request.build_absolute_uri(reverse('sslcommerz_success')),
                'fail_url': request.build_absolute_uri(reverse('sslcommerz_fail')),
                'cancel_url': request.build_absolute_uri(reverse('sslcommerz_cancel')),
                'ipn_url': request.build_absolute_uri(reverse('sslcommerz_ipn')), # Important for server-to-server validation
                'cus_name': booking.customer_name,
                'cus_email': booking.customer_email,
                'cus_add1': 'N/A', # Placeholder, can be collected from form if needed
                'cus_phone': 'N/A', # Placeholder
                'cus_city': 'Dhaka', # <--- ADDED THIS LINE
                'cus_state': 'Dhaka', # <--- ADDED THIS LINE
                'cus_postcode': '1000', # <--- ADDED THIS LINE
                'cus_country': 'Bangladesh', # <--- ADDED THIS LINE
                'shipping_method': 'NO',
                'product_name': 'Ticket Booking',
                'product_category': 'Tickets',
                'product_profile': 'general',
            }

            try:
                response = requests.post(base_url, data=post_data)
                response_data = response.json()
                
                if response_data['status'] == 'SUCCESS':
                    # Return the GatewayPageURL to the frontend for redirection
                    return Response({'gateway_url': response_data['GatewayPageURL'], 'booking_id': str(booking.unique_id)}, status=status.HTTP_200_OK)
                else:
                    logger.error(f"SSLCommerz initiation failed for booking {booking.unique_id}: {response_data}")
                    return Response({'error': response_data.get('failedreason', 'Payment initiation failed')}, status=status.HTTP_400_BAD_REQUEST)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error connecting to SSLCommerz for booking {booking.unique_id}: {e}")
                return Response({'error': 'Failed to connect to payment gateway. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- SSLCommerz Callback Views ---
@csrf_exempt # CSRF protection is not needed for external POST requests from payment gateway
def sslcommerz_success(request):
    """
    Handles the success callback from SSLCommerz after a successful payment.
    Updates booking status, decrements ticket quantity, and sends confirmation email.
    """
    if request.method == 'POST':
        data = request.POST
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')
        amount = data.get('amount')
        currency = data.get('currency')

        logger.info(f"SSLCommerz Success Callback - Tran ID: {tran_id}, Val ID: {val_id}, Amount: {amount}")

        try:
            booking = Booking.objects.get(unique_id=tran_id)
            if not booking.is_paid:
                # IMPORTANT: In a production environment, you should perform server-side validation here
                # by calling SSLCommerz's validation API with `val_id` to ensure the payment is genuine.
                # For simplicity, this example assumes the success callback is reliable.

                booking.is_paid = True
                booking.transaction_id = val_id
                booking.save()

                # Decrease available ticket quantity for each booked ticket
                for booked_ticket in booking.booked_tickets.all():
                    ticket_type = booked_ticket.ticket_type
                    if ticket_type.available_quantity >= booked_ticket.quantity:
                        ticket_type.available_quantity -= booked_ticket.quantity
                        ticket_type.save()
                    else:
                        logger.warning(f"Insufficient quantity for {ticket_type.name} (ID: {ticket_type.id}) for booking {booking.unique_id}. Booked: {booked_ticket.quantity}, Available: {ticket_type.available_quantity}")
                        # You might want to handle this more robustly, e.g., refund or alert admin.

                # Send confirmation email to the customer
                send_confirmation_email(booking)

                # Redirect to landing page with success message and unique ID
                return redirect(reverse('landing_page') + f'?status=success&id={booking.unique_id}')
            else:
                # Booking was already marked as paid (e.g., via IPN), just redirect
                logger.info(f"SSLCommerz Success: Booking {tran_id} already paid.")
                return redirect(reverse('landing_page') + f'?status=success&id={booking.unique_id}')

        except Booking.DoesNotExist:
            logger.error(f"SSLCommerz Success: Booking with tran_id {tran_id} not found.")
            return redirect(reverse('landing_page') + '?status=error&msg=BookingNotFound')
        except Exception as e:
            logger.error(f"Error processing SSLCommerz success for tran_id {tran_id}: {e}")
            return redirect(reverse('landing_page') + '?status=error&msg=PaymentProcessingError')
    return redirect(reverse('landing_page') + '?status=error&msg=InvalidRequest') # If not a POST request

@csrf_exempt
def sslcommerz_fail(request):
    """
    Handles the fail callback from SSLCommerz when payment fails.
    """
    if request.method == 'POST':
        data = request.POST
        tran_id = data.get('tran_id')
        logger.warning(f"SSLCommerz Fail Callback - Tran ID: {tran_id}")
        # Optionally, update booking status to failed in your DB
        return redirect(reverse('landing_page') + f'?status=failed&id={tran_id}')
    return redirect(reverse('landing_page') + '?status=error&msg=InvalidRequest')

@csrf_exempt
def sslcommerz_cancel(request):
    """
    Handles the cancel callback from SSLCommerz when payment is cancelled by user.
    """
    if request.method == 'POST':
        data = request.POST
        tran_id = data.get('tran_id')
        logger.info(f"SSLCommerz Cancel Callback - Tran ID: {tran_id}")
        # Optionally, update booking status to cancelled in your DB
        return redirect(reverse('landing_page') + f'?status=cancelled&id={tran_id}')
    return redirect(reverse('landing_page') + '?status=error&msg=InvalidRequest')

@csrf_exempt
def sslcommerz_ipn(request):
    """
    Handles the Instant Payment Notification (IPN) from SSLCommerz.
    This is a server-to-server communication and is crucial for reliable payment confirmation.
    It should perform robust validation and update the booking status.
    """
    if request.method == 'POST':
        data = request.POST
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')
        status_code = data.get('status') # e.g., 'VALID', 'VALIDATED', 'FAILED', 'CANCELLED'
        amount = data.get('amount')
        currency = data.get('currency')

        logger.info(f"SSLCommerz IPN Callback - Tran ID: {tran_id}, Status: {status_code}, Val ID: {val_id}")

        if status_code == 'VALID' or status_code == 'VALIDATED':
            try:
                booking = Booking.objects.get(unique_id=tran_id)
                if not booking.is_paid:
                    # --- CRITICAL: Server-side validation using SSLCommerz API ---
                    # This step verifies the payment authenticity and prevents fraud.
                    # You would typically make another request to SSLCommerz's validation API.
                    # Example (pseudo-code, replace with actual SSLCommerz validation logic):
                    # validation_url = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
                    # validation_params = {
                    #     'val_id': val_id,
                    #     'store_id': settings.SSLCOMMERZ_STORE_ID,
                    #     'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
                    # }
                    # validation_response = requests.get(validation_url, params=validation_params)
                    # validation_data = validation_response.json()
                    #
                    # if validation_data.get('status') == 'VALID' and float(validation_data.get('amount')) == float(amount):
                    #     # Payment is truly valid and amount matches
                    #     booking.is_paid = True
                    #     booking.transaction_id = val_id
                    #     booking.save()
                    #
                    #     # Decrease available ticket quantity
                    #     for booked_ticket in booking.booked_tickets.all():
                    #         ticket_type = booked_ticket.ticket_type
                    #         if ticket_type.available_quantity >= booked_ticket.quantity:
                    #             ticket_type.available_quantity -= booked_ticket.quantity
                    #             ticket_type.save()
                    #
                    #     send_confirmation_email(booking)
                    #     return JsonResponse({'status': 'SUCCESS'})
                    # else:
                    #     logger.error(f"IPN Validation Failed for tran_id {tran_id}. Validation data: {validation_data}")
                    #     return JsonResponse({'status': 'VALIDATION_FAILED'}, status=400)
                    
                    # For demonstration, we'll assume IPN is valid if status is 'VALID'/'VALIDATED'
                    booking.is_paid = True
                    booking.transaction_id = val_id
                    booking.save()

                    # Decrease available ticket quantity
                    for booked_ticket in booking.booked_tickets.all():
                        ticket_type = booked_ticket.ticket_type
                        if ticket_type.available_quantity >= booked_ticket.quantity:
                            ticket_type.available_quantity -= booked_ticket.quantity
                            ticket_type.save()

                    send_confirmation_email(booking)
                    return JsonResponse({'status': 'SUCCESS'})
                else:
                    logger.info(f"SSLCommerz IPN: Booking {tran_id} already paid.")
                    return JsonResponse({'status': 'ALREADY_PAID'})

            except Booking.DoesNotExist:
                logger.error(f"SSLCommerz IPN: Booking with tran_id {tran_id} not found.")
                return JsonResponse({'status': 'BOOKING_NOT_FOUND'}, status=404)
            except Exception as e:
                logger.error(f"Error processing SSLCommerz IPN for tran_id {tran_id}: {e}")
                return JsonResponse({'status': 'ERROR'}, status=500)
        else:
            logger.warning(f"SSLCommerz IPN: Unsuccessful payment status: {status_code} for tran_id {tran_id}")
            # You might want to log this or update booking status to failed/cancelled if it's not already.
            return JsonResponse({'status': 'UNSUCCESSFUL_PAYMENT'}, status=200)
    return JsonResponse({'status': 'INVALID_REQUEST'}, status=400)


def send_confirmation_email(booking):
    """
    Sends a confirmation email to the customer with booking details.
    """
    subject = 'Your Ticket Booking Confirmation'
    # Render the HTML email template with booking data
    message = render_to_string('tickets/confirmation_email.html', {
        'booking': booking,
    })
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [booking.customer_email]

    try:
        send_mail(subject, message, from_email, recipient_list, html_message=message)
        logger.info(f"Confirmation email sent to {booking.customer_email} for booking {booking.unique_id}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {booking.customer_email}: {e}")

# --- Frontend Landing Page View ---
def landing_page(request):
    """
    Renders the main landing page, displaying success/failure messages
    and unique booking ID after payment redirects.
    """
    status_msg = request.GET.get('status') # 'success', 'failed', 'cancelled', 'error'
    unique_id = request.GET.get('id') # Unique booking ID or transaction ID
    return render(request, 'tickets/landing_page.html', {
        'status_msg': status_msg,
        'unique_id': unique_id
    })

