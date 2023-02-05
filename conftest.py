from django.test import Client
from pytest import fixture


@fixture
def client():
    return Client()


@fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@fixture(scope='session', autouse=True)
def django_db_setup(django_db_setup):
    pass
