# repl-nix-workspace

## Description
Add your description here.

## Prérequis

- Python >= 3.11
- [pip](https://pip.pypa.io/en/stable/)

## Installation

```bash
git clone https://github.com/Pimoos83/See.git
cd See
python -m venv venv
source venv/bin/activate     # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement du projet

```bash
python src/app.py
```
ou
```bash
gunicorn src.app:app
```

## Structure du projet

```
See/
├── src/
│   ├── app.py
│   ├── main.py
│   └── utils.py
├── requirements.txt
├── pyproject.toml
├── README.md
└── ...
```

> Pense à adapter le nom du fichier principal selon ton projet (app.py, main.py, etc.).
