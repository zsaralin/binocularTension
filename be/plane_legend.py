# plane_legend.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QCheckBox
)
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt
from live_config import LiveConfig

class PlaneLegendWidget(QWidget):
    """Widget to display explanations of the different planes in the 3D viewer."""
    
    def __init__(self, parent=None):
        super(PlaneLegendWidget, self).__init__(parent)
        self.live_config = LiveConfig.get_instance()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface for the plane legend."""
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create a scroll area for better handling of content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Add title
        title = QLabel("3D Viewer Plane Guide")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        content_layout.addWidget(title)
        
        # Add explanation sections with visibility toggles
        self.add_plane_section(
            content_layout,
            "Vertical Division Planes",
            "• Divide space into angular sections\n"
            "• Track left-right movement\n"
            "• Controlled by X Divider Angle",
            'show_vertical_planes'
        )
        
        self.add_plane_section(
            content_layout,
            "Top Horizontal Plane",
            "• Upper tracking boundary\n"
            "• Detects 'looking up' movements\n"
            "• Set by Y Top Divider & Angle",
            'show_top_plane'
        )
        
        self.add_plane_section(
            content_layout,
            "Bottom Horizontal Plane",
            "• Lower tracking boundary\n"
            "• Detects 'looking down' movements\n"
            "• Set by Y Bottom Divider & Angle",
            'show_bottom_plane'
        )
        
        # Add tips section
        tips_label = QLabel("Tips:")
        tips_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        content_layout.addWidget(tips_label)
        
        tips_content = QLabel(
            "• Use viewpoint buttons to understand plane positions\n"
            "• Green highlight shows active zone\n"
            "• Adjust planes using control panel sliders\n"
            "• Red dots show tracked objects\n"
            "• Toggle plane visibility using checkboxes"
        )
        tips_content.setWordWrap(True)
        content_layout.addWidget(tips_content)
        
        # Set up scroll area
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
        
    def add_plane_section(self, layout, title, description, visibility_attr):
        """Add a section explaining a specific plane type."""
        # Create container frame
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        frame.setLineWidth(1)
        
        # Create layout for the frame
        frame_layout = QVBoxLayout()
        
        # Create header layout
        header_layout = QHBoxLayout()
        
        
        # Add title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(title_label)
        
        # Add visibility checkbox
        checkbox = QCheckBox("Show")
        checkbox.setChecked(getattr(self.live_config, visibility_attr))
        checkbox.stateChanged.connect(
            lambda state, attr=visibility_attr: self.toggle_plane_visibility(attr, state)
        )
        header_layout.addWidget(checkbox)
        
        frame_layout.addLayout(header_layout)
        
        # Add description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        frame_layout.addWidget(desc_label)
        
        frame.setLayout(frame_layout)
        layout.addWidget(frame)
        
    def toggle_plane_visibility(self, visibility_attr, state):
        """Toggle the visibility of a plane type."""
        setattr(self.live_config, visibility_attr, bool(state))