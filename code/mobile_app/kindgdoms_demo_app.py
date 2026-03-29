from __future__ import annotations

import os
import tempfile
import importlib
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager


class RootScreenManager(ScreenManager):
	pass

class StartScreen(Screen):
	pass

class GalleryScreen(Screen):
	pass

class ProcessedReviewScreen(Screen):
	pass

class GridScreen(Screen):
	pass

class ResultScreen(Screen):
	pass


class KingdomsApp(App):
	selected_image_path = StringProperty("")
	processed_image_path = StringProperty("")
	processing_status = StringProperty("Waiting for image")
	result_text = StringProperty("")
	selected_symbols = ListProperty([])


	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._pending_gallery_selection = ""
		self._temp_camera_file = ""


	def build(self):
		Builder.load_file(str(Path(__file__).with_name("kingdomsdemo.kv")))
		return RootScreenManager()


	def on_start(self):
		self._initialize_symbol_grid()


	def _initialize_symbol_grid(self):
		grid = self.root.get_screen("grid").ids.symbol_grid
		grid.clear_widgets()

		defaults = []
		for r in range(5):
			for c in range(6):
				defaults.append("e")

		from kivy.uix.textinput import TextInput

		for symbol in defaults:
			cell = TextInput(
				text=symbol,
				multiline=False,
				halign="center",
				font_size="18sp",
			)
			grid.add_widget(cell)


	def take_new_photo(self):
		# On Android, plyer camera requires a path; the app uses a temporary file.
		suffix = ".jpg"
		temp_dir = tempfile.gettempdir()
		self._temp_camera_file = os.path.join(temp_dir, f"kivy_capture_{os.getpid()}{suffix}")

		try:
			camera = importlib.import_module("plyer").camera
			camera.take_picture(filename=self._temp_camera_file, on_complete=self._on_camera_complete)
		except Exception:
			self.processing_status = "Camera not available. Use gallery option."


	def _on_camera_complete(self, file_path):
		if not file_path:
			self.processing_status = "Photo capture canceled."
			return
		self.selected_image_path = file_path
		self.run_first_processing()


	def on_gallery_selection(self, selection):
		self._pending_gallery_selection = selection[0] if selection else ""


	def use_selected_from_gallery(self):
		if not self._pending_gallery_selection:
			self.processing_status = "No image selected yet."
			return

		self.selected_image_path = self._pending_gallery_selection
		self.run_first_processing()


	def run_first_processing(self):
		if not self.selected_image_path:
			self.processing_status = "No input image available."
			return

		# Placeholder for first image-processing stage.
		self.processing_status = "First processing complete. Please review image."
		self.processed_image_path = self.selected_image_path
		self.root.current = "processed_review"


	def run_second_processing(self):
		# Placeholder for second image-processing stage.
		self.processing_status = "Second processing complete."
		self._initialize_symbol_grid()
		self.root.current = "grid"


	def approve_grid_and_calculate(self):
		grid = self.root.get_screen("grid").ids.symbol_grid
		self.selected_symbols = [
			(child.text.strip()[:1] if child.text.strip() else "?")
			for child in reversed(grid.children)
		]

		symbol_count = len([s for s in self.selected_symbols if s != "?"])
		unique_symbols = len(set(self.selected_symbols))

		# Placeholder for final calculation output.
		self.result_text = (
			"Calculated output\n\n"
			f"Filled cells: {symbol_count}/30\n"
			f"Unique symbols: {unique_symbols}\n"
			f"Sample row 1: {' '.join(self.selected_symbols[:6])}"
		)
		self.root.current = "result"


	def reset_to_start(self, keep_temp):
		self.selected_image_path = ""
		self.processed_image_path = ""
		self.processing_status = "Waiting for image"
		self.result_text = ""
		self._pending_gallery_selection = ""

		if not keep_temp and self._temp_camera_file and Path(self._temp_camera_file).exists():
			try:
				Path(self._temp_camera_file).unlink()
			except OSError:
				pass
		self._temp_camera_file = ""

		# Delay screen switch to avoid race with on_release events.
		Clock.schedule_once(lambda _dt: self._go_to_start(), 0)


	def _go_to_start(self):
		self.root.current = "start"



if __name__ == "__main__":
	KingdomsApp().run()
