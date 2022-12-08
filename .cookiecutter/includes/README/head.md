Usage
-----

```python
from checkmatelib import CheckmateClient, CheckmateException

client = CheckmateClient("http://checkmate.example.com")
try:
    hits = client.check_url("http://bad.example.com", "YOUR_CHECKMATE_API_KEY")
   
except CheckmateException:
    ...   # To block or not to block?

if hits:
    print(hits.reason_codes)
```

### Updating the data files

You can refresh the domain information with the following command:

```shell
hdev run update-data
```
