# Small Ecommerce shop, built with Django

Built from scratch shop for personal usage:
* Templates built on [Material Design Bootstrap 4](https://mdbootstrap.com/docs/b4/jquery/);
* Anonymous checkout and payment through [Django Sessions](https://docs.djangoproject.com/en/4.0/topics/http/sessions/);
* Internalization for EN and DE;
* Integrated [Paypal Server Side Checkout](https://github.com/paypal/Checkout-Python-SDK);
* Email notification of User and Admins about succesfull order, refunds, deliveries;
* Lightbox for image gallery;

> Kudos to [JustDjango](https://github.com/justdjango/django-ecommerce) and 
> the video [tutorial](https://www.youtube.com/watch?v=YZvRrldjf1Y) for getting me started!


## Installation
1. Create virtual environment inside downloaded folder `python -m venv venv`
2. Switch to virtual environment: 
> *nix `source venv/bin/activate`
> Windows `venv/bin/activate`
3. Install all dependencies from requirements.txt `pip install -r requirements.txt`
4. Migrate everything, create database 
> `python manage.py makemigrations`
> `python manage.py migrate`
5. Create superuser (admin) `python manage.py createsuperuser`
6. Create `.env` file in root directory with fields:
> DJANGO_SECRET_KEY = "YOUR DJANGO SECRET. CAN BE GENERATED VIA [GENERATION](https://humberto.io/blog/tldr-generate-django-secret-key/)"\
> HOST = "YOUR EXTERNAL IP ON WHICH YOU WOULD LIKE TO SERVE YOUR APP"\
> PAYPAL_CLIENT_ID = "TO BE OBTAINED IN develope.paypal.com"\
> PAYPAL_CLIENT_SECRET = "TO BE OBTAINED IN develope.paypal.com"\
> GMAIL_ACCOUNT = "YOUR GMAIL ADDRESS"\
> GMAIL_PASSWORD = "YOUR GMAIL APP PASSWORD"\
7. App uses memcached. Either install memcached on your machine or change settings.py "CACHES"
8. Run local server `python manage.py runserver` 
9. In the admin panel `127.0.0.1/admin` change domain name of your website

## Usual ordering process:
1. User enters site;
2. User places item in the order with `ordered = False` which is a workaround for cart implementation:
> if not logged in - Order with `session_key` is created for this user;
> if logged in - Order for this user is created, `session_key` remains empty;
3. User proceeds to checkout;
4. User proceeds for payment procedure. As of now it is only PayPal server side;
5. After succesfull capture of Paypal credit, Order is marked `ordered = True` and available for admin to proceed with the delivery;


## Future plans:    
* API;
* Additional payment methods;
* Auction functionality;
* Tracking API;