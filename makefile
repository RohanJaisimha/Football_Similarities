format:
	rm -rf __pycache__
	rm -rf */__pycache__
	black *.py
	black */*.py
