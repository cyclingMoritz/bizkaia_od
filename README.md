# Bizkaia OD

Hackathon to visualize Bizkaia Open data

## 🧩 Project Structure

data/ # Raw, processed and external data
notebooks/ # Jupyter notebooks
src/ # Source code for data processing and modeling
tests/ # Unit tests

## ⚙️ Setup

### 1️⃣ Install Dependencies

Create and set up a **virtual environment** using `uv`:

```sh
uv sync
```

### 2️⃣ Activate the Environment

```sh
source .venv/bin/activate
```
### 3️⃣ Add the environment to the list of Jupyter kernels

```sh
python -m ipykernel install --user --name=bizkaia_od --display-name "Python (uv-bizkaia_od)"
```
### Install local library

```sh
uv pip install -e .
```

# 🧠 Notes
You can import project paths easily:
```python
from src.config import RAW_DATA_DIR
```