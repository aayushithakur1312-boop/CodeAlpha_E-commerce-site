from django.core.management.base import BaseCommand

from shop.models import Category, Product


SAMPLE_PRODUCTS = [
    (
        "Electronics",
        "Wireless Headphones",
        "Comfortable over-ear headphones with clear, balanced sound.",
        "1499.00",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=85",
        20,
    ),
    (
        "Electronics",
        "Smart Watch",
        "A stylish everyday smartwatch with a bright, easy-to-read display.",
        "2199.00",
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=85",
        15,
    ),
    (
        "Footwear",
        "Running Shoes",
        "Lightweight cushioned shoes for daily runs and active days.",
        "1799.00",
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=85",
        18,
    ),
    (
        "Accessories",
        "Everyday Backpack",
        "A practical, roomy backpack for commuting, college, and travel.",
        "999.00",
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=85",
        12,
    ),
    (
        "Accessories",
        "Classic Sunglasses",
        "Timeless lightweight sunglasses for a polished everyday look.",
        "799.00",
        "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=800&q=85",
        25,
    ),
    (
        "Electronics",
        "Compact Camera",
        "A versatile camera to capture favorite everyday moments.",
        "4999.00",
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=85",
        8,
    ),
]


class Command(BaseCommand):
    help = "Create the sample categories and products if they do not already exist."

    def handle(self, *args, **options):
        for category_name, name, description, price, image_url, stock in SAMPLE_PRODUCTS:
            category, _ = Category.objects.get_or_create(name=category_name)
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "description": description,
                    "price": price,
                    "image_url": image_url,
                    "stock": stock,
                },
            )
            if created:
                self.stdout.write(f"Added {product.name}")
        self.stdout.write(self.style.SUCCESS("Sample catalog is ready."))
