from __future__ import annotations

import ctypes
import sys

_MUTEX_HANDLE = None
ERROR_ALREADY_EXISTS = 183


def _close_boot_splash() -> None:
    try:
        import pyi_splash  # type: ignore
        pyi_splash.close()
    except Exception:
        pass


def _single_instance_ok() -> bool:
    global _MUTEX_HANDLE

    if not sys.platform.startswith('win'):
        return True

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.GetLastError.restype = ctypes.c_ulong

    _MUTEX_HANDLE = kernel32.CreateMutexW(
        None,
        False,
        'Local\\ConvertidorImagenSVG_CAZEL_v4',
    )

    if not _MUTEX_HANDLE:
        return True

    return kernel32.GetLastError() != ERROR_ALREADY_EXISTS


def _show_already_running_message() -> None:
    _close_boot_splash()
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            'Convertidor ya abierto',
            'El Convertidor de Imagen a SVG ya se esta abriendo o ya esta abierto.\n\n'
            'No es necesario volver a hacer doble clic. Revisa la barra de tareas.',
            parent=root,
        )
        root.destroy()
    except Exception:
        pass


def main() -> None:
    if not _single_instance_ok():
        _show_already_running_message()
        return

    # La pantalla de carga de PyInstaller permanece visible mientras
    # se importan la interfaz y las librerias de la aplicacion.
    from app import run_app

    run_app()


if __name__ == '__main__':
    main()
