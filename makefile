format:
	rm -rf __pycache__
	black *.py

getData:
	python3 fbrefDataGetter.py 2018-2019
	python3 fbrefDataGetter.py 2019-2020
	python3 fbrefDataGetter.py 2020-2021
	python3 fbrefDataGetter.py 2021-2022
