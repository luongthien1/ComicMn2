# BaseWed
The base wed side with frontend and backend for all thing

## Backend

Framework: Fastapi

Install with uv: uv install ...

### Start:

1. Create venv:

```python -m venv .venv```

2. Active the venv

3. Install uv:

```pip install uv```

And use ```uv sync``` for install all library in pyproject.toml, if there are some others, use ```uv add <package name>```

### Precommit

Install pre-commit (need to run ```uv sync``` before)

```pre-commit install```



## Frontend

React with Typescript, main css framework is antd (ant design)

Routes in routes folder, with routes_config with setting url, and other folder is the main screen be set in routes_config.

### Npm install

Cd into frontend folder, run:

```npm install```

### Node run

At the project root folder:
```
npm install concurrently

npm run dev
```