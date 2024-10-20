import json

d = json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
print(d.foo)