from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from flask import current_app

def paypal_client():
    if current_app.config["PAYPAL_MODE"] == "sandbox":
        env = SandboxEnvironment(
            client_id=current_app.config["Ac-JNjw6BP4gSFevb84-9BMIZzlAkAk7F5gZRYXHCgrZ1UvSprI9cqrc0wZu34YabHILQ2Wr827A4nD7"],
            client_secret=current_app.config["EN6E574mviE1Y4NYyKtRZlCL7x4e2OIbARUp4zi0nOfhVh01Rc_8mzOs0h8eGTcogUxb1ZNEieuENKzR"]
        )
    else:
        env = LiveEnvironment(
            client_id=current_app.config["ATZf-Ol3y8Ihys93GOK-nS3Ui0lqvrTsaBwa8uTNfaxqxuo1vMLwdwY0T0sqI_NQSbbcDMB_tbxZ4QQQ"],
            client_secret=current_app.config["ECON0dYSvER4hA65ufDjiUInQzjHn4pzzhrEuGXqhuL8Pvys5HW4VJCLiOZ4h5IfgN_-n9r1IP2rd_YS"]
        )

    return PayPalHttpClient(env)
