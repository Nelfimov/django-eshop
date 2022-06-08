# Small Ecommerce shop, built with Django

Built from scratch shop for personal usage:
* Anonymous checkout and payment;
* Internalization for EN and DE;
* Integrated [Paypal Server Side Checkout](https://github.com/paypal/Checkout-Python-SDK);
* Email notification of User and Admins about succesfull order;
* Lightbox for image gallery;

> Kudos to [JustDjango](https://github.com/justdjango/django-ecommerce) and 
> the video [tutorial](https://www.youtube.com/watch?v=YZvRrldjf1Y) for gettings me started


## Usual ordering process:
1. User enters site;
2. User places item in the cart:
> if not logged in - cart with session key is created for this user;
> if logged in - cart for this user is created, session key remains empty;
3. User proceeds to checkout;
4. Order marked `ordered = False` is created if the info in checkout form is valid;
5. User proceeds for payment procedure. As of now it is only PayPal server side;


## Future plans:
* API;
* Additional payment methods;
* Auction functionality;
* Tracking API;