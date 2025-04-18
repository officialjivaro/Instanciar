# appdata/logic/main_window.py
import threading
import webbrowser
from appdata.gui.instance_manager import GuiInstanceManager
from appdata.logic.install import install_instanciar

class MainWindowLogic:
    def __init__(self, manager):
        self.manager = manager

    def install_app(self):
        install_instanciar()

    def refresh_list(self, list_widget):
        list_widget.clear()
        for i in self.manager.data:
            list_widget.addItem(i["name"])

    def on_rows_moved(self, list_widget):
        order = []
        for i in range(list_widget.count()):
            order.append(list_widget.item(i).text())
        self.manager.rearrange_instances(order)

    def create_instance(self, parent, list_widget):
        e = GuiInstanceManager(self.manager, None, parent)
        e.exec()
        self.refresh_list(list_widget)

    def edit_instance(self, parent, list_widget):
        it = list_widget.currentItem()
        if it:
            e = GuiInstanceManager(self.manager, it.text(), parent)
            e.exec()
            self.refresh_list(list_widget)

    def delete_instance(self, list_widget):
        it = list_widget.currentItem()
        if it:
            self.manager.delete_instance(it.text())
            self.refresh_list(list_widget)

    def launch_instance_in_thread(self, list_widget):
        it = list_widget.currentItem()
        if it:
            name = it.text()
            t = threading.Thread(
                target=self.manager.launch_instance,
                args=(name, "chrome", None),
                daemon=True
            )
            t.start()

    def open_commands(self):
        webbrowser.open("https://www.jivaro.net/downloads/programs/info/instanciar")

    def open_about_jivaro(self):
        webbrowser.open("https://www.jivaro.net/")

    def open_discord(self):
        webbrowser.open("https://discord.gg/GDfX5BFGye")

    def open_proxies(self):
        webbrowser.open("https://jivaro.net/content/blog/the-best-affordable-proxy-providers")