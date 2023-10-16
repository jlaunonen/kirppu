PYTHON := python
LANGUAGES := fi en
BROWSERS := firefox

# Optionally include user variables.
sinclude makevars

MM_ARGS = $(foreach lang, ${LANGUAGES}, -l ${lang}) -i KirppuVenv -i node_modules --no-location $(foreach ignore, ${MM_IGNORES}, -i ${ignore})

# Prefix for some commands to use when not run in activated virtualenv.
ifeq ($(origin VIRTUAL_ENV), undefined)
PFX := ./KirppuVenv/bin/
endif

PW_ARGS = $(foreach browser, ${BROWSERS}, --browser=${browser})


default: help

messages: ## Extract strings from sources for localization.
	DEBUG=1 ${PFX}${PYTHON} manage.py makemessages -d djangojs ${MM_ARGS}
	DEBUG=1 ${PFX}${PYTHON} manage.py makemessages -d django ${MM_ARGS}

static:   ## Install npm dependencies and build static files.
	cd kirppu && npm i && npm run build

compile:  ## Compile localizations for use.
	DEBUG=1 ${PFX}${PYTHON} manage.py compilemessages

c:        ## Clean compiled pyc files.
	find kirppu -name \*.pyc -exec rm {} +
	find kirppuauth -name \*.pyc -exec rm {} +
	find kirppu_project -name \*.pyc -exec rm {} +

cloc:     ## Count project lines using cloc.
	cloc --git HEAD --exclude-ext=po

apistub:  ## Create/update ajax_api stub file helping navigation from frontend code to backend.
	find kirppu -! -path "kirppu/node_modules*" -name \*.py -exec python3 make_api_stub.py --js kirppu/static_src/js/api_stub.js --py kirppu/tests/api_access.pyi -- {} +

test:     ## Run unit tests
	DEBUG=1 ${PFX}py.test -vvv -m "not web" ${ARGS}

browsertest:  ## Run browser tests
	DEBUG=1 DJANGO_ALLOW_ASYNC_UNSAFE=true ${PFX}py.test -vvv -m "web" ${PW_ARGS} ${ARGS}

alltests:  ## Run unit and browser tests
	DEBUG=1 DJANGO_ALLOW_ASYNC_UNSAFE=true ${PFX}py.test -vvv -m "not web or web" ${PW_ARGS} ${ARGS}

update-constraints:  ## Update constraints.txt to match pyproject.toml
	pip-compile --all-extras --output-file=constraints.txt --strip-extras --upgrade

requirement-sets:  ## Generate requirements-* files.
	scripts/generate-dep-set.py --extra dev -o "requirements-dev.txt"
	scripts/generate-dep-set.py --extra oauth --extra production -o "requirements-production.txt"

help:     ## This help.
	@grep -F -h "#""#" $(MAKEFILE_LIST) | sed -e "s/:[^#]*#""#/\n\t/" -e "s/\\s*#""#/\t/"

.PHONY: apistub c cloc compile default help messages requirement-sets static test update-constraints
