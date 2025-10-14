from database.models.movies import Movie
from database.models.carts import Cart


def validate_cart_item(cart: Cart, movie: Movie) -> Movie:
    if any(item.movie_id == movie.id for item in cart.items):
        raise ValueError("This movie is already in the cart.")
    if movie.id in [m.id for m in cart.user.get_purchased_movies()]:
        raise ValueError("You have already purchased this movie.")
    return movie
