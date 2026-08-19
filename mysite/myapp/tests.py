from decimal import Decimal

from django.test import TestCase

from .models import Wishlist, Cart, product, user


class WishlistPageTests(TestCase):
    def setUp(self):
        self.seller = user.objects.create(
            fname='Seller',
            lname='One',
            email='seller@example.com',
            password='secret',
            mobile=987654321,
            address='Test address',
            profile_picture='profile_pictures/seller.jpg',
            usertype='seller',
        )
        self.buyer = user.objects.create(
            fname='Buyer',
            lname='One',
            email='buyer@example.com',
            password='secret',
            mobile=123456789,
            address='Buyer address',
            profile_picture='profile_pictures/buyer.jpg',
            usertype='buyer',
        )
        self.product_obj = product.objects.create(
            seller=self.seller,
            product_catagory='fruits',
            product_name='Apple',
            product_price=Decimal('12.50'),
            product_desc='Fresh apple',
            product_image='product_images/apple.jpg',
        )
        session = self.client.session
        session['email'] = self.buyer.email
        session.save()

    def test_wishlist_page_shows_saved_product(self):
        Wishlist.objects.create(user=self.buyer, product=self.product_obj)

        response = self.client.get('/wishlist/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Wishlist')
        self.assertContains(response, 'Apple')

    def test_wishlist_count_is_updated_in_session(self):
        Wishlist.objects.create(user=self.buyer, product=self.product_obj)

        response = self.client.get('/wishlist/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['wishlist_count'], 1)

    def test_product_details_shows_remove_button_when_in_wishlist(self):
        Wishlist.objects.create(user=self.buyer, product=self.product_obj)

        response = self.client.get(f'/product-details/{self.product_obj.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Remove From Wishlist')
        self.assertNotContains(response, 'Add To Wishlist')

    def test_add_to_cart_creates_cart_item_and_redirects_to_cart(self):
        response = self.client.get(f'/add-to-cart/{self.product_obj.pk}/', follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cart')
        self.assertEqual(Cart.objects.filter(user=self.buyer).count(), 1)
        self.assertEqual(self.client.session['cart_count'], 1)

    def test_cart_page_shows_saved_cart_product(self):
        Cart.objects.create(
            user=self.buyer,
            product=self.product_obj,
            product_price=12.50,
            product_qty=1,
            total_price=12.50,
        )

        response = self.client.get('/cart/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Cart')
        self.assertContains(response, 'Apple')
