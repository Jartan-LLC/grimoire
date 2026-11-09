# Publish the built wheel to PyPI. PyPI never accepts the same version twice: if an upload is
# broken, yank it on PyPI and release the next patch version instead.
publish:
	python3 -m build
	python3 -m twine upload dist/*
