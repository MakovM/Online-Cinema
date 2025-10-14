import os

from database.models.base import Base
from database.models.accounts import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
    UserProfileModel,
)
from database.models.movies import (
    Movie,
    Genre,
    Star,
    Director,
    Certification,
    movie_genres,
    movie_stars,
    movie_directors,
)
from database.models.carts import (
    Cart,
    CartItem,
)
from database.models.orders import OrderModel, OrderItemModel, OrderStatusEnum
from database.models.movies import (
    Movie,
    Genre,
    Star,
    Director,
    Certification,
    movie_genres,
    movie_stars,
    movie_directors,
)


from database.session_sqlite import reset_sqlite_database as reset_database

environment = os.getenv("ENVIRONMENT", "developing")

if environment == "testing":
    from database.session_sqlite import (
        get_sqlite_db_contextmanager as get_db_contextmanager,
        get_sqlite_db as get_db,
    )
else:
    from database.session_postgresql import (
        get_postgresql_db_contextmanager as get_db_contextmanager,
        get_postgresql_db as get_db,
    )
