import datetime
import inspect
import sys
from pathlib import Path

import toml

_REPO_ROOT = Path(__file__).resolve().parent.parent
with (_REPO_ROOT / "pyproject.toml").open() as f:
    _pyproject = toml.load(f)

project = "snecs"
copyright = f"{datetime.date.today().year}, Slavfox"
author = "Slavfox"
version = release = _pyproject["tool"]["poetry"]["version"]
repo = "https://github.com/slavfox/snecs"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.githubpages",
]
templates_path = ["_templates"]
exclude_patterns = ["_build"]
html_theme = "alabaster"
html_static_path = ["_static"]
html_favicon = "_static/favicon.png"
html_logo = None
html_baseurl = "https://snecs.slavfox.space/"
html_theme_options = {
    'logo': 'snecs_logo_bw.png',
    'canonical_url': html_baseurl,
    'fixed_sidebar': True,
    'touch_icon': 'apple_touch_icon.png',
    'extra_nav_links': {
        "GitHub repo": repo
    },
    "show_relbars": True,
    "head_font_family": "xkcd-script",
}
default_role = "any"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
autodoc_typehints = "description"

# Based on numpy code:
# https://github.com/numpy/numpy/blob/master/doc/source/conf.py#L328
def linkcode_resolve(domain, info):
    if domain != "py":
        return None

    module = info["module"]
    fullname = info["fullname"]

    obj = sys.modules.get(module)
    if not obj:
        return None

    for elem in fullname.split("."):
        try:
            obj = getattr(obj, elem)
        except Exception:
            return None

    try:
        sourcefile = inspect.getsourcefile(obj)
    except Exception:
        sourcefile = None

    if not sourcefile:
        return None

    linenos = ""
    try:
        source, lineno = inspect.getsourcelines(obj)
    except Exception:
        lineno = None
    else:
        if lineno:
            linenos = f"#L{lineno}-L{lineno + len(source) - 1}"

    filepath = Path(sourcefile).relative_to(_REPO_ROOT)

    return f"{repo}/tree/master/{filepath}{linenos}"


def setup(app):
    app.add_stylesheet("style-overrides.css")
