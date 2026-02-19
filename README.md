# logster

Compact JSON log formatter for pipe mode.

## Install

```bash
pip install .
```

## Run

```bash
your_app 2>&1 | logster
```

Example with uvicorn:

```bash
uvicorn app:app --reload 2>&1 | logster
```
