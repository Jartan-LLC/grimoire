# pubsubby

`pip install pubsubby`

```python
from pubsubby import Client

client = Client("broker.example.com")
client.subscribe("orders", cb=handle_order)
```
