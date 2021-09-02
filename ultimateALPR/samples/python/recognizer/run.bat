setlocal
set arg1=%1
set PYTHONPATH=../../../binaries/windows/x86_64;../../../python
python recognizer.py --image %arg1% --assets ../../../assets