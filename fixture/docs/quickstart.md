# Quickstart

metrolen converts, formats, and parses lengths. Add the folder that contains
`metrolen` to `PYTHONPATH`, then import it.

## Check whether a unit is metric

```python
import metrolen
print(metrolen.is_metric("km"))
```

Output:

```text
True
```

## Convert between units

```python
import metrolen
print(metrolen.convert(5, "km", "m"))
```

Output:

```text
5000.0
```
