miniros() {
    venv/bin/python -m miniros "$@"
}

checkdeps() {
    venv/bin/pip install -r requirements.txt
}