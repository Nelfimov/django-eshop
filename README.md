# Small Ecommerce shop, built with Django

Built from scratch shop for personal usage:
* Anonymous checkout and payment through Sessions;
* Internalization for EN and DE;
* Integrated [Paypal Server Side Checkout](https://github.com/paypal/Checkout-Python-SDK);
* Email notification of User and Admins about succesfull order;
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
6. Run local server `python manage.py runserver`
7. In the admin panel `127.0.0.1/admin` change name of your website

## Usual ordering process:
1. User enters site;
2. User places item in the cart:
> if not logged in - cart with `session_key` is created for this user;
> if logged in - cart for this user is created, `session_key` remains empty;
3. User proceeds to checkout;
4. Order marked `ordered = False` is created if the info in checkout form is valid;
5. User proceeds for payment procedure. As of now it is only PayPal server side;


## Future plans:    
* API;
* Additional payment methods;
* Auction functionality;
* Tracking API;