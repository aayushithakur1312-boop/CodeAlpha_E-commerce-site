from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CheckoutForm, RegistrationForm
from .models import Category, Order, OrderItem, Product


def _session_cart(request):
    stored_cart = request.session.get("cart", {})
    cart = {}
    if isinstance(stored_cart, dict):
        for product_id, quantity in stored_cart.items():
            product_id = str(product_id)
            if (
                product_id.isdigit()
                and isinstance(quantity, int)
                and not isinstance(quantity, bool)
                and quantity > 0
            ):
                cart[product_id] = cart.get(product_id, 0) + quantity
    if cart != stored_cart:
        request.session["cart"] = cart
    return cart


def _cart_items(request):
    cart = _session_cart(request)
    ids = [key for key in cart if str(key).isdigit()]
    products = Product.objects.filter(pk__in=ids, is_active=True).select_related(
        "category"
    )
    items = []
    total = Decimal("0.00")
    for product in products:
        quantity = cart.get(str(product.pk), cart.get(product.pk, 0))
        if not isinstance(quantity, int) or quantity < 1:
            continue
        subtotal = product.price * quantity
        items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
        total += subtotal
    return items, total


def home(request):
    products = Product.objects.filter(is_active=True).select_related("category")
    categories = Category.objects.filter(products__is_active=True).distinct()
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)
    return render(
        request,
        "shop/home.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "selected_category": category_slug,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"), slug=slug, is_active=True
    )
    return render(request, "shop/product_detail.html", {"product": product})


def cart_detail(request):
    items, total = _cart_items(request)
    return render(request, "shop/cart.html", {"items": items, "total": total})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        quantity = 0
    cart = _session_cart(request)
    existing = cart.get(str(product.pk), 0)
    if quantity < 1:
        messages.error(request, "Choose a valid quantity.")
    elif existing + quantity > product.stock:
        messages.error(request, f"Only {product.stock} unit(s) are currently in stock.")
    else:
        cart[str(product.pk)] = existing + quantity
        request.session.modified = True
        messages.success(request, f"{product.name} added to your cart.")
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("cart")


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = int(request.POST.get("quantity", "0"))
    except (TypeError, ValueError):
        quantity = -1
    cart = _session_cart(request)
    if quantity == 0:
        cart.pop(str(product.pk), None)
    elif 0 < quantity <= product.stock:
        cart[str(product.pk)] = quantity
    else:
        messages.error(request, f"Enter a quantity from 1 to {product.stock}.")
    request.session.modified = True
    return redirect("cart")


@require_POST
def cart_remove(request, product_id):
    cart = _session_cart(request)
    cart.pop(str(product_id), None)
    cart.pop(product_id, None)
    request.session.modified = True
    return redirect("cart")


@login_required
def checkout(request):
    items, total = _cart_items(request)
    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    form = CheckoutForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        cart = _session_cart(request)
        try:
            with transaction.atomic():
                product_ids = [int(key) for key in cart if str(key).isdigit()]
                locked_products = {
                    product.pk: product
                    for product in Product.objects.select_for_update()
                    .filter(pk__in=product_ids, is_active=True)
                    .order_by("pk")
                }
                order_lines = []
                current_total = Decimal("0.00")
                for product_id in product_ids:
                    product = locked_products.get(product_id)
                    quantity = cart.get(str(product_id), 0)
                    if (
                        product is None
                        or not isinstance(quantity, int)
                        or quantity < 1
                        or quantity > product.stock
                    ):
                        raise ValueError("A cart item is no longer available in that quantity.")
                    current_total += product.price * quantity
                    order_lines.append((product, quantity))

                order = Order.objects.create(
                    user=request.user,
                    payment_method=Order.PaymentMethod.COD,
                    total=current_total,
                    **form.cleaned_data,
                )
                for product, quantity in order_lines:
                    updated = Product.objects.filter(
                        pk=product.pk, is_active=True, stock__gte=quantity
                    ).update(stock=F("stock") - quantity)
                    if updated != 1:
                        raise ValueError(
                            f"{product.name} just sold out. Review your cart and try again."
                        )
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=quantity,
                    )
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("cart")
        request.session["cart"] = {}
        return redirect("order_confirmation", number=order.number)

    return render(
        request, "shop/checkout.html", {"form": form, "items": items, "total": total}
    )


@login_required
def order_confirmation(request, number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), number=number, user=request.user
    )
    return render(request, "shop/order_confirmation.html", {"order": order})


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")
    return render(request, "shop/register.html", {"form": form})
