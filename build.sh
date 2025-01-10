cd miniros
rm -rf dist
../venv/bin/python -m build
cd ..
venv/bin/pip install miniros/dist/miniros-0.0.1-py3-none-any.whl --force-reinstall
echo Done