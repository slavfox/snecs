.PHONY: help lint test doc-deps docs

ifdef NOCOLOR
NC=
ERROR=[ERROR]
INFO=[INFO]
WARNING=[WARNING]
$(info $(INFO) Output coloring is disabled.)
else
NC=$(shell printf "\033[0m")
ERROR=$(shell printf "\033[1;31m")[ERROR]$(NC)
INFO=$(shell printf "\033[1;32m")[INFO]$(NC)
WARNING=$(shell printf "\033[1;33m")[WARNING]$(NC)
$(info $(INFO) Output coloring is enabled. Pass NOCOLOR=true to disable.)
endif

POETRY_PYTHON=$(shell poetry run which python)
PYTHON_IMPLEMENTATION=$(shell $(POETRY_PYTHON) -c "import sys;print(sys.implementation.name)")
MYPY_CMD="$(POETRY_PYTHON) -m mypy"
VENV_SITE_PACKAGES=$(shell poetry run python -c "import site; print(site.getsitepackages()[0])")

ifneq ($(shell $(POETRY_PYTHON) -m mypy -V 2>/dev/null; echo $$?), 0)
ifneq (, $(shell which mypy))
	MYPY_CMD=$(shell which mypy)
else
	MYPY_CMD=
endif
endif

ifneq ($(shell $(POETRY_PYTHON) -m mypy -V 2>/dev/null; echo $$?), 0)
WHICH_BLACK=$(shell which black)
ifneq (, $$WHICH_BLACK)
	BLACK_CMD=$(WHICH_BLACK)
else
	BLACK_CMD=
endif
endif

SRC_DIR=snecs
TESTS_DIR=
DOCS_DIR=

help:
	@printf "make help         - display this message\n"
	@printf "make test         - run tests\n"
	@printf "make lint         - run linters\n"
	@printf "make docs         - run tests\n"

# Run all linters (isort, black, flake8, mypy) without early-exiting if
# any of them fails.
lint: $(VENV_SITE_PACKAGES)/flake8 $(VENV_SITE_PACKAGES)/isort
	@STATUS=0; \
	printf "$(INFO) Running isort.$(NC)\n"; \
	poetry run isort -ac -rc $(SRC_DIR) $(TESTS_DIR) $(DOCS_DIR) || { \
		STATUS=$$?; printf "$(ERROR) isort failed.\n"; \
	}; \
	if ! [[ -z "$(BLACK_CMD)" ]]; then \
		printf "$(INFO) Running black.$(NC)\n"; \
	    $(BLACK_CMD) $(SRC_DIR) $(TESTS_DIR) $(DOCS_DIR) || { \
			STATUS=$$?; printf "$(WARN) Reformatted sources.\n"; \
		}; \
	fi; \
	printf "$(INFO) Running flake8.$(NC)\n"; \
	poetry run flake8 $(SRC_DIR) $(TESTS_DIR) $(DOCS_DIR) || { \
		STATUS=$$?; printf "$(ERROR) flake8 failed.\n"; \
	}; \
	if ! [[ -z "$(MYPY_CMD)" ]]; then \
		printf "$(INFO) Running mypy.$(NC)\n"; \
	    $(MYPY_CMD) $(SRC_DIR) $(TESTS_DIR) || { \
			STATUS=$$?; printf "$(ERROR) mypy failed.\n"; \
		}; \
	fi; \
	if [[ $$STATUS -eq 0 ]]; then \
		printf "$(INFO) No lint issues found.$(NC)\n"; \
	else \
		printf "$(ERROR) Encountered issues.$(NC)\n"; \
		exit $$STATUS; \
	fi

$(VENV_SITE_PACKAGES)/%:
	@printf "$(INFO) Installing dev dependencies.$(NC)\n"
	@poetry install -E docs
	@printf "$(INFO) Done.$(NC)\n"

docs: $(VENV_SITE_PACKAGES)/sphinx
	cd docs && make html
