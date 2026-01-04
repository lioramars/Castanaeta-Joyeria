import os
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment

def get_paypal_client():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    mode = os.getenv("PAYPAL_MODE", "sandbox")

    if mode == "live":
        environment = LiveEnvironment(
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        environment = SandboxEnvironment(
            client_id=client_id,
            client_secret=client_secret
        )

    return PayPalHttpClient(environment)
