# Parsing lengths

`parse_quantity` reads text such as `"12 cm"` and returns a value and a unit.

## Parse a length

```python
import metrolen
print(metrolen.parse_quantity("12 cm"))
```

Output:

```text
(12.0, 'cm')
```

## Reject unknown units

Pass `strict=True` to raise an error for unit names metrolen does not know.

```python
import metrolen
print(metrolen.parse_quantity("5 km", strict=True))
```

Output:

```text
(5.0, 'km')
```
