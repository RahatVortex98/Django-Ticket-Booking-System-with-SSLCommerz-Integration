document.addEventListener('DOMContentLoaded', function() {
    const ticketSelectionDiv = document.getElementById('ticketSelection');
    const bookingForm = document.getElementById('bookingForm');
    const totalAmountSpan = document.getElementById('totalAmount');
    let ticketTypesData = []; // To store fetched ticket types

    // Function to fetch ticket types from Django API
    async function fetchTicketTypes() {
        try {
            const response = await fetch('/api/ticket-types/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            ticketTypesData = data;
            renderTicketSelection();
        } catch (error) {
            console.error('Error fetching ticket types:', error);
            ticketSelectionDiv.innerHTML = '<div class="alert alert-danger">Error loading ticket types. Please try again later.</div>';
        }
    }

    // Function to render ticket selection fields
    function renderTicketSelection() {
        ticketSelectionDiv.innerHTML = ''; // Clear loading message
        if (ticketTypesData.length === 0) {
            ticketSelectionDiv.innerHTML = '<div class="alert alert-warning">No ticket types available at the moment.</div>';
            return;
        }

        ticketTypesData.forEach(ticket => {
            const ticketDiv = document.createElement('div');
            ticketDiv.classList.add('form-group', 'row', 'align-items-center', 'mb-2');
            ticketDiv.innerHTML = `
                <div class="col-md-4">
                    <label>${ticket.name} (BDT ${ticket.price})</label>
                </div>
                <div class="col-md-4">
                    <input type="number" class="form-control ticket-quantity"
                           data-ticket-id="${ticket.id}"
                           data-ticket-price="${ticket.price}"
                           data-available-quantity="${ticket.available_quantity}"
                           value="0" min="0" max="${ticket.available_quantity}">
                </div>
                <div class="col-md-4">
                    <small class="form-text text-muted">Available: ${ticket.available_quantity}</small>
                </div>
            `;
            ticketSelectionDiv.appendChild(ticketDiv);
        });

        // Add event listener for quantity changes
        document.querySelectorAll('.ticket-quantity').forEach(input => {
            input.addEventListener('change', calculateTotal);
            input.addEventListener('keyup', calculateTotal);
        });
        calculateTotal(); // Initial calculation
    }

    // Function to calculate total amount
    function calculateTotal() {
        let total = 0;
        document.querySelectorAll('.ticket-quantity').forEach(input => {
            const quantity = parseInt(input.value) || 0;
            const price = parseFloat(input.dataset.ticketPrice);
            total += (quantity * price);
        });
        totalAmountSpan.textContent = total.toFixed(2);
    }

    // Form Submission
    bookingForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const customerName = document.getElementById('customerName').value;
        const customerEmail = document.getElementById('customerEmail').value;
        const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;

        const bookedTickets = [];
        document.querySelectorAll('.ticket-quantity').forEach(input => {
            const quantity = parseInt(input.value) || 0;
            if (quantity > 0) {
                const ticketId = parseInt(input.dataset.ticketId);
                const availableQuantity = parseInt(input.dataset.availableQuantity);

                if (quantity > availableQuantity) {
                    alert(`You are trying to book ${quantity} tickets for ${ticketTypesData.find(t => t.id === ticketId).name}, but only ${availableQuantity} are available.`);
                    return; // Prevent form submission
                }

                bookedTickets.push({
                    ticket_type: ticketId,
                    quantity: quantity
                });
            }
        });

        if (bookedTickets.length === 0) {
            alert('Please select at least one ticket.');
            return;
        }

        const payload = {
            customer_name: customerName,
            customer_email: customerEmail,
            booked_tickets: bookedTickets
        };

        // Show loading state
        const submitButton = bookingForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = 'Processing...';

        try {
            const response = await fetch('/api/book-tickets/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                if (data.gateway_url) {
                    window.location.href = data.gateway_url; // Redirect to SSLCommerz
                } else {
                    alert('Booking created but no payment gateway URL found.');
                    console.error('No gateway URL:', data);
                }
            } else {
                console.error('Booking error:', data);
                let errorMessage = 'Failed to create booking.';
                if (data.error) {
                    errorMessage = data.error;
                } else if (data.customer_name) {
                    errorMessage += `\nName: ${data.customer_name[0]}`;
                } else if (data.customer_email) {
                    errorMessage += `\nEmail: ${data.customer_email[0]}`;
                }
                alert(errorMessage);
            }
        } catch (error) {
            console.error('Network or server error:', error);
            alert('An unexpected error occurred. Please try again.');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Proceed to Payment';
        }
    });

    // Initial fetch of ticket types
    fetchTicketTypes();
});