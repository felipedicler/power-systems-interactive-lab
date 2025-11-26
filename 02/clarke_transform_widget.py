import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QSlider, QLabel,
    QPushButton, QCheckBox, QDoubleSpinBox, QHBoxLayout, QGroupBox, QFrame,
    QSizePolicy, QSplitter, QRadioButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette, QFont
import pyqtgraph as pg

# --- Styling & Parameters ---

# Modern Dark Theme Colors
COLOR_BG = "#1e1e1e"
COLOR_PANEL = "#252526"
COLOR_TEXT = "#d4d4d4"
COLOR_ACCENT = "#007acc"
COLOR_ACCENT_HOVER = "#0098ff"
COLOR_BORDER = "#3e3e42"

# Plot Colors (Neon/Bright for dark background)
COLOR_POS_SEQ = ['#FF5555', '#55FF55', '#5555FF']  # Red, Green, Blue (Bright)
COLOR_NEG_SEQ = ['#FF55FF', '#55FFFF', '#FFFF55']  # Magenta, Cyan, Yellow (Bright)
COLOR_RES_POS = '#FFFFFF'
COLOR_RES_NEG = '#AAAAAA'

# Parameters
omega = 2 * np.pi
t = np.linspace(0, 2, 200)
angles = np.array([0, 120, 240]) * np.pi / 180

# Configure PyQtGraph global look
pg.setConfigOption('background', COLOR_BG)
pg.setConfigOption('foreground', COLOR_TEXT)
pg.setConfigOptions(antialias=True)

class ClarkeTransformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clarke Transform Visualization")
        self.resize(1200, 800)
        self.apply_stylesheet()

        # Default amplitudes
        # Default amplitudes
        self.amp_pos_harmonics = [1.0, 0.0, 0.0, 0.0, 0.0] # H1 to H5
        self.amp_neg = 0.1
        self.amp_neg = 0.1

        # Main Layout (Horizontal: Sidebar + Content)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(15)

        # Title in Sidebar
        title_label = QLabel("Controls")
        title_label.setObjectName("SidebarTitle")
        title_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title_label)

        # 1. Playback Controls
        group_playback = QGroupBox("Playback")
        layout_playback = QVBoxLayout()
        
        self.slider_label = QLabel("Time: 0.00 s")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(t)-1)
        self.slider.valueChanged.connect(self.update_plots)

        hbox_buttons = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_all)
        hbox_buttons.addWidget(self.play_button)
        hbox_buttons.addWidget(self.reset_button)

        self.loop_checkbox = QCheckBox("Loop Animation")
        self.loop_checkbox.setChecked(True)

        layout_playback.addWidget(self.slider_label)
        layout_playback.addWidget(self.slider)
        layout_playback.addLayout(hbox_buttons)
        layout_playback.addWidget(self.loop_checkbox)
        group_playback.setLayout(layout_playback)
        sidebar_layout.addWidget(group_playback)

        # 2. Amplitudes
        group_amps = QGroupBox("Amplitudes")
        layout_amps = QGridLayout()
        
        layout_amps.addWidget(QLabel("Positive Sequence Harmonics:"), 0, 0, 1, 2)
        
        self.amp_pos_inputs = []
        for i in range(5):
            h_num = i + 1
            layout_amps.addWidget(QLabel(f"H{h_num}:"), i+1, 0)
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 10.0)
            spin.setValue(self.amp_pos_harmonics[i])
            spin.setSingleStep(0.1)
            spin.valueChanged.connect(self.update_amplitudes)
            layout_amps.addWidget(spin, i+1, 1)
            self.amp_pos_inputs.append(spin)

        layout_amps.addWidget(QLabel("Negative Seq (Fundamental):"), 6, 0)
        self.amp_neg_input = QDoubleSpinBox()
        self.amp_neg_input.setRange(0.0, 10.0)
        self.amp_neg_input.setValue(self.amp_neg)
        self.amp_neg_input.setSingleStep(0.1)
        self.amp_neg_input.valueChanged.connect(self.update_amplitudes)
        layout_amps.addWidget(self.amp_neg_input, 6, 1)

        group_amps.setLayout(layout_amps)
        sidebar_layout.addWidget(group_amps)

        # 3. Transform Type
        group_transform = QGroupBox("Transform Type")
        layout_transform = QVBoxLayout()
        
        self.radio_amp_inv = QRadioButton("Amplitude Invariant (k=2/3)")
        self.radio_amp_inv.toggled.connect(self.update_amplitudes)
        
        self.radio_power_inv = QRadioButton("Power Invariant (k=√2/3)")
        self.radio_power_inv.setChecked(True)
        self.radio_power_inv.toggled.connect(self.update_amplitudes)
        
        layout_transform.addWidget(self.radio_amp_inv)
        layout_transform.addWidget(self.radio_power_inv)
        group_transform.setLayout(layout_transform)
        sidebar_layout.addWidget(group_transform)

        # 3. Visualization Options
        group_viz = QGroupBox("Visualization")
        layout_viz = QVBoxLayout()

        self.decomposition_checkbox = QCheckBox("Decomposition Mode")
        self.decomposition_checkbox.stateChanged.connect(self.update_plots)
        
        self.trajectory_checkbox = QCheckBox("Show Trajectory")
        self.trajectory_checkbox.stateChanged.connect(self.toggle_trajectory)

        self.show_rotating_fields_checkbox = QCheckBox("Show Pos/Neg in Combined")
        self.show_rotating_fields_checkbox.stateChanged.connect(self.update_plots)

        self.extra_trajectory_checkbox = QCheckBox("Trajectory for Extra Fields")
        self.extra_trajectory_checkbox.setEnabled(False)
        self.extra_trajectory_checkbox.stateChanged.connect(self.toggle_extra_trajectory)

        layout_viz.addWidget(self.decomposition_checkbox)
        layout_viz.addWidget(self.trajectory_checkbox)
        layout_viz.addWidget(self.show_rotating_fields_checkbox)
        layout_viz.addWidget(self.extra_trajectory_checkbox)
        group_viz.setLayout(layout_viz)
        sidebar_layout.addWidget(group_viz)

        sidebar_layout.addStretch() # Push everything up
        main_layout.addWidget(sidebar)

        # --- Content Area (Plots) ---
        content_widget = QWidget()
        grid = QGridLayout(content_widget)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setSpacing(10)

        # 1. Combined Field (Phasor ABC) - Top Left
        self.field_combined = self.create_field("Combined Sequence (ABC)")
        grid.addWidget(self.field_combined, 0, 0)

        # 2. Combined Signals (Time Domain ABC) - Top Right
        self.plot_combined = self.create_signal_plot("Signals: Combined (ABC)")
        grid.addWidget(self.plot_combined, 0, 1)

        # 3. Clarke Field (Phasor Alpha-Beta) - Bottom Left
        self.field_clarke = self.create_field("Clarke Transform (αβ)")
        grid.addWidget(self.field_clarke, 1, 0)

        # 4. Clarke Signals (Time Domain Alpha-Beta) - Bottom Right
        self.plot_clarke = self.create_signal_plot("Signals: αβ")
        grid.addWidget(self.plot_clarke, 1, 1)

        # Set stretch factors
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        main_layout.addWidget(content_widget)

        # --- Initialization of Graphics Items ---
        
        # --- ABC Items ---
        # Vectors
        self.lines_combined, self.tips_combined = self.create_vectors(self.field_combined, COLOR_POS_SEQ + COLOR_NEG_SEQ)
        self.resultant_line_combined, self.resultant_tip_combined = self.create_resultant(self.field_combined)

        # Extra rotating fields for combined
        self.extra_line_pos = pg.PlotDataItem(pen=pg.mkPen(COLOR_RES_POS, width=2, style=Qt.DashLine))
        self.extra_tip_pos = pg.ScatterPlotItem(size=10, brush=COLOR_RES_POS)
        self.field_combined.addItem(self.extra_line_pos)
        self.field_combined.addItem(self.extra_tip_pos)

        self.extra_line_neg = pg.PlotDataItem(pen=pg.mkPen(COLOR_RES_NEG, width=2, style=Qt.DashLine))
        self.extra_tip_neg = pg.ScatterPlotItem(size=10, brush=COLOR_RES_NEG)
        self.field_combined.addItem(self.extra_line_neg)
        self.field_combined.addItem(self.extra_tip_neg)

        # Trajectories ABC
        self.trajectory_combined = pg.PlotDataItem(pen=pg.mkPen(COLOR_RES_POS, width=1))
        self.field_combined.addItem(self.trajectory_combined)

        # Extra trajectories ABC
        self.extra_trajectory_pos = pg.PlotDataItem(pen=pg.mkPen(COLOR_RES_POS, width=1, style=Qt.DotLine))
        self.field_combined.addItem(self.extra_trajectory_pos)
        self.extra_trajectory_neg = pg.PlotDataItem(pen=pg.mkPen(COLOR_RES_NEG, width=1, style=Qt.DotLine))
        self.field_combined.addItem(self.extra_trajectory_neg)
        
        # --- Clarke Items ---
        # Vectors (Alpha, Beta)
        # Using Orange for Alpha, Cyan for Beta
        COLOR_ALPHA = '#FFA500'
        COLOR_BETA = '#00FFFF'
        self.lines_clarke, self.tips_clarke = self.create_vectors(self.field_clarke, [COLOR_ALPHA, COLOR_BETA])
        self.resultant_line_clarke, self.resultant_tip_clarke = self.create_resultant(self.field_clarke)
        
        # Trajectory Clarke
        self.trajectory_clarke = pg.PlotDataItem(pen=pg.mkPen(COLOR_RES_POS, width=1))
        self.field_clarke.addItem(self.trajectory_clarke)

        self.traj_points_combined = []
        self.traj_points_extra_pos = []
        self.traj_points_extra_neg = []
        self.traj_points_clarke = []

        # Initialize signals
        self.compute_signals()

        # Signal curves and markers (ABC)
        self.curves_combined = [self.plot_combined.plot(t, self.signals_combined[:, i], pen=pg.mkPen(c, width=2), name=f"{chr(65+i)}") for i, c in enumerate(COLOR_POS_SEQ)]
        self.marker_combined = [self.plot_combined.plot([t[0]], [self.signals_combined[0, i]], pen=None, symbol='o', symbolBrush=c, symbolSize=8) for i, c in enumerate(COLOR_POS_SEQ)]

        # Signal curves and markers (Clarke)
        self.curves_clarke = []
        self.curves_clarke.append(self.plot_clarke.plot(t, self.signals_alpha, pen=pg.mkPen(COLOR_ALPHA, width=2), name="α"))
        self.curves_clarke.append(self.plot_clarke.plot(t, self.signals_beta, pen=pg.mkPen(COLOR_BETA, width=2), name="β"))
        
        self.marker_clarke = []
        self.marker_clarke.append(self.plot_clarke.plot([t[0]], [self.signals_alpha[0]], pen=None, symbol='o', symbolBrush=COLOR_ALPHA, symbolSize=8))
        self.marker_clarke.append(self.plot_clarke.plot([t[0]], [self.signals_beta[0]], pen=None, symbol='o', symbolBrush=COLOR_BETA, symbolSize=8))

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_frame)
        self.is_playing = False

        self.update_plots(0)

    def apply_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG};
                color: {COLOR_TEXT};
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }}
            QFrame#Sidebar {{
                background-color: {COLOR_PANEL};
                border-right: 1px solid {COLOR_BORDER};
            }}
            QLabel#SidebarTitle {{
                font-size: 14pt;
                font-weight: bold;
                color: {COLOR_ACCENT};
                margin-bottom: 10px;
            }}
            QGroupBox {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
                color: {COLOR_ACCENT};
            }}
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #005c99;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {COLOR_BORDER};
                height: 6px;
                background: {COLOR_BG};
                margin: 2px 0;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLOR_ACCENT};
                border: 1px solid {COLOR_ACCENT};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 3px;
                background: {COLOR_BG};
            }}
            QCheckBox::indicator:checked {{
                background: {COLOR_ACCENT};
                border-color: {COLOR_ACCENT};
            }}
            QDoubleSpinBox {{
                background-color: {COLOR_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {COLOR_ACCENT};
            }}
        """)

    def create_field(self, title):
        field = pg.PlotWidget(title=title)
        field.setXRange(-3, 3)
        field.setYRange(-3, 3)
        field.setAspectLocked(True)
        field.showGrid(x=True, y=True, alpha=0.3)
        field.getPlotItem().setTitle(title, color=COLOR_TEXT, size='11pt')
        return field

    def create_signal_plot(self, title):
        plot = pg.PlotWidget(title=title)
        plot.addLegend(offset=(10, 10))
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.getPlotItem().setTitle(title, color=COLOR_TEXT, size='11pt')
        return plot

    def create_vectors(self, field, colors):
        lines = [pg.PlotDataItem(pen=pg.mkPen(c, width=3)) for c in colors]
        tips = [pg.ScatterPlotItem(size=12, brush=c, pen=None) for c in colors]
        for line, tip in zip(lines, tips):
            field.addItem(line)
            field.addItem(tip)
        return lines, tips

    def create_resultant(self, field):
        line = pg.PlotDataItem(pen=pg.mkPen('w', width=4))
        tip = pg.ScatterPlotItem(size=16, brush='w', pen=None)
        field.addItem(line)
        field.addItem(tip)
        return line, tip

    def compute_signals(self):
        # Positive Sequence: Sum of Harmonics 1-5
        # V_pos = Sum( A_h * cos(h * (omega*t - angle)) )
        self.signals_pos = np.zeros((len(t), 3))
        
        for h_idx, amp in enumerate(self.amp_pos_harmonics):
            h_order = h_idx + 1
            if amp > 0.001:
                # Calculate harmonic component for all time and phases
                # Shape: (200, 3)
                component = np.array([[amp * np.cos(h_order * (omega * ti - angle)) for angle in angles] for ti in t])
                self.signals_pos += component

        self.signals_neg = np.array([[self.amp_neg * np.cos(omega * ti + angle) for angle in angles] for ti in t])
        self.signals_combined = self.signals_pos + self.signals_neg
        
        # Clarke Transform (Power Invariant)
        # alpha = sqrt(2/3) * (a - 0.5b - 0.5c)
        # beta  = sqrt(2/3) * (sqrt(3)/2 * b - sqrt(3)/2 * c)
        
        a = self.signals_combined[:, 0]
        b = self.signals_combined[:, 1]
        c = self.signals_combined[:, 2]
        
        if self.radio_amp_inv.isChecked():
            k = 2/3
        else:
            k = np.sqrt(2/3)
            
        self.signals_alpha = k * (a - 0.5*b - 0.5*c)
        self.signals_beta  = k * (np.sqrt(3)/2 * b - np.sqrt(3)/2 * c)

    def update_amplitudes(self):
        self.amp_pos_harmonics = [spin.value() for spin in self.amp_pos_inputs]
        self.amp_neg = self.amp_neg_input.value()
        self.compute_signals()
        
        # Update ABC curves
        for i in range(3):
            self.curves_combined[i].setData(t, self.signals_combined[:, i])
            
        # Update Clarke curves
        self.curves_clarke[0].setData(t, self.signals_alpha)
        self.curves_clarke[1].setData(t, self.signals_beta)
        
        self.update_plots(self.slider.value())

    def update_plots(self, frame):
        # Handle slider vs direct call
        if isinstance(frame, int):
            pass
        else:
            frame = self.slider.value()
            
        self.slider_label.setText(f"Time: {t[frame]:.2f} s")

        # Enable extra trajectory checkbox only if conditions are met
        self.extra_trajectory_checkbox.setEnabled(
            self.trajectory_checkbox.isChecked() and self.show_rotating_fields_checkbox.isChecked()
        )

        decomposition = self.decomposition_checkbox.isChecked()

        # --- ABC Mode Updates ---
        # Update markers
        for i in range(3):
            self.marker_combined[i].setData([t[frame]], [self.signals_combined[frame, i]])

        # Compute vectors
        vectors_pos = [(self.signals_pos[frame, i]*np.cos(angles[i]), self.signals_pos[frame, i]*np.sin(angles[i])) for i in range(3)]
        vectors_neg = [(self.signals_neg[frame, i]*np.cos(angles[i]), self.signals_neg[frame, i]*np.sin(angles[i])) for i in range(3)]
        vectors_combined = vectors_pos + vectors_neg
        
        sum_pos = (sum(v[0] for v in vectors_pos), sum(v[1] for v in vectors_pos))
        sum_neg = (sum(v[0] for v in vectors_neg), sum(v[1] for v in vectors_neg))
        
        # Update combined vectors
        self.update_field_vectors(self.lines_combined, self.tips_combined, vectors_combined, self.resultant_line_combined, self.resultant_tip_combined, decomposition)

        # Fix for artifact when amplitude is 0: Hide vectors if amplitude is 0
        # Positive Sequence (Indices 0-2)
        # Fix for artifact when amplitude is 0: Hide vectors if amplitude is 0
        # Positive Sequence (Indices 0-2)
        # Check if any harmonic has amplitude
        total_pos_amp = sum(self.amp_pos_harmonics)
        if total_pos_amp < 0.01:
            for i in range(3):
                self.lines_combined[i].setVisible(False)
                self.tips_combined[i].setVisible(False)
        else:
            for i in range(3):
                self.lines_combined[i].setVisible(True)
                self.tips_combined[i].setVisible(True)

        # Negative Sequence (Indices 3-5)
        if self.amp_neg < 0.01:
            for i in range(3, 6):
                self.lines_combined[i].setVisible(False)
                self.tips_combined[i].setVisible(False)
        else:
            for i in range(3, 6):
                self.lines_combined[i].setVisible(True)
                self.tips_combined[i].setVisible(True)

        # --- Clarke Mode Updates ---
        # Update markers
        self.marker_clarke[0].setData([t[frame]], [self.signals_alpha[frame]])
        self.marker_clarke[1].setData([t[frame]], [self.signals_beta[frame]])
        
        # Vectors: Alpha is on X axis, Beta is on Y axis
        val_alpha = self.signals_alpha[frame]
        val_beta = self.signals_beta[frame]
        
        vec_alpha = (val_alpha, 0)
        vec_beta = (0, val_beta)
        vectors_clarke = [vec_alpha, vec_beta]
        
        self.update_field_vectors(self.lines_clarke, self.tips_clarke, vectors_clarke, self.resultant_line_clarke, self.resultant_tip_clarke, decomposition)
        
        # Extra rotating fields in combined (Applicable to both modes if desired, but usually for ABC)
        if self.show_rotating_fields_checkbox.isChecked():
            # Positive resultant (reconstructed)
            if total_pos_amp >= 0.01:
                x_pos = sum_pos[0]
                y_pos = sum_pos[1]
                self.extra_line_pos.setData([0, x_pos], [0, y_pos])
                self.extra_tip_pos.setData([x_pos], [y_pos])
            else:
                self.extra_line_pos.setData([], [])
                self.extra_tip_pos.setData([], [])
                x_pos, y_pos = 0, 0 # Needed for negative offset

            # Negative resultant (added on top of positive)
            if self.amp_neg >= 0.01:
                x_neg = sum_neg[0]
                y_neg = sum_neg[1]
                self.extra_line_neg.setData([x_pos, x_pos + x_neg], [y_pos, y_pos + y_neg])
                self.extra_tip_neg.setData([x_pos + x_neg], [y_pos + y_neg])
            else:
                self.extra_line_neg.setData([], [])
                self.extra_tip_neg.setData([], [])
        else:
            self.extra_line_pos.setData([], [])
            self.extra_tip_pos.setData([], [])
            self.extra_line_neg.setData([], [])
            self.extra_tip_neg.setData([], [])

        # Update trajectory if enabled
        if self.trajectory_checkbox.isChecked():
            self.update_trajectory(self.resultant_line_combined, self.traj_points_combined, self.trajectory_combined)
            self.update_trajectory(self.resultant_line_clarke, self.traj_points_clarke, self.trajectory_clarke)

            # Extra trajectories if enabled
            if self.extra_trajectory_checkbox.isChecked() and self.show_rotating_fields_checkbox.isChecked():
                # Positive extra trajectory
                x_pos = sum_pos[0]
                y_pos = sum_pos[1]
                self.traj_points_extra_pos.append((x_pos, y_pos))
                xs, ys = zip(*self.traj_points_extra_pos)
                self.extra_trajectory_pos.setData(xs, ys)

                # Negative extra trajectory
                x_neg = sum_neg[0]
                y_neg = sum_neg[1]
                
                tip_x = x_pos + x_neg
                tip_y = y_pos + y_neg
                
                self.traj_points_extra_neg.append((tip_x, tip_y))
                xs, ys = zip(*self.traj_points_extra_neg)
                self.extra_trajectory_neg.setData(xs, ys)

    def update_field_vectors(self, lines, tips, vectors, resultant_line, resultant_tip, decomposition):
        if decomposition:
            points = [(0, 0)]
            for vec in vectors:
                last = points[-1]
                points.append((last[0] + vec[0], last[1] + vec[1]))
            for i, (line, tip) in enumerate(zip(lines, tips)):
                line.setData([points[i][0], points[i+1][0]], [points[i][1], points[i+1][1]])
                tip.setData([points[i+1][0]], [points[i+1][1]])
            resultant_line.setData([0, points[-1][0]], [0, points[-1][1]])
            resultant_tip.setData([points[-1][0]], [points[-1][1]])
        else:
            x_sum = sum(v[0] for v in vectors)
            y_sum = sum(v[1] for v in vectors)
            for line, tip, vec in zip(lines, tips, vectors):
                line.setData([0, vec[0]], [0, vec[1]])
                tip.setData([vec[0]], [vec[1]])
            resultant_line.setData([0, x_sum], [0, y_sum])
            resultant_tip.setData([x_sum], [y_sum])

    def update_trajectory(self, resultant_line, traj_points, trajectory_item):
        x = resultant_line.xData[-1]
        y = resultant_line.yData[-1]
        traj_points.append((x, y))
        xs, ys = zip(*traj_points)
        trajectory_item.setData(xs, ys)

    def toggle_trajectory(self):
        if not self.trajectory_checkbox.isChecked():
            self.clear_trajectories()

    def toggle_extra_trajectory(self):
        if not self.extra_trajectory_checkbox.isChecked():
            self.traj_points_extra_pos.clear()
            self.traj_points_extra_neg.clear()
            self.extra_trajectory_pos.setData([], [])
            self.extra_trajectory_neg.setData([], [])

    def clear_trajectories(self):
        self.traj_points_combined.clear()
        self.traj_points_extra_pos.clear()
        self.traj_points_extra_neg.clear()
        self.traj_points_clarke.clear()
        self.trajectory_combined.setData([], [])
        self.extra_trajectory_pos.setData([], [])
        self.extra_trajectory_neg.setData([], [])
        self.trajectory_clarke.setData([], [])

    def reset_all(self):
        self.timer.stop()
        self.is_playing = False
        self.play_button.setText("Play")
        self.slider.setValue(0)
        self.clear_trajectories()

    def toggle_play(self):
        if self.is_playing:
            self.timer.stop()
            self.play_button.setText("Play")
        else:
            self.timer.start(50)
            self.play_button.setText("Pause")
        self.is_playing = not self.is_playing

    def advance_frame(self):
        current = self.slider.value()
        if current < self.slider.maximum():
            self.slider.setValue(current + 1)
        else:
            if self.loop_checkbox.isChecked():
                self.slider.setValue(0)
                self.clear_trajectories()
            else:
                self.timer.stop()
                self.play_button.setText("Play")
                self.is_playing = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ClarkeTransformWidget()
    win.show()
    sys.exit(app.exec_())
