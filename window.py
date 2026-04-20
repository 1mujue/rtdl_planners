import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget,\
    QPlainTextEdit, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Slot
from conductor import Conductor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RTDL Planner GUI")
        self.resize(800, 600)
        self.center_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.center_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.center_widget)

        # input region
        self.task_input = QPlainTextEdit()
        self.task_input.setPlaceholderText("Please enter your task description...")

        # output region
        self.rtdl_out_view = QPlainTextEdit()
        self.rtdl_out_view.setReadOnly(True)
        self.rtdl_out_view.setPlaceholderText("The generated RTDL will be showed here...")

        self.world_state_view = QPlainTextEdit()
        self.world_state_view.setReadOnly(True)
        self.world_state_view.setPlaceholderText("The world state will be showed here...")
        
        self.bt_xml_view = QPlainTextEdit()
        self.bt_xml_view.setReadOnly(True)
        self.bt_xml_view.setPlaceholderText("The compiled xml will be showed here...")

        self.system_log_view = QPlainTextEdit()
        self.system_log_view.setReadOnly(True)
        self.system_log_view.setPlaceholderText("The Build/Run log will be showed here...")
        
        self.out_tabs = QTabWidget()
        self.out_tabs.addTab(self.world_state_view, "World State")
        self.out_tabs.addTab(self.rtdl_out_view, "RTDL")
        self.out_tabs.addTab(self.bt_xml_view, "BT XML")
        self.out_tabs.addTab(self.system_log_view,"System Log")
        
        # button region
        self.button_layout = QHBoxLayout()

        self.get_state_button = QPushButton("get world state")
        self.get_state_button.clicked.connect(self.on_get_world_state)

        self.gen_rtdl_button = QPushButton("plan RTDL")
        self.gen_rtdl_button.clicked.connect(self.on_gen_rtdl)

        self.compile_rtdl_button = QPushButton("compile RTDL")
        self.compile_rtdl_button.clicked.connect(self.on_compile_rtdl)

        self.build_pkg_button = QPushButton("build")
        self.build_pkg_button.clicked.connect(self.on_build_pkg)

        self.run_pkg_button = QPushButton("run")
        self.run_pkg_button.clicked.connect(self.on_run_pkg)

        self.visualize_button = QPushButton("visualize BT")
        self.visualize_button.clicked.connect(self.on_visualize_bt)

        self.set_rtdl_button = QPushButton("set RTDL")
        self.set_rtdl_button.clicked.connect(self.on_set_rtdl)

        self.button_layout.addWidget(self.get_state_button)
        self.button_layout.addWidget(self.gen_rtdl_button)  
        self.button_layout.addWidget(self.compile_rtdl_button)
        self.button_layout.addWidget(self.build_pkg_button)
        self.button_layout.addWidget(self.run_pkg_button)
        self.button_layout.addWidget(self.visualize_button)
        self.button_layout.addWidget(self.set_rtdl_button)
        
        # add these components to main layout.
        self.main_layout.addWidget(self.task_input)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.out_tabs)

        self.conductor = Conductor()
    
    @Slot()
    def on_gen_rtdl(self) -> None:
        result = self.conductor.plan_rtdl(self.task_input.toPlainText())
        self.rtdl_out_view.setPlainText("The plan result(including RTDL):")
        self.rtdl_out_view.appendPlainText("The plan summary:\n" + result["plan_summary"])
        self.rtdl_out_view.appendPlainText("The assumption: ")
        for ass in result["assumptions"]:
            self.rtdl_out_view.appendPlainText(ass)
        self.rtdl_out_view.appendPlainText("The RTDL: \n" + result["rtdl"])

    @Slot()
    def on_get_world_state(self) -> None:
        world_state = self.conductor.get_world_state()
        self.world_state_view.setPlainText("The world state: \n" + world_state)

    @Slot()
    def on_compile_rtdl(self) -> None:
        bt_xml, stdout, stderr = self.conductor.compile_rtdl()
        self.bt_xml_view.setPlainText(bt_xml)
        self.system_log_view.appendPlainText("Compile standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Compile standard error: \n" + stderr)

    @Slot()
    def on_build_pkg(self) -> None:
        stdout, stderr = self.conductor.build_ros2_bt_pkg()
        self.system_log_view.appendPlainText("Build pkg standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Build pkg standard error: \n" + stderr)

    @Slot()
    def on_run_pkg(self) -> None:
        stdout, stderr = self.conductor.run()
        self.system_log_view.appendPlainText("Run standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Run standard error: \n" + stderr)

    @Slot()
    def on_visualize_bt(self) -> None:
        stdout, stderr = self.conductor.visualize_bt()
        self.system_log_view.appendPlainText("Visualize standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Visualize standard error: \n" + stderr)

    @Slot()
    def on_set_rtdl(self) -> None:
        self.conductor.last_rtdl = self.task_input.toPlainText()
        self.system_log_view.appendPlainText("Set RTDL successfully, the content: ")
        self.system_log_view.appendPlainText(self.conductor.last_rtdl)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
