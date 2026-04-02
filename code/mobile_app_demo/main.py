from kivy.app import App
from kivy.uix.boxlayout import BoxLayout


class HelloWorldApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        return layout


if __name__ == '__main__':
    HelloWorldApp().run()
