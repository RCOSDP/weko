from flask import url_for,current_app


def login(client, obj = None, email=None, password=None):
    """Log the user in with the test client."""
    login_url = url_for('security.login')

    if obj:
        email = obj.email
        password = obj.password_plaintext
        client.post(login_url, data=dict(
            email=email or current_app.config['TEST_USER_EMAIL'],
            password=password or current_app.config['TEST_USER_PASSWORD'],
        ))
    else:
        client.post(login_url, data=dict(
            email=email or current_app.config['TEST_USER_EMAIL'],
            password=password or current_app.config['TEST_USER_PASSWORD'],
        ))

def logout(client):
    logout_url = url_for("security.logout")
    client.get(logout_url)
