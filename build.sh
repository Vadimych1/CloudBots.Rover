cd miniros
rm -rf dist
python -m build
pip install ./dist/miniros/miniros-0.0.1-py3-none-any.whl --force-reinstall
cd ..
echo "Done"