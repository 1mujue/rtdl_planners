import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget,\
    QPlainTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QSplitter, \
    QLabel, QGridLayout, QProgressDialog
from PySide6.QtCore import Slot, Qt, QObject, Signal, QThread, QTimer
from conductor import Conductor

class MyQtWorker(QObject):
    result_ready = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, func):
        super().__init__()
        self.func = func
    
    @Slot()
    def run(self):
        try:
            result = self.func()
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

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
        self.task_input_label = QLabel("Task Input")
        self.task_input = QPlainTextEdit()
        self.task_input.setPlaceholderText("Please enter your task description...")

        self.input_panel = QWidget()
        self.input_layout = QVBoxLayout()
        self.input_layout.addWidget(self.task_input_label)
        self.input_layout.addWidget(self.task_input)
        self.input_panel.setLayout(self.input_layout)

        # output region
        self.output_label = QLabel("Artifacts / Outputs")

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
        self.out_tabs.addTab(self.system_log_view, "System Log")

        self.output_panel = QWidget()
        self.output_layout = QVBoxLayout()
        self.output_layout.addWidget(self.output_label)
        self.output_layout.addWidget(self.out_tabs)
        self.output_panel.setLayout(self.output_layout)

        self.task_input_label.setObjectName("sectionTitle")
        self.output_label.setObjectName("sectionTitle")

        self.input_panel.setObjectName("workPanel")
        self.output_panel.setObjectName("workPanel")
        
        # button region
        self.action_layout = QHBoxLayout()

        # these are related with RTDL, or frontend.
        self.get_state_button = QPushButton("get world state")
        self.get_state_button.clicked.connect(self.on_get_world_state)

        self.set_rtdl_button = QPushButton("set RTDL")
        self.set_rtdl_button.clicked.connect(self.on_set_rtdl)

        self.gen_rtdl_button = QPushButton("plan RTDL")
        self.gen_rtdl_button.clicked.connect(self.on_gen_rtdl)

        self.compile_rtdl_button = QPushButton("compile RTDL")
        self.compile_rtdl_button.clicked.connect(self.on_compile_rtdl)

        # these are related with execution, or backend.
        self.build_pkg_button = QPushButton("build")
        self.build_pkg_button.clicked.connect(self.on_build_pkg)

        self.run_pkg_button = QPushButton("run")
        self.run_pkg_button.clicked.connect(self.on_run_pkg)

        self.visualize_button = QPushButton("visualize BT")
        self.visualize_button.clicked.connect(self.on_visualize_bt)

        # to make frontend and backend clear, we create a group!
        self.planning_group = QGroupBox("Planning")
        self.planning_layout = QGridLayout()
        self.execution_group = QGroupBox("Execution")
        self.execution_layout = QHBoxLayout()

        self.planning_layout.addWidget(self.get_state_button, 0, 0)
        self.planning_layout.addWidget(self.set_rtdl_button, 0, 1)
        self.planning_layout.addWidget(self.gen_rtdl_button, 1, 0)
        self.planning_layout.addWidget(self.compile_rtdl_button, 1, 1)

        self.execution_layout.addWidget(self.build_pkg_button)
        self.execution_layout.addWidget(self.run_pkg_button)
        self.execution_layout.addWidget(self.visualize_button)

        self.planning_group.setLayout(self.planning_layout)
        self.execution_group.setLayout(self.execution_layout)

        self.action_layout.addWidget(self.planning_group)
        self.action_layout.addWidget(self.execution_group)
    
        # add these components to main layout.
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.input_panel)
        self.main_splitter.addWidget(self.output_panel)
        self.main_splitter.setSizes([180, 420])
                
        self.main_layout.addLayout(self.action_layout)
        self.main_layout.addWidget(self.main_splitter)

        self.main_layout.setContentsMargins(16, 16, 12, 12)
        self.main_layout.setSpacing(11)

        # the backend.
        self.conductor = Conductor()

        # the style.
        self.setStyleSheet("""
        QMainWindow {
            background: #f4f6fb;
        }

        QPlainTextEdit {
            background: #ffffff;
            color: #1f2937;
            border: 1px solid #eef2f7;
            border-radius: 10px;
            padding: 10px;
            font-size: 13px;
            selection-background-color: #cfe0ff;
            selection-color: #111827;
        }
        
        QPlainTextEdit[placeholderText]:empty {
            color: #94a3b8;
        }

        QPushButton {
            background: #2f6fed;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            min-height: 34px;
            font-weight: 600;
        }

        QPushButton:hover {
            background: #255ed0;
        }

        QPushButton:pressed {
            background: #1e4fb1;
        }

        QTabWidget::pane {
            background: white;
            border: 1px solid #eef2f7;
            border-radius: 10px;
            top: -1px;
        }

        QTabBar::tab {
            background: #dfe6f3;
            color: #334155;
            border: 1px solid #c7d0e0;
            padding: 8px 16px;
            margin-right: 4px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }

        QTabBar::tab:selected {
            background: white;
            color: #111827;
            font-weight: 700;
            border-bottom-color: white;
        }

        QTabBar::tab:hover:!selected {
            background: #d3dceb;
        }
                           
        QGroupBox {
            border: 1px solid #cfd6e6;
            border-radius: 10px;
            margin-top: 12px;
            padding: 12px 10px 10px 10px;
            font-weight: 700;
            color: #334155;
            background: #ffffff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px 0 4px;
        }
                           
        QLabel#sectionTitle {
            color: #0f172a;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 4px;
        }
                           
        QWidget#workPanel {
            background: #ffffff;
            border: 1px solid #d7dbe7;
            border-radius: 12px;
        }
        """)

        self.system_log_view.setStyleSheet("""
            background: #0f172a;
            color: #e5e7eb;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 10px;
            font-size: 13px;
        """)

    def center_wait_dialog(self):
        if not hasattr(self, "wait_dialog") or self.wait_dialog is None:
            return

        center_point = self.mapToGlobal(self.rect().center())
        dialog_rect = self.wait_dialog.frameGeometry()
        dialog_rect.moveCenter(center_point)
        self.wait_dialog.move(dialog_rect.topLeft())
    
    def start_blocking_task(self, title, func, on_result) -> None:
        self.wait_dialog = QProgressDialog(title, None, 0, 0, self)
        self.wait_dialog.setWindowTitle("Please wait")
        self.wait_dialog.setWindowModality(Qt.WindowModal)
        self.wait_dialog.setCancelButton(None)
        self.wait_dialog.setMinimumDuration(0)
        self.wait_dialog.setAutoClose(False)
        self.wait_dialog.setAutoReset(False)

        self.wait_dialog.setWindowFlag(Qt.CustomizeWindowHint, True)
        self.wait_dialog.setWindowFlag(Qt.WindowTitleHint, True)
        self.wait_dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.wait_dialog.adjustSize()
        self.wait_dialog.show()
        QTimer.singleShot(0, self.center_wait_dialog)

        self.worker_thread = QThread(self)
        self.worker = MyQtWorker(func)

        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.result_ready.connect(on_result)
        self.worker.error_occurred.connect(self.on_background_error)

        self.worker.finished.connect(self.wait_dialog.close)
        self.worker.finished.connect(self.worker_thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    @Slot(str)
    def on_background_error(self, message):
        self.system_log_view.appendPlainText("[ERROR]")
        self.system_log_view.appendPlainText(message)

    @Slot()
    def on_gen_rtdl(self) -> None:
        result = self.conductor.plan_rtdl(self.task_input.toPlainText())
        self.rtdl_out_view.setPlainText("The plan result(including RTDL):")
        self.rtdl_out_view.appendPlainText("The plan summary:\n" + result["plan_summary"])
        self.rtdl_out_view.appendPlainText("The assumption: ")
        for ass in result["assumptions"]:
            self.rtdl_out_view.appendPlainText(ass)
        self.rtdl_out_view.appendPlainText("The RTDL: \n" + result["rtdl"])

        self.out_tabs.setCurrentIndex(1)

    @Slot()
    def on_get_world_state(self) -> None:
        world_state = self.conductor.get_world_state()
        self.world_state_view.setPlainText("The world state: \n" + world_state)

        self.out_tabs.setCurrentIndex(0)

    @Slot()
    def on_compile_rtdl(self) -> None:
        self.start_blocking_task(
            "Compiling RTDL, please wait...",
            self.conductor.compile_rtdl,
            self.on_compile_rtdl_finished
        )

    @Slot(object)
    def on_compile_rtdl_finished(self, result) -> None:
        bt_xml, stdout, stderr = result
        self.bt_xml_view.setPlainText(bt_xml)
        self.system_log_view.appendPlainText("Compile standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Compile standard error: \n" + stderr)
        self.out_tabs.setCurrentIndex(2)

    @Slot()
    def on_build_pkg(self) -> None:
        self.start_blocking_task(
            "Building package, please wait...",
            self.conductor.build_ros2_bt_pkg,
            self.on_build_pkg_finished
        )

    @Slot(object)
    def on_build_pkg_finished(self, result) -> None:
        stdout, stderr = result
        self.system_log_view.appendPlainText("Build pkg standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Build pkg standard error: \n" + stderr)
        self.out_tabs.setCurrentIndex(3)

    @Slot()
    def on_run_pkg(self) -> None:
        self.start_blocking_task(
            "Running the task, please wait...",
            self.conductor.run,
            self.on_run_pkg_finished
        )
       

    @Slot(object)
    def on_run_pkg_finished(self, result) -> None:
        stdout, stderr = result
        self.system_log_view.appendPlainText("Run standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Run standard error: \n" + stderr)
        self.out_tabs.setCurrentIndex(3)

    @Slot()
    def on_visualize_bt(self) -> None:
        stdout, stderr = self.conductor.visualize_bt()
        self.system_log_view.appendPlainText("Visualize standard output: \n" + stdout)
        self.system_log_view.appendPlainText("Visualize standard error: \n" + stderr)

        self.out_tabs.setCurrentIndex(3)

    @Slot()
    def on_set_rtdl(self) -> None:
        self.conductor.last_rtdl = self.task_input.toPlainText()
        self.rtdl_out_view.appendPlainText("Set RTDL successfully, the content: ")
        self.rtdl_out_view.appendPlainText(self.conductor.last_rtdl)

        self.out_tabs.setCurrentIndex(1)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
