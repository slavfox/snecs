import datetime
import configparser
from pathlib import Path

project = "snecs"
copyright = f"{datetime.date.today().year}, Slavfox"
author = "Slavfox"
_config = configparser.ConfigParser()
_config.read(Path(__file__).resolve().parent.parent / "setup.cfg")
version = release = _config["bumpversion"]["current_version"]
del _config

extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx"]
templates_path = ["_templates"]
exclude_patterns = ["_build"]
html_theme = "alabaster"
html_static_path = ["_static"]
html_favicon = "_static/favicon.png"
html_logo = "_static/snecs_logo_bw.png"
default_role = "any"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}


def setup(app):
    app.add_stylesheet("style-overrides.css")
