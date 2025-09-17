import json
import pytest
from django.test import Client, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache


GRAPHQL_URL = "/api/graphql/"
User = get_user_model()


def gql(client: Client, query: str, variables: dict | None = None):
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    return client.post(GRAPHQL_URL, data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
@override_settings(RECAPTCHA_ENABLED=False)
def test_token_auth_success_when_recaptcha_disabled():
    client = Client()
    user = User.objects.create_user(
        email="john.doe@upeu.edu.pe",
        password="S3cretPass!",
        first_name="John",
        last_name="Doe",
        role="PRACTICANTE",
    )

    query = """
    mutation TokenAuth($email: String!, $password: String!){
      tokenAuth(email: $email, password: $password){
        success
        message
        token
        refreshToken
        user { email role }
      }
    }
    """
    res = gql(client, query, {"email": user.email, "password": "S3cretPass!"})
    data = res.json()["data"]["tokenAuth"]
    assert data["success"] is True
    assert data["token"]
    assert data["refreshToken"]
    assert data["user"]["email"] == user.email


@pytest.mark.django_db
@override_settings(RECAPTCHA_ENABLED=False)
def test_token_auth_blocked_after_30_failures():
    client = Client()
    email = "blocked@upeu.edu.pe"
    # Simula 30 fallos previos
    cache.set(f"loginfail:{email}", 30, timeout=3600)

    query = """
    mutation TokenAuth($email: String!, $password: String!){
      tokenAuth(email: $email, password: $password){ success message token }
    }
    """
    res = gql(client, query, {"email": email, "password": "bad"})
    data = res.json()["data"]["tokenAuth"]
    assert data["success"] is False
    assert "bloqueado" in data["message"].lower()


@pytest.mark.django_db
@override_settings(RECAPTCHA_ENABLED=False, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_forgot_and_reset_password_with_code_flow():
    client = Client()
    pwd = "OldPass!123"
    user = User.objects.create_user(
        email="alice@upeu.edu.pe",
        password=pwd,
        first_name="Alice",
        last_name="Smith",
        role="PRACTICANTE",
    )

    # Solicitar OTP
    q_forgot = """
    mutation Forgot($email: String!){
      forgotPassword(email: $email){ success message }
    }
    """
    res1 = gql(client, q_forgot, {"email": user.email})
    data1 = res1.json()["data"]["forgotPassword"]
    assert data1["success"] is True

    # Obtener OTP desde cache
    code = cache.get(f"pwdotp:{user.email.lower()}")
    assert code, "OTP no generado"

    # Reset con código
    new_password = "NewPass!456"
    q_reset = """
    mutation Reset($email: String!, $code: String!, $pwd: String!, $conf: String!){
      resetPasswordWithCode(email: $email, code: $code, newPassword: $pwd, confirmPassword: $conf){
        success
        message
      }
    }
    """
    res2 = gql(client, q_reset, {"email": user.email, "code": code, "pwd": new_password, "conf": new_password})
    data2 = res2.json()["data"]["resetPasswordWithCode"]
    assert data2["success"] is True

    # Autenticar con nueva contraseña
    q_login = """
    mutation TokenAuth($email: String!, $password: String!){
      tokenAuth(email: $email, password: $password){ success token }
    }
    """
    res3 = gql(client, q_login, {"email": user.email, "password": new_password})
    data3 = res3.json()["data"]["tokenAuth"]
    assert data3["success"] is True
    assert data3["token"]


@pytest.mark.django_db
@override_settings(RECAPTCHA_ENABLED=False)
def test_change_password():
    client = Client()
    user = User.objects.create_user(
        email="bob@upeu.edu.pe",
        password="OldPwd!",
        first_name="Bob",
        last_name="Lee",
        role="PRACTICANTE",
    )
    # Login primero
    q_login = """
    mutation TokenAuth($email: String!, $password: String!){
      tokenAuth(email: $email, password: $password){ token }
    }
    """
    res_login = gql(client, q_login, {"email": user.email, "password": "OldPwd!"})
    token = res_login.json()["data"]["tokenAuth"]["token"]
    assert token

    # Llamar changePassword con autorización via cookie ya manejada por la vista
    q_change = """
    mutation Change($cur: String!, $new: String!, $conf: String!){
      changePassword(currentPassword: $cur, newPassword: $new, confirmPassword: $conf){ success message }
    }
    """
    res_change = gql(client, q_change, {"cur": "OldPwd!", "new": "NewPwd!1", "conf": "NewPwd!1"})
    data_change = res_change.json()["data"]["changePassword"]
    assert data_change["success"] is True


@pytest.mark.django_db
def test_logout_succeeds_even_without_refresh_token():
    client = Client()
    q_logout = """
    mutation { logout { success message } }
    """
    res = gql(client, q_logout)
    data = res.json()["data"]["logout"]
    assert data["success"] is True
