# type: ignore
# flake8: noqa
"""
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import io
import json
import logging
import os
import threading
import time
import traceback

import remi
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

import remi.gui as gui
from remi import App, start

API_HOST = (
    "http://localhost:5000" if "API_HOST" not in os.environ else os.environ["API_HOST"]
)


class RefreshImageWidget(remi.gui.Image):
    def __init__(self, url=None, **kwargs):
        self.app_instance = None
        super().__init__("/res:logo.jpg", **kwargs)
        self.frame_index = 0
        self._buf = None
        self.url = url

    def search_app_instance(self, node):
        if issubclass(node.__class__, remi.server.App):
            return node
        if not hasattr(node, "get_parent"):
            return None
        return self.search_app_instance(node.get_parent())

    def load(self):
        try:
            data = requests.get(self.url)
            self._buf = io.BytesIO(data.content)
            self.refresh()
        except requests.ConnectionError:
            logger.info("couldn't reload")

    def refresh(self, *args):
        if self.app_instance == None:
            self.app_instance = self.search_app_instance(self)
            if self.app_instance == None:
                return
        self.frame_index = self.frame_index + 1
        self.app_instance.execute_javascript(
            """
            url = '/%(id)s/get_image_data?index=%(frame_index)s';

            xhr = null;
            xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.responseType = 'blob'
            xhr.onload = function(e){
                urlCreator = window.URL || window.webkitURL;
                urlCreator.revokeObjectURL(document.getElementById('%(id)s').src);
                imageUrl = urlCreator.createObjectURL(this.response);
                document.getElementById('%(id)s').src = imageUrl;
            }
            xhr.send();
            """
            % {"id": id(self), "frame_index": self.frame_index}
        )

    def get_image_data(self, index=0):
        try:
            self._buf.seek(0)
            headers = {"Content-type": "image/jpeg"}
            return [self._buf.read(), headers]
        except:
            print(traceback.format_exc())
        return None, None


class MyApp(App):
    def __init__(self, *args, recorder=None):
        super().__init__(*args)

    def idle(self):
        if hasattr(self, "data_table"):
            i = 0
            for k, v in self.data.items():
                i += 1
                self.data_table.item_at(i, 0).set_text(str(k))
                self.data_table.item_at(i, 1).set_text(str(v))
        else:
            logger.info("no counter")

    def _get_list_from_app_args(self, name):
        return super()._get_list_from_app_args(name)

    def preview_screen(self) -> gui.Widget:
        self.to_review = gui.Button("review tracks")
        tabs = gui.HBox(
            children=[self.to_review],
            style={"margin": "0px auto", "background-color": "lightgray"},
        )

        self.stop_flag = False

        self.img = RefreshImageWidget(
            f"{API_HOST}/v1/preview.jpeg", margin="10px", width=0, height=0
        )
        self.video = gui.VideoPlayer(width=806, height=600)
        self.check = gui.CheckBoxLabel(
            "Preview", False, width=200, height=30, margin="10px"
        )

        self.data_table = gui.TableWidget(8, 2)
        self.data_table.item_at(0, 0).set_text("k")
        self.data_table.item_at(0, 1).set_text("v")

        self.check.onchange.do(self.on_check_change)
        video_container = gui.VBox(
            [tabs, self.img, self.check, self.data_table], margin="8pt auto"
        )

        self.refresh = False
        self.running = True
        return video_container

    def review_screen(self) -> gui.Widget:
        self.to_preview = gui.Button("change page")
        reviewcontainer = gui.HBox(
            children=[self.to_preview],
            style={"margin": "0px auto", "background-color": "lightgray"},
        )
        return reviewcontainer

    def main(self):
        self.data = {}
        # self.recorder = Recorder()

        self.previewcontainer = self.preview_screen()
        self.reviewcontainer = self.review_screen()
        self.to_review.onclick.do(self.set_different_root_widget, self.reviewcontainer)
        self.to_preview.onclick.do(
            self.set_different_root_widget, self.previewcontainer
        )

        t = threading.Thread(target=self.update)
        t.start()

        return self.reviewcontainer

    def set_different_root_widget(self, emitter, page_to_be_shown):
        self.set_root_widget(page_to_be_shown)
        self.check.set_value(False)
        self.refresh = False

    def update_data(self):
        try:
            current = requests.get(f"{API_HOST}/v1/state")
            self.data = json.loads(current.content)
        except requests.RequestException:
            pass

    def update(self):
        lasttime: int = 0
        while self.running:
            time.sleep(0.1)
            if self.refresh and lasttime != int(time.time()):
                self.img.load()
                lasttime = int(time.time())
            self.update_data()

    def __main(self):
        # the margin 0px auto centers the main container
        verticalContainer = gui.Container(
            width=540,
            margin="0px auto",
            style={"display": "block", "overflow": "hidden"},
        )

        horizontalContainer = gui.Container(
            width="100%",
            layout_orientation=gui.Container.LAYOUT_HORIZONTAL,
            margin="0px",
            style={"display": "block", "overflow": "auto"},
        )

        subContainerLeft = gui.Container(
            width=320,
            style={"display": "block", "overflow": "auto", "text-align": "center"},
        )
        self.img = gui.Image("/res:logo.png", height=100, margin="10px")
        self.img.onclick.do(self.on_img_clicked)

        self.table = gui.Table.new_from_list(
            [
                ("ID", "First Name", "Last Name"),
                ("101", "Danny", "Young"),
                ("102", "Christine", "Holand"),
                ("103", "Lars", "Gordon"),
                ("104", "Roberto", "Robitaille"),
                ("105", "Maria", "Papadopoulos"),
            ],
            width=300,
            height=200,
            margin="10px",
        )
        self.table.on_table_row_click.do(self.on_table_row_click)

        # the arguments are	width - height - layoutOrientationOrizontal
        subContainerRight = gui.Container(
            style={
                "width": "220px",
                "display": "block",
                "overflow": "auto",
                "text-align": "center",
            }
        )
        self.count = 0
        self.counter = gui.Label("", width=200, height=30, margin="10px")

        self.lbl = gui.Label("This is a LABEL!", width=200, height=30, margin="10px")

        self.bt = gui.Button("Press me!", width=200, height=30, margin="10px")
        # setting the listener for the onclick event of the button
        self.bt.onclick.do(self.on_button_pressed)

        self.txt = gui.TextInput(width=200, height=30, margin="10px")
        self.txt.set_text("This is a TEXTAREA")
        self.txt.onchange.do(self.on_text_area_change)

        self.spin = gui.SpinBox(1, 0, 100, width=200, height=30, margin="10px")
        self.spin.onchange.do(self.on_spin_change)

        self.progress = gui.Progress(1, 100, width=200, height=5)

        self.check = gui.CheckBoxLabel(
            "Label checkbox", True, width=200, height=30, margin="10px"
        )
        self.check.onchange.do(self.on_check_change)

        self.btInputDiag = gui.Button(
            "Open InputDialog", width=200, height=30, margin="10px"
        )
        self.btInputDiag.onclick.do(self.open_input_dialog)

        self.btFileDiag = gui.Button(
            "File Selection Dialog", width=200, height=30, margin="10px"
        )
        self.btFileDiag.onclick.do(self.open_fileselection_dialog)

        self.btUploadFile = gui.FileUploader("./", width=200, height=30, margin="10px")
        self.btUploadFile.onsuccess.do(self.fileupload_on_success)
        self.btUploadFile.onfailed.do(self.fileupload_on_failed)

        items = ("Danny Young", "Christine Holand", "Lars Gordon", "Roberto Robitaille")
        self.listView = gui.ListView.new_from_list(
            items, width=300, height=120, margin="10px"
        )
        self.listView.onselection.do(self.list_view_on_selected)

        self.link = gui.Link(
            "http://localhost:8081",
            "A link to here",
            width=200,
            height=30,
            margin="10px",
        )

        self.dropDown = gui.DropDown.new_from_list(
            ("DropDownItem 0", "DropDownItem 1"), width=200, height=20, margin="10px"
        )
        self.dropDown.onchange.do(self.drop_down_changed)
        self.dropDown.select_by_value("DropDownItem 0")

        self.slider = gui.Slider(10, 0, 100, 5, width=200, height=20, margin="10px")
        self.slider.onchange.do(self.slider_changed)

        self.colorPicker = gui.ColorPicker(
            "#ffbb00", width=200, height=20, margin="10px"
        )
        self.colorPicker.onchange.do(self.color_picker_changed)

        self.date = gui.Date("2015-04-13", width=200, height=20, margin="10px")
        self.date.onchange.do(self.date_changed)

        self.video = gui.Widget(_type="iframe", width=290, height=200, margin="10px")
        self.video.attributes[
            "src"
        ] = "https://drive.google.com/file/d/0B0J9Lq_MRyn4UFRsblR3UTBZRHc/preview"
        self.video.attributes["width"] = "100%"
        self.video.attributes["height"] = "100%"
        self.video.attributes["controls"] = "true"
        self.video.style["border"] = "none"

        self.tree = gui.TreeView(width="100%", height=300)
        ti1 = gui.TreeItem("Item1")
        ti2 = gui.TreeItem("Item2")
        ti3 = gui.TreeItem("Item3")
        subti1 = gui.TreeItem("Sub Item1")
        subti2 = gui.TreeItem("Sub Item2")
        subti3 = gui.TreeItem("Sub Item3")
        subti4 = gui.TreeItem("Sub Item4")
        subsubti1 = gui.TreeItem("Sub Sub Item1")
        subsubti2 = gui.TreeItem("Sub Sub Item2")
        subsubti3 = gui.TreeItem("Sub Sub Item3")
        self.tree.append([ti1, ti2, ti3])
        ti2.append([subti1, subti2, subti3, subti4])
        subti4.append([subsubti1, subsubti2, subsubti3])

        # appending a widget to another, the first argument is a string key
        subContainerRight.append(
            [
                self.counter,
                self.lbl,
                self.bt,
                self.txt,
                self.spin,
                self.progress,
                self.check,
                self.btInputDiag,
                self.btFileDiag,
            ]
        )
        # use a defined key as we replace this widget later
        fdownloader = gui.FileDownloader(
            "download test", "../remi/res/logo.png", width=200, height=30, margin="10px"
        )
        subContainerRight.append(fdownloader, key="file_downloader")
        subContainerRight.append(
            [
                self.btUploadFile,
                self.dropDown,
                self.slider,
                self.colorPicker,
                self.date,
                self.tree,
            ]
        )
        self.subContainerRight = subContainerRight

        subContainerLeft.append(
            [self.img, self.table, self.listView, self.link, self.video]
        )

        horizontalContainer.append([subContainerLeft, subContainerRight])

        menu = gui.Menu(width="100%", height="30px")
        m1 = gui.MenuItem("File", width=100, height=30)
        m2 = gui.MenuItem("View", width=100, height=30)
        m2.onclick.do(self.menu_view_clicked)
        m11 = gui.MenuItem("Save", width=100, height=30)
        m12 = gui.MenuItem("Open", width=100, height=30)
        m12.onclick.do(self.menu_open_clicked)
        m111 = gui.MenuItem("Save", width=100, height=30)
        m111.onclick.do(self.menu_save_clicked)
        m112 = gui.MenuItem("Save as", width=100, height=30)
        m112.onclick.do(self.menu_saveas_clicked)
        m3 = gui.MenuItem("Dialog", width=100, height=30)
        m3.onclick.do(self.menu_dialog_clicked)

        menu.append([m1, m2, m3])
        m1.append([m11, m12])
        m11.append([m111, m112])

        menubar = gui.MenuBar(width="100%", height="30px")
        menubar.append(menu)

        verticalContainer.append([menubar, horizontalContainer])

        # this flag will be used to stop the display_counter Timer
        self.stop_flag = False

        # kick of regular display of counter
        self.display_counter()

        # returning the root widget
        return verticalContainer

    # listener function
    def on_img_clicked(self, widget):
        self.lbl.set_text("Image clicked!")

    def on_table_row_click(self, table, row, item):
        self.lbl.set_text("Table Item clicked: " + item.get_text())

    def on_button_pressed(self, widget):
        self.lbl.set_text("Button pressed! ")
        self.bt.set_text("Hi!")

    def on_text_area_change(self, widget, newValue):
        self.lbl.set_text("Text Area value changed!")

    def on_spin_change(self, widget, newValue):
        self.lbl.set_text("SpinBox changed, new value: " + str(newValue))

    def on_check_change(self, widget, newValue):
        self.refresh = newValue
        if self.refresh:
            self.img.set_size(806, 600)
        else:
            self.img.set_size(0, 0)

    def open_input_dialog(self, widget):
        self.inputDialog = gui.InputDialog(
            "Input Dialog", "Your name?", initial_value="type here", width=500
        )
        self.inputDialog.confirm_value.do(self.on_input_dialog_confirm)

        # here is returned the Input Dialog widget, and it will be shown
        self.inputDialog.show(self)

    def on_input_dialog_confirm(self, widget, value):
        self.lbl.set_text("Hello " + value)

    def open_fileselection_dialog(self, widget):
        self.fileselectionDialog = gui.FileSelectionDialog(
            "File Selection Dialog", "Select files and folders", False, "."
        )
        self.fileselectionDialog.confirm_value.do(self.on_fileselection_dialog_confirm)

        # here is returned the Input Dialog widget, and it will be shown
        self.fileselectionDialog.show(self)

    def on_fileselection_dialog_confirm(self, widget, filelist):
        # a list() of filenames and folders is returned
        self.lbl.set_text("Selected files: %s" % ",".join(filelist))
        if len(filelist):
            f = filelist[0]
            # replace the last download link
            fdownloader = gui.FileDownloader(
                "download selected", f, width=200, height=30
            )
            self.subContainerRight.append(fdownloader, key="file_downloader")

    def list_view_on_selected(self, widget, selected_item_key):
        """The selection event of the listView, returns a key of the clicked event.
        You can retrieve the item rapidly
        """
        self.lbl.set_text(
            "List selection: " + self.listView.children[selected_item_key].get_text()
        )

    def drop_down_changed(self, widget, value):
        self.lbl.set_text("New Combo value: " + value)

    def slider_changed(self, widget, value):
        self.lbl.set_text("New slider value: " + str(value))

    def color_picker_changed(self, widget, value):
        self.lbl.set_text("New color value: " + value)

    def date_changed(self, widget, value):
        self.lbl.set_text("New date value: " + value)

    def menu_save_clicked(self, widget):
        self.lbl.set_text("Menu clicked: Save")

    def menu_saveas_clicked(self, widget):
        self.lbl.set_text("Menu clicked: Save As")

    def menu_open_clicked(self, widget):
        self.lbl.set_text("Menu clicked: Open")

    def menu_view_clicked(self, widget):
        self.lbl.set_text("Menu clicked: View")

    def fileupload_on_success(self, widget, filename):
        self.lbl.set_text("File upload success: " + filename)

    def fileupload_on_failed(self, widget, filename):
        self.lbl.set_text("File upload failed: " + filename)

    def on_close(self):
        """Overloading App.on_close event to stop the Timer."""
        self.stop_flag = True
        self.running = False

        super().on_close()


def main():
    start(
        MyApp,
        debug=True,
        address="0.0.0.0",
        port=8081,
        start_browser=True,
        multiple_instance=True,
    )


if __name__ == "__main__":
    # starts the webserver
    # optional parameters
    # start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
    main()
