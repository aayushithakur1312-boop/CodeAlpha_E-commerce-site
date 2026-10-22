from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Order, Product


class StorefrontTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            category=self.category,
            name="Headphones",
            description="Good sound for every day.",
            price=Decimal("1499.00"),
            stock=3,
        )
        self.user = User.objects.create_user(
            username="shopper", password="safe-password-123", email="shopper@example.com"
        )

    def test_home_search_and_category_filter(self):
        response = self.client.get(reverse("home"), {"q": "headphones", "category": "electronics"})
        self.assertContains(response, "Headphones")
        self.assertEqual(len(response.context["products"]), 1)

    def test_add_to_cart_updates_session_cart(self):
        response = self.client.post(
            reverse("cart_add", args=[self.product.pk]),
            {"quantity": "2"},
            HTTP_REFERER=reverse("home"),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 2)

    def test_add_to_cart_rejects_missing_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse("cart_add", args=[self.product.pk]), {"quantity": "1"}
        )
        self.assertEqual(response.status_code, 403)

    def test_add_to_cart_does_not_redirect_to_an_external_host(self):
        response = self.client.post(
            reverse("cart_add", args=[self.product.pk]),
            {"quantity": "1", "next": "https://example.org"},
        )
        self.assertRedirects(response, reverse("cart"))

    def test_checkout_requires_authentication(self):
        response = self.client.get(reverse("checkout"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('checkout')}"
        )

    def test_checkout_calculates_total_and_decrements_stock(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["cart"] = {str(self.product.pk): 2}
        session.save()
        response = self.client.post(
            reverse("checkout"),
            {
                "full_name": "Shopper",
                "email": "shopper@example.com",
                "phone": "9876543210",
                "address": "12 Market Street",
                "city": "Bengaluru",
                "postal_code": "560001",
                "total": "0.01",
            },
        )
        order = Order.objects.get(user=self.user)
        self.assertRedirects(
            response, reverse("order_confirmation", args=[order.number])
        )
        self.assertEqual(order.total, Decimal("2998.00"))
        self.assertEqual(order.payment_method, Order.PaymentMethod.COD)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(order.items.get().unit_price, Decimal("1499.00"))

    def test_checkout_rejects_quantity_above_stock_without_order(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["cart"] = {str(self.product.pk): 4}
        session.save()
        response = self.client.post(
            reverse("checkout"),
            {
                "full_name": "Shopper",
                "email": "shopper@example.com",
                "phone": "9876543210",
                "address": "12 Market Street",
                "city": "Bengaluru",
                "postal_code": "560001",
            },
        )
        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
