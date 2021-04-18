#include "Python.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPWSTR lpCmdLine, int nCmdShow) {

    int argc = 4;
    wchar_t* argv[] = {

        L"bbsed.exe",
        L"-E",
        L"-m",
        L"bbsed",
    };
    return Py_Main(argc, argv);
}
