import json
import random
from datetime import UTC, datetime, timedelta

import factory
from faker import Faker


class FirebaseUserFactory(factory.Factory):
    class Meta:
        model = dict

    uid = factory.Faker("uuid4")
    email = factory.Faker("email")
    email_verified = factory.Faker("pybool")
    display_name = factory.Faker("name")
    photo_url = factory.Faker("image_url")
    disabled = factory.Faker("pybool")
    provider_data = factory.LazyAttribute(
        lambda obj: [
            {
                "provider_id": random.choice(["google.com", "github.com"]),
                "display_name": obj.display_name,
                "photo_url": obj.photo_url,
                "email": obj.email,
                "uid": obj.uid,
            },
        ],
    )
    metadata = factory.LazyAttribute(
        lambda obj: {
            "last_sign_in_time": Faker().unix_time(),
            "creation_time": Faker().unix_time(),
        },
    )
    tenant_id = factory.Faker("word")


class FirebaseAuthTokenFactory(factory.Factory):
    class Meta:
        model = dict

    iss = factory.LazyFunction(lambda: f"https://securetoken.google.com/{Faker().word()}")
    aud = factory.Faker("url")
    iat = factory.LazyFunction(
        lambda: Faker().unix_time(
            start_datetime=datetime.now(tz=UTC) - timedelta(seconds=60),
            end_datetime=datetime.now(tz=UTC),
        ),
    )
    exp = factory.LazyAttribute(lambda obj: obj.iat + obj.oauth_expires_in)
    event_id = factory.Faker("ean")
    event_type = factory.Iterator(["beforeSignUp", "beforeSignIn"])
    sign_in_method = factory.Iterator(["google.com", "github.com", "password"])
    raw_user_info = factory.LazyAttribute(
        lambda obj: json.dumps(
            {
                "name": obj.user_record["display_name"],
                "granted_scopes": " ".join([]),
                "id": obj.user_record["uid"],
                "verified_email": obj.user_record["email_verified"],
                "given_name": obj.user_record["display_name"].split(" ", 1)[0],
                "family_name": obj.user_record["display_name"].split(" ", 1)[-1],
                "locale": obj.locale,
                "hd": obj.user_record["email"].split("@")[-1],
                "email": obj.user_record["email"],
                "picture": obj.user_record["photo_url"],
            },
        ),
    )
    oauth_id_token = factory.Faker("ean")
    oauth_access_token = factory.Faker("ean")
    oauth_token_secret = None
    oauth_refresh_token = factory.Faker("ean")
    oauth_expires_in = 3600
    user_agent = factory.Faker("user_agent")
    ip_address = factory.Faker("ipv4")
    locale = "en"
    sub = factory.Faker("ean")
    tenant_id = factory.Faker("word")
    user_record = factory.SubFactory(FirebaseUserFactory)
