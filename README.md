Django Ticket Booking System with SSLCommerz Integration




## Overview
This is a full-stack web application for booking event tickets, built with Django for the backend and HTML, CSS, JavaScript, and Bootstrap for the frontend. It features dynamic ticket selection, customer information collection, integration with the SSLCommerz payment gateway, and automated email confirmations.

## Features
* **Dynamic Landing Page:** Displays available ticket types fetched from the backend.
* **Ticket Booking Form:** Collects customer name, email, and allows selection of multiple ticket types and quantities.
* **Ticket Selection:** Supports Silver, Gold, Platinum ticket types (prices and quantities are editable by admin).
* **Form Submission & Payment Redirection:** Submits booking data to the backend and redirects to SSLCommerz for payment.
* **SSLCommerz Payment Gateway Integration:** Handles secure online payments.
* **Post-Payment Processing:**
    * Saves ticket data to the database upon successful payment.
    * Sends a confirmation email with booking details.
    * Generates and displays a unique booking ID to the user.
    * Redirects back to the landing page with success/failure messages.
* **Admin Panel:** Django's built-in admin interface for managing ticket types and viewing bookings.

## Technologies Used
* **Backend:**
    * Python 3.x
    * Django (Web Framework)
    * Django REST Framework (for API endpoints)
    * `requests` (for HTTP requests to SSLCommerz)
    * `python-dotenv` (for managing environment variables)
* **Frontend:**
    * HTML5
    * CSS3 (Custom styling)
    * Bootstrap 4.x (Responsive design)
    * JavaScript (ES6+) (for dynamic content and AJAX)
* **Database:** SQLite (default for development, easily configurable for PostgreSQL/MySQL)
* **Payment Gateway:** SSLCommerz

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```
*(Replace `your-username` and `your-repo-name` with your actual GitHub details)*

### 2. Create and Activate a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(You'll need to create `requirements.txt` first: `pip freeze > requirements.txt`)*

### 4. Configure Environment Variables
Create a file named `.env` in the **root directory** of your project (the same directory as `manage.py`). This file will store your sensitive credentials. **Do NOT commit this file to Git!**

```
# .env
SECRET_KEY='your_django_secret_key_from_settings_py'
SSLCOMMERZ_STORE_ID='YOUR_SSLCOMMERZ_STORE_ID'
SSLCOMMERZ_STORE_PASSWORD='YOUR_SSLCOMMERZ_STORE_PASSWORD'
EMAIL_HOST_USER='your_email@gmail.com'
EMAIL_HOST_PASSWORD='your_gmail_app_password' # Use App Password for Gmail with 2FA
DEFAULT_FROM_EMAIL='no-reply@yourdomain.com'
# DEBUG=True # Optional: can control DEBUG status from .env
```
* Replace placeholder values with your actual credentials.
* Ensure your `settings.py` is configured to read these variables using `os.environ.get()`.

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Django Superuser
This allows you to access the Django admin panel.
```bash
python manage.py createsuperuser
```
Follow the prompts to create your admin user.

### 7. Add Ticket Types via Admin Panel
* Start the development server: `python manage.py runserver`
* Go to `http://127.0.0.1:8000/admin/` in your browser.
* Log in with your superuser credentials.
* Navigate to "Tickets" -> "Ticket Types".
* Add "Silver", "Gold", "Platinum" (or any other types) with their respective prices and `available_quantity`. Ensure `is_active` is checked.

### 8. Run the Development Server
```bash
python manage.py runserver
```

Screenshots:
Front Page:

![1 Front page](https://github.com/user-attachments/assets/1201ab17-2e96-478c-b25f-18e5ae8cf577)

User Input Info:

![2 input front page](https://github.com/user-attachments/assets/6088f65f-e37e-4636-bdbb-aff9564b8493)

SSLCOMMERZE interface:

![3 SSLCOMMERZE](https://github.com/user-attachments/assets/c2b55b2c-f4fb-4a73-a6a1-63ddf47b0f37)

SSLCOMMERZE OTP page:

![4  OTP page](https://github.com/user-attachments/assets/c6bdbbca-c686-4f22-adf5-d1fdec233971)

After Payment successful message: 
![5  successfull msg](https://github.com/user-attachments/assets/d258fcd1-df6a-4228-b025-de7a1d528649)

Customer GOT mail:

![customer got mail](https://github.com/user-attachments/assets/b8abb2c7-4f75-4fa3-a7cc-7d5ae7298170)

Admin Dashboard:

![7](https://github.com/user-attachments/assets/befa009f-55d9-4a52-a1e1-cd0623f372f5)

## Usage
1.  Open your browser and go to `http://127.0.0.1:8000/`.
2.  Select the desired ticket quantities, enter your name and email.
3.  Click "Proceed to Payment".
4.  You will be redirected to the SSLCommerz Testbox Gateway. Enter any OTP (e.g., `123456`) and click "Success".
5.  You will be redirected back to the landing page with a payment success message and your unique booking ID.
6.  A confirmation email will be sent to the provided email address.



## Future Enhancements
* Implement user authentication for booking history.
* Add a proper "My Bookings" page for users.
* Integrate a more robust logging system (e.g., Sentry).
* Add ticket cancellation/refund functionality.
* Improve frontend error handling and user feedback.
* Implement ticket PDF generation.
