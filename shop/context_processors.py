def cart_summary(request):
    cart = request.session.get("cart", {})
    count = 0
    if isinstance(cart, dict):
        for quantity in cart.values():
            if isinstance(quantity, int) and not isinstance(quantity, bool) and quantity > 0:
                count += quantity
    return {"cart_item_count": count}
