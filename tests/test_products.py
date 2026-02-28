def test_add_product(client):
    response = client.post("/products", json={
        "name": "Laptop",
        "price": 50000,
        "stock": 10
    })

    assert response.status_code == 200
    assert response.json["message"] == "Product added"


def test_get_products(client):
    client.post("/products", json={
        "name": "Mouse",
        "price": 500,
        "stock": 20
    })

    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json) == 1