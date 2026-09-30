from fastapi.testclient import TestClient
from main import app

client=TestClient(app) #

def test_any():
    respone=client.get("/items/10?q=phone")
    assert respone.status_code==200
    assert respone.json() == {
  "item_id": 10,
  "q": "phone"
}
    respone2=client.get("/items/10")
    assert respone2.status_code==200
    assert respone2.json() == {
      "item_id": 10,
      "q": None
    }
    respone3=client.get("/items/0")
    assert respone3.status_code==422
   

    
