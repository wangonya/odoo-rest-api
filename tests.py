def test_login(client):
    response = client.post('/api/login', json={
        'username': 'admin', 'password': 'admin'
    })

    assert response.status_code == 200
    assert response.get_json()['message'] == 'Login successful'


def test_login_failure(client):
    response = client.post('/api/login', json={
        'username': 'badadmin', 'password': 'badadmin'
    })

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Invalid username / password'


def test_create_sale_order(client):
    assert True is False
