@ECHO OFF

WHERE python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 GOTO :InstallPython

WHERE pip >nul 2>nul
IF %ERRORLEVEL% NEQ 0 GOTO :InstallPython

CALL pip install virtualenv virtualenvwrapper-win
CALL rmvirtualenv snap_attack_solver >nul 2>nul
CALL mkvirtualenv snap_attack_solver --clear --no-wheel --no-setuptools
CALL workon snap_attack_solver
CALL pip install -r requirements.txt
CALL deactivate

GOTO :End

:InstallPython
ECHO Please install Python 3 before running setup.bat (https://www.python.org/downloads)
ECHO Make sure to let installer add Python to system PATH

:End
PAUSE
