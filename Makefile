# ---------------------------------
#          INSTALL & TEST
# ---------------------------------
install_requirements:
	@pip install -r requirements.txt

check_code:
	@flake8 --ignore=E501,W503 tests/*.py model_data/*.py

black:
	@black tests/*.py model_data/*.py

test:
	@pytest --verbose --capture=no tests/test_with_pytest.py

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ */*.pyc __pycache__
	@rm -fr build dist
	@rm -fr frontend-test-*.dist-info
	@rm -fr frontend-test.egg-info

install:
	@pip install . -U

all: clean install test black check_code
