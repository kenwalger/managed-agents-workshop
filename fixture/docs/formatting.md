# Formatting lengths

`format_quantity` turns a number and a unit into display text.

## Choose the number of decimal places

```python
import metrolen
print(metrolen.format_quantity(2.5, "m", precision=1))
```

Output:

```text
2.5 m
```

## Use the default precision

```python
import metrolen
print(metrolen.format_quantity(1.23456, "km"))
```

Output:

```text
1.23 km
```
