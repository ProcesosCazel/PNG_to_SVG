from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from vectorizer import VectorizationError

APP_TITLE = 'Convertidor de Imagen a SVG'


class SvgConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry('900x610')
        self.minsize(820, 560)
        self.protocol('WM_DELETE_WINDOW', self.destroy)

        self.selected_file: Path | None = None
        self.output_file: Path | None = None
        self.preview_image = None

        self._configure_style()
        self._build_ui()
        self.after(100, self._mark_ready)

    def _mark_ready(self) -> None:
        self.status.config(text='Listo. Selecciona una imagen para comenzar.')

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use('vista')
        except tk.TclError:
            pass
        style.configure('Title.TLabel', font=('Segoe UI', 22, 'bold'))
        style.configure('Subtitle.TLabel', font=('Segoe UI', 10))
        style.configure('Big.TButton', font=('Segoe UI', 11, 'bold'), padding=(16, 10))
        style.configure('Status.TLabel', font=('Segoe UI', 10))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=24)
        root.pack(fill='both', expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)

        ttk.Label(root, text='Convertidor PNG / JPEG a SVG', style='Title.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='w'
        )
        ttk.Label(
            root,
            text='Selecciona una imagen, revisa la vista previa y presiona Convertir a SVG.',
            style='Subtitle.TLabel',
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=(4, 18))

        left = ttk.LabelFrame(root, text='1. Imagen de entrada', padding=16)
        left.grid(row=2, column=0, sticky='nsew', padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        ttk.Button(left, text='Seleccionar imagen...', command=self.select_image, style='Big.TButton').grid(
            row=0, column=0, sticky='ew', pady=(0, 12)
        )

        self.preview = tk.Label(
            left,
            text='Sin imagen seleccionada',
            bg='#f4f4f4',
            fg='#666666',
            relief='solid',
            bd=1,
            font=('Segoe UI', 11),
        )
        self.preview.grid(row=1, column=0, sticky='nsew')

        self.file_label = ttk.Label(left, text='PNG, JPG o JPEG', anchor='center')
        self.file_label.grid(row=2, column=0, sticky='ew', pady=(10, 0))

        right = ttk.LabelFrame(root, text='2. Conversion', padding=16)
        right.grid(row=2, column=1, sticky='nsew', padx=(10, 0))
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text='Calidad:').grid(row=0, column=0, sticky='w')
        self.quality = ttk.Combobox(right, state='readonly', values=['Rapida', 'Normal', 'Alta', 'Super alta'])
        self.quality.set('Alta')
        self.quality.grid(row=1, column=0, sticky='ew', pady=(4, 6))

        ttk.Label(
            right,
            text='Super alta = mas nitidez y detalle, pero puede tardar varios segundos.',
            wraplength=330,
            justify='left',
        ).grid(row=2, column=0, sticky='w', pady=(0, 12))

        self.convert_button = ttk.Button(
            right,
            text='Convertir a SVG',
            command=self.start_conversion,
            state='disabled',
            style='Big.TButton',
        )
        self.convert_button.grid(row=3, column=0, sticky='ew')

        self.progress = ttk.Progressbar(right, mode='indeterminate')
        self.progress.grid(row=4, column=0, sticky='ew', pady=(12, 0))

        ttk.Separator(right).grid(row=5, column=0, sticky='ew', pady=20)

        self.status = ttk.Label(
            right,
            text='Iniciando...',
            style='Status.TLabel',
            wraplength=330,
            justify='left',
        )
        self.status.grid(row=6, column=0, sticky='w')

        self.open_svg_button = ttk.Button(
            right, text='Abrir SVG', command=self.open_svg, state='disabled', style='Big.TButton'
        )
        self.open_svg_button.grid(row=7, column=0, sticky='ew', pady=(24, 8))

        self.open_folder_button = ttk.Button(
            right, text='Abrir carpeta de salida', command=self.open_folder, state='disabled'
        )
        self.open_folder_button.grid(row=8, column=0, sticky='ew')

        ttk.Label(
            root,
            text='El SVG se guarda en la misma carpeta que la imagen original.',
            anchor='center',
        ).grid(row=3, column=0, columnspan=2, sticky='ew', pady=(16, 0))

    def select_image(self) -> None:
        path = filedialog.askopenfilename(
            title='Seleccionar imagen',
            filetypes=[
                ('Imagenes compatibles', '*.png *.jpg *.jpeg'),
                ('PNG', '*.png'),
                ('JPEG', '*.jpg *.jpeg'),
            ],
        )
        if not path:
            return

        self.selected_file = Path(path)
        self.output_file = None
        self.file_label.config(text=self.selected_file.name)
        self.status.config(text='Imagen lista para convertir. Selecciona la calidad deseada.')
        self.convert_button.config(state='normal')
        self.open_svg_button.config(state='disabled')
        self.open_folder_button.config(state='disabled')
        self._show_preview(self.selected_file)

    def _show_preview(self, path: Path) -> None:
        try:
            from PIL import Image, ImageTk

            with Image.open(path) as img:
                preview = img.convert('RGB')
                preview.thumbnail((390, 360), Image.Resampling.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(preview)
            self.preview.config(image=self.preview_image, text='')
        except Exception:
            self.preview.config(image='', text='No fue posible mostrar la vista previa')

    def start_conversion(self) -> None:
        if not self.selected_file:
            return

        output = self.selected_file.with_suffix('.svg')
        if output.exists():
            overwrite = messagebox.askyesno(
                'Archivo existente',
                f'Ya existe:\n{output.name}\n\nDeseas reemplazarlo?',
            )
            if not overwrite:
                selected = filedialog.asksaveasfilename(
                    title='Guardar SVG como...',
                    defaultextension='.svg',
                    initialfile=f'{self.selected_file.stem}_vector.svg',
                    filetypes=[('SVG', '*.svg')],
                )
                if not selected:
                    return
                output = Path(selected)

        self.output_file = output
        self.convert_button.config(state='disabled')
        self.open_svg_button.config(state='disabled')
        self.open_folder_button.config(state='disabled')
        self.status.config(text='Convirtiendo imagen...')
        self.progress.start(12)

        quality = self.quality.get()
        input_file = self.selected_file
        output_file = self.output_file
        thread = threading.Thread(
            target=self._convert_worker,
            args=(input_file, output_file, quality),
            daemon=True,
        )
        thread.start()

    def _convert_worker(self, input_file: Path, output_file: Path, quality: str) -> None:
        started = time.perf_counter()
        try:
            # Heavy numerical imports are delayed until the user actually converts.
            from vectorizer import image_to_svg

            stats = image_to_svg(input_file, output_file, quality=quality)
            elapsed = time.perf_counter() - started
            self.after(0, self._conversion_ok, stats, elapsed)
        except VectorizationError as exc:
            self.after(0, self._conversion_failed, str(exc))
        except Exception as exc:
            self.after(0, self._conversion_failed, f'Error inesperado: {exc}')

    def _conversion_ok(self, stats: dict, elapsed: float) -> None:
        self.progress.stop()
        self.convert_button.config(state='normal')
        self.open_svg_button.config(state='normal')
        self.open_folder_button.config(state='normal')
        self.status.config(
            text=(
                'Conversion terminada correctamente.\n'
                f'Contornos: {stats["contours_written"]}  |  Tiempo: {elapsed:.1f} s\n'
                f'Archivo: {Path(stats["output"]).name}'
            )
        )
        messagebox.showinfo('Conversion terminada', 'El archivo SVG se creo correctamente.')

    def _conversion_failed(self, message: str) -> None:
        self.progress.stop()
        self.convert_button.config(state='normal')
        self.status.config(text='No fue posible completar la conversion.')
        messagebox.showerror('Error de conversion', message)

    def open_svg(self) -> None:
        if self.output_file and self.output_file.exists():
            self._open_path(self.output_file)

    def open_folder(self) -> None:
        if self.output_file:
            folder = self.output_file.parent
            if sys.platform.startswith('win'):
                subprocess.Popen(['explorer', str(folder)])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(folder)])
            else:
                subprocess.Popen(['xdg-open', str(folder)])

    @staticmethod
    def _open_path(path: Path) -> None:
        if sys.platform.startswith('win'):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', str(path)])
        else:
            subprocess.Popen(['xdg-open', str(path)])



def _close_boot_splash() -> None:
    try:
        import pyi_splash  # type: ignore
        pyi_splash.close()
    except Exception:
        pass


def run_app() -> None:
    app = SvgConverterApp()
    # Force the main window to be painted before closing the loading screen.
    app.update_idletasks()
    app.update()
    _close_boot_splash()
    app.mainloop()


if __name__ == '__main__':
    run_app()
