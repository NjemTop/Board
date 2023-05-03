from peewee_migrate import Router
from .model_class import conn

router = Router(conn)

def create_migrations():
    router.create(auto=True)
    router.run()
