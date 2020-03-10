import datetime

project = "snecs"
default_role = "any"
# noinspection PyShadowingBuiltins
copyright = f"{datetime.date.today().year}, Slavfox"
author = "Slavfox"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
html_static_path = ["_static"]


intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
