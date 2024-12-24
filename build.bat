pip uninstall miniros
cd miniros
rmdir /s /q dist
python -m build
pip install dist/miniros-0.0.1-py3-none-any.whl --force-reinstall
cd ..