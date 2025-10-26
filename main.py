import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsTextItem, QMessageBox,
                             QDialog, QFormLayout, QDoubleSpinBox, QTextEdit,
                             QTabWidget, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

# Estilos CSS
STYLE_SHEET = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QPushButton#deleteBtn {
    background-color: #f44336;
}

QPushButton#deleteBtn:hover {
    background-color: #d32f2f;
}

QPushButton#calculateBtn {
    background-color: #4CAF50;
    font-size: 11pt;
    padding: 10px 20px;
}

QPushButton#calculateBtn:hover {
    background-color: #45a049;
}

QLabel {
    color: #333;
}

QLabel#titleLabel {
    font-size: 14pt;
    font-weight: bold;
    color: #1976D2;
    padding: 10px;
}

QLineEdit, QComboBox, QDoubleSpinBox {
    padding: 6px;
    border: 2px solid #ddd;
    border-radius: 4px;
    background-color: white;
}

QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #2196F3;
}

QGraphicsView {
    background-color: white;
    border: 2px solid #ddd;
    border-radius: 4px;
}

QTextEdit {
    background-color: #f9f9f9;
    border: 2px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    font-family: 'Consolas', 'Courier New', monospace;
}

QGroupBox {
    background-color: white;
    border: 2px solid #ddd;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
}

QGroupBox::title {
    color: #1976D2;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QTabWidget::pane {
    border: 2px solid #ddd;
    border-radius: 4px;
    background-color: white;
}

QTabBar::tab {
    background-color: #e0e0e0;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #2196F3;
    color: white;
}

QScrollArea {
    border: none;
}
"""


class ComponentBlock(QGraphicsItem):
    """Bloque gráfico que representa un componente del sistema"""
    
    def __init__(self, component_type, name, params):
        super().__init__()
        self.component_type = component_type
        self.name = name
        self.params = params
        self.width = 120
        self.height = 80
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # Colores según tipo de componente
        self.colors = {
            'Componente Simple': QColor(100, 181, 246),
            'Serie': QColor(129, 199, 132),
            'Paralelo': QColor(255, 183, 77),
            'Redundancia k-de-n': QColor(255, 138, 101),
            'Sistema con Mantenimiento': QColor(186, 104, 200)
        }
        
        self.connections_out = []
        self.connections_in = []
        
    def boundingRect(self):
        return QRectF(-self.width/2, -self.height/2, self.width, self.height)
    
    def paint(self, painter, option, widget):
        # Configurar antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Color base
        base_color = self.colors.get(self.component_type, QColor(200, 200, 200))
        
        # Si está seleccionado, usar borde más grueso
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 152, 0), 3))
        else:
            painter.setPen(QPen(Qt.black, 2))
        
        # Dibujar rectángulo con gradiente
        painter.setBrush(QBrush(base_color))
        rect = QRectF(-self.width/2, -self.height/2, self.width, self.height)
        painter.drawRoundedRect(rect, 10, 10)
        
        # Dibujar nombre del componente
        painter.setPen(QPen(Qt.black))
        font = QFont('Arial', 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect.adjusted(5, 5, -5, -40), Qt.AlignCenter | Qt.TextWordWrap, self.name)
        
        # Dibujar tipo de componente
        font.setPointSize(7)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(rect.adjusted(5, 35, -5, -5), Qt.AlignCenter | Qt.TextWordWrap, 
                        self.component_type)
    
    def get_mtbf(self):
        """Calcula el MTBF del componente según su tipo y parámetros"""
        if self.component_type == 'Componente Simple':
            # MTBF = 1/λ para tasa de fallo constante
            lambda_val = self.params.get('lambda', 0.001)
            if lambda_val > 0:
                return 1 / lambda_val
            return float('inf')
            
        elif self.component_type == 'Serie':
            # Para sistema en serie: 1/MTBF_sys = Σ(1/MTBF_i)
            n = self.params.get('n_components', 2)
            mtbf_comp = self.params.get('mtbf_component', 1000)
            if mtbf_comp > 0:
                return mtbf_comp / n
            return 0
            
        elif self.component_type == 'Paralelo':
            # Redundancia paralela: MTBF aumenta significativamente
            n = self.params.get('n_components', 2)
            mtbf_comp = self.params.get('mtbf_component', 1000)
            # Aproximación: MTBF_sys ≈ MTBF_comp * (1 + 1/2 + 1/3 + ... + 1/n)
            harmonic_sum = sum(1/i for i in range(1, n+1))
            return mtbf_comp * harmonic_sum
            
        elif self.component_type == 'Redundancia k-de-n':
            # Sistema k-de-n: requiere al menos k de n componentes
            n = self.params.get('n_total', 3)
            k = self.params.get('k_required', 2)
            mtbf_comp = self.params.get('mtbf_component', 1000)
            # Aproximación simplificada
            if k <= n:
                factor = sum(1/i for i in range(k, n+1))
                return mtbf_comp * factor
            return 0
            
        elif self.component_type == 'Sistema con Mantenimiento':
            # Con mantenimiento preventivo: MTBF_PM = ∫R(t)dt / (1-R(Y))
            mtbf_base = self.params.get('mtbf_base', 1000)
            interval = self.params.get('maintenance_interval', 100)
            lambda_val = 1 / mtbf_base if mtbf_base > 0 else 0.001
            
            # Calcular R(Y) - confiabilidad en el intervalo de mantenimiento
            r_y = math.exp(-lambda_val * interval)
            
            # Calcular integral de R(t) de 0 a Y
            integral_r = mtbf_base * (1 - math.exp(-lambda_val * interval))
            
            if r_y < 1:
                mtbf_pm = integral_r / (1 - r_y)
                return mtbf_pm
            return mtbf_base
        
        return 0


class ConnectionLine(QGraphicsItem):
    """Línea de conexión entre componentes"""
    
    def __init__(self, start_block, end_block):
        super().__init__()
        self.start_block = start_block
        self.end_block = end_block
        self.setZValue(-1)
        
    def boundingRect(self):
        start = self.start_block.pos()
        end = self.end_block.pos()
        return QRectF(start, end).normalized().adjusted(-10, -10, 10, 10)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        start = self.start_block.pos()
        end = self.end_block.pos()
        
        line = QLineF(start, end)
        
        # Dibujar línea con flecha
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(line)
        
        # Dibujar flecha al final
        angle = math.atan2(-line.dy(), line.dx())
        arrow_size = 10
        
        arrow_p1 = end + QPointF(
            math.sin(angle + math.pi / 3) * arrow_size,
            math.cos(angle + math.pi / 3) * arrow_size
        )
        arrow_p2 = end + QPointF(
            math.sin(angle + math.pi - math.pi / 3) * arrow_size,
            math.cos(angle + math.pi - math.pi / 3) * arrow_size
        )
        
        arrow_head = QPainterPath()
        arrow_head.moveTo(end)
        arrow_head.lineTo(arrow_p1)
        arrow_head.lineTo(arrow_p2)
        arrow_head.closeSubpath()
        
        painter.setBrush(QBrush(QColor(100, 100, 100)))
        painter.drawPath(arrow_head)


class ComponentDialog(QDialog):
    """Diálogo para configurar parámetros del componente"""
    
    def __init__(self, component_type, parent=None):
        super().__init__(parent)
        self.component_type = component_type
        self.params = {}
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f'Configurar {self.component_type}')
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Nombre del componente
        self.name_input = QLineEdit(f'{self.component_type} 1')
        form_layout.addRow('Nombre:', self.name_input)
        
        # Parámetros específicos según tipo
        if self.component_type == 'Componente Simple':
            self.lambda_input = QDoubleSpinBox()
            self.lambda_input.setDecimals(6)
            self.lambda_input.setRange(0.000001, 1.0)
            self.lambda_input.setValue(0.001)
            self.lambda_input.setSuffix(' fallos/hora')
            form_layout.addRow('Tasa de fallo (λ):', self.lambda_input)
            
        elif self.component_type == 'Serie':
            self.n_input = QDoubleSpinBox()
            self.n_input.setDecimals(0)
            self.n_input.setRange(2, 100)
            self.n_input.setValue(2)
            form_layout.addRow('Número de componentes:', self.n_input)
            
            self.mtbf_input = QDoubleSpinBox()
            self.mtbf_input.setRange(1, 1000000)
            self.mtbf_input.setValue(1000)
            self.mtbf_input.setSuffix(' horas')
            form_layout.addRow('MTBF por componente:', self.mtbf_input)
            
        elif self.component_type == 'Paralelo':
            self.n_input = QDoubleSpinBox()
            self.n_input.setDecimals(0)
            self.n_input.setRange(2, 10)
            self.n_input.setValue(2)
            form_layout.addRow('Componentes en paralelo:', self.n_input)
            
            self.mtbf_input = QDoubleSpinBox()
            self.mtbf_input.setRange(1, 1000000)
            self.mtbf_input.setValue(1000)
            self.mtbf_input.setSuffix(' horas')
            form_layout.addRow('MTBF por componente:', self.mtbf_input)
            
        elif self.component_type == 'Redundancia k-de-n':
            self.n_input = QDoubleSpinBox()
            self.n_input.setDecimals(0)
            self.n_input.setRange(2, 10)
            self.n_input.setValue(3)
            form_layout.addRow('Total de componentes (n):', self.n_input)
            
            self.k_input = QDoubleSpinBox()
            self.k_input.setDecimals(0)
            self.k_input.setRange(1, 10)
            self.k_input.setValue(2)
            form_layout.addRow('Requeridos (k):', self.k_input)
            
            self.mtbf_input = QDoubleSpinBox()
            self.mtbf_input.setRange(1, 1000000)
            self.mtbf_input.setValue(1000)
            self.mtbf_input.setSuffix(' horas')
            form_layout.addRow('MTBF por componente:', self.mtbf_input)
            
        elif self.component_type == 'Sistema con Mantenimiento':
            self.mtbf_base_input = QDoubleSpinBox()
            self.mtbf_base_input.setRange(1, 1000000)
            self.mtbf_base_input.setValue(1000)
            self.mtbf_base_input.setSuffix(' horas')
            form_layout.addRow('MTBF base:', self.mtbf_base_input)
            
            self.interval_input = QDoubleSpinBox()
            self.interval_input.setRange(1, 10000)
            self.interval_input.setValue(100)
            self.interval_input.setSuffix(' horas')
            form_layout.addRow('Intervalo mantenimiento (Y):', self.interval_input)
        
        layout.addLayout(form_layout)
        
        # Información teórica
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setHtml(self.get_theory_info())
        layout.addWidget(QLabel('Información teórica:'))
        layout.addWidget(info_text)
        
        # Botones
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('Aceptar')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('Cancelar')
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_theory_info(self):
        """Retorna información teórica sobre el tipo de componente"""
        info = {
            'Componente Simple': '''
                <b>Ley de falla exponencial:</b><br>
                R(t) = e<sup>-λt</sup><br>
                MTBF = 1/λ<br>
                <i>Válido para tasa de fallo constante</i>
            ''',
            'Serie': '''
                <b>Sistema en Serie:</b><br>
                1/MTBF<sub>sys</sub> = Σ(1/MTBF<sub>i</sub>)<br>
                <i>Todos los componentes deben funcionar</i>
            ''',
            'Paralelo': '''
                <b>Redundancia Paralela:</b><br>
                MTBF aumenta con redundancia<br>
                <i>El sistema funciona si al menos uno opera</i>
            ''',
            'Redundancia k-de-n': '''
                <b>Sistema k-de-n:</b><br>
                Requiere k de n componentes operando<br>
                <i>Mayor flexibilidad que serie/paralelo</i>
            ''',
            'Sistema con Mantenimiento': '''
                <b>Con Mantenimiento Preventivo:</b><br>
                MTBF<sub>PM</sub> = ∫R(t)dt / (1-R(Y))<br>
                <i>Mantenimiento cada Y horas mejora confiabilidad</i>
            '''
        }
        return info.get(self.component_type, '')
    
    def get_params(self):
        """Obtiene los parámetros configurados"""
        params = {'name': self.name_input.text()}
        
        if self.component_type == 'Componente Simple':
            params['lambda'] = self.lambda_input.value()
            
        elif self.component_type == 'Serie':
            params['n_components'] = int(self.n_input.value())
            params['mtbf_component'] = self.mtbf_input.value()
            
        elif self.component_type == 'Paralelo':
            params['n_components'] = int(self.n_input.value())
            params['mtbf_component'] = self.mtbf_input.value()
            
        elif self.component_type == 'Redundancia k-de-n':
            params['n_total'] = int(self.n_input.value())
            params['k_required'] = int(self.k_input.value())
            params['mtbf_component'] = self.mtbf_input.value()
            
        elif self.component_type == 'Sistema con Mantenimiento':
            params['mtbf_base'] = self.mtbf_base_input.value()
            params['maintenance_interval'] = self.interval_input.value()
        
        return params


class MTBFCalculator(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        self.components = []
        self.connections = []
        self.connection_mode = False
        self.connection_start = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('MTBF Calculator - Sistema de Evaluación de Confiabilidad')
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Panel izquierdo - Herramientas
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(300)
        
        # Título
        title = QLabel('MTBF Calculator')
        title.setObjectName('titleLabel')
        title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title)
        
        # Grupo de componentes
        components_group = QGroupBox('Componentes del Sistema')
        components_layout = QVBoxLayout()
        
        component_types = [
            'Componente Simple',
            'Serie',
            'Paralelo',
            'Redundancia k-de-n',
            'Sistema con Mantenimiento'
        ]
        
        for comp_type in component_types:
            btn = QPushButton(f'Agregar {comp_type}')
            btn.clicked.connect(lambda checked, ct=comp_type: self.add_component(ct))
            components_layout.addWidget(btn)
        
        components_group.setLayout(components_layout)
        left_layout.addWidget(components_group)
        
        # Grupo de acciones
        actions_group = QGroupBox('Acciones')
        actions_layout = QVBoxLayout()
        
        self.connect_btn = QPushButton('Conectar Componentes')
        self.connect_btn.setCheckable(True)
        self.connect_btn.clicked.connect(self.toggle_connection_mode)
        actions_layout.addWidget(self.connect_btn)
        
        delete_btn = QPushButton('Eliminar Seleccionado')
        delete_btn.setObjectName('deleteBtn')
        delete_btn.clicked.connect(self.delete_selected)
        actions_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton('Limpiar Todo')
        clear_btn.setObjectName('deleteBtn')
        clear_btn.clicked.connect(self.clear_all)
        actions_layout.addWidget(clear_btn)
        
        actions_group.setLayout(actions_layout)
        left_layout.addWidget(actions_group)
        
        # Botón calcular
        calc_btn = QPushButton('Calcular MTBF del Sistema')
        calc_btn.setObjectName('calculateBtn')
        calc_btn.clicked.connect(self.calculate_system_mtbf)
        left_layout.addWidget(calc_btn)
        
        left_layout.addStretch()
        
        # Información del proyecto
        info_group = QGroupBox('Información')
        info_layout = QVBoxLayout()
        info_text = QLabel(
            '<small><b>Proyecto de Investigación UTP</b><br>'
            'Metodología para evaluar MTBF<br>'
            'según etapas TRL<br><br>'
            '<i>Arrastra los bloques para diseñar<br>'
            'tu sistema de confiabilidad</i></small>'
        )
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        left_layout.addWidget(info_group)
        
        main_layout.addWidget(left_panel)
        
        # Panel central/derecho - Vista y resultados
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tabs para vista y resultados
        self.tabs = QTabWidget()
        
        # Tab 1: Vista del sistema
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.mousePressEvent = self.scene_mouse_press
        
        self.tabs.addTab(self.view, 'Diseño del Sistema')
        
        # Tab 2: Resultados
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(QLabel('<b>Resultados del Análisis de Confiabilidad:</b>'))
        results_layout.addWidget(self.results_text)
        
        self.tabs.addTab(results_widget, 'Resultados')
        
        right_layout.addWidget(self.tabs)
        main_layout.addWidget(right_panel)
        
        # Aplicar estilos
        self.setStyleSheet(STYLE_SHEET)
        
    def add_component(self, component_type):
        """Agrega un nuevo componente al sistema"""
        dialog = ComponentDialog(component_type, self)
        
        if dialog.exec_() == QDialog.Accepted:
            params = dialog.get_params()
            name = params.pop('name')
            
            block = ComponentBlock(component_type, name, params)
            
            # Posicionar en el centro de la vista
            x = 400 + len(self.components) * 30
            y = 300 + (len(self.components) % 3) * 100
            block.setPos(x, y)
            
            self.scene.addItem(block)
            self.components.append(block)
            
    def toggle_connection_mode(self):
        """Activa/desactiva el modo de conexión"""
        self.connection_mode = self.connect_btn.isChecked()
        if self.connection_mode:
            self.connect_btn.setText('Modo Conexión: Activo')
            self.connect_btn.setStyleSheet('background-color: #FF9800;')
        else:
            self.connect_btn.setText('Conectar Componentes')
            self.connect_btn.setStyleSheet('')
            self.connection_start = None
            
    def scene_mouse_press(self, event):
        """Maneja clics en la escena para crear conexiones"""
        QGraphicsView.mousePressEvent(self.view, event)
        
        if self.connection_mode:
            pos = self.view.mapToScene(event.pos())
            item = self.scene.itemAt(pos, self.view.transform())
            
            if isinstance(item, ComponentBlock):
                if self.connection_start is None:
                    self.connection_start = item
                    item.setSelected(True)
                else:
                    if item != self.connection_start:
                        # Crear conexión
                        connection = ConnectionLine(self.connection_start, item)
                        self.scene.addItem(connection)
                        self.connections.append(connection)
                        
                        self.connection_start.connections_out.append(item)
                        item.connections_in.append(self.connection_start)
                        
                    self.connection_start.setSelected(False)
                    self.connection_start = None
                    
    def delete_selected(self):
        """Elimina el componente seleccionado"""
        for item in self.scene.selectedItems():
            if isinstance(item, ComponentBlock):
                # Eliminar conexiones asociadas
                for conn in self.connections[:]:
                    if conn.start_block == item or conn.end_block == item:
                        self.scene.removeItem(conn)
                        self.connections.remove(conn)
                
                self.scene.removeItem(item)
                self.components.remove(item)
                
    def clear_all(self):
        """Limpia todo el diseño"""
        reply = QMessageBox.question(self, 'Confirmar', 
                                     '¿Está seguro de eliminar todo el diseño?',
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.scene.clear()
            self.components.clear()
            self.connections.clear()
            self.results_text.clear()
            
    def calculate_system_mtbf(self):
        """Calcula el MTBF del sistema completo"""
        if not self.components:
            QMessageBox.warning(self, 'Advertencia', 
                              'No hay componentes en el sistema.')
            return
        
        results = '<h2>Análisis de Confiabilidad del Sistema</h2>'
        results += '<hr>'
        
        results += '<h3>Componentes Individuales:</h3>'
        results += '<table border="1" cellpadding="5" cellspacing="0" width="100%">'
        results += '<tr style="background-color: #2196F3; color: white;">'
        results += '<th>Nombre</th><th>Tipo</th><th>MTBF (horas)</th><th>λ (fallos/hora)</th></tr>'
        
        total_mtbf = 0
        for comp in self.components:
            mtbf = comp.get_mtbf()
            lambda_val = 1/mtbf if mtbf > 0 else 0
            
            results += f'<tr>'
            results += f'<td>{comp.name}</td>'
            results += f'<td>{comp.component_type}</td>'
            results += f'<td><b>{mtbf:.2f}</b></td>'
            results += f'<td>{lambda_val:.6f}</td>'
            results += f'</tr>'
        
        results += '</table><br>'
        
        # Calcular MTBF del sistema
        # Simplificación: si hay conexiones, considerar serie
        # Si no hay conexiones, tomar el promedio
        if self.connections:
            # Sistema en serie (simplificado)
            lambda_system = sum(1/comp.get_mtbf() for comp in self.components if comp.get_mtbf() > 0)
            mtbf_system = 1/lambda_system if lambda_system > 0 else 0
            
            results += '<h3>MTBF del Sistema (Configuración Serie):</h3>'
            results += f'<p style="font-size: 14pt; color: #4CAF50;"><b>MTBF<sub>sistema</sub> = {mtbf_system:.2f} horas</b></p>'
            results += f'<p>λ<sub>sistema</sub> = {lambda_system:.6f} fallos/hora</p>'
            
            # Calcular confiabilidad para diferentes tiempos
            results += '<h3>Confiabilidad R(t) en diferentes tiempos:</h3>'
            results += '<table border="1" cellpadding="5" cellspacing="0" width="100%">'
            results += '<tr style="background-color: #2196F3; color: white;">'
            results += '<th>Tiempo (horas)</th><th>R(t)</th><th>Q(t)</th></tr>'
            
            for t in [100, 500, 1000, 2000, 5000]:
                r_t = math.exp(-lambda_system * t)
                q_t = 1 - r_t
                results += f'<tr><td>{t}</td><td>{r_t:.4f}</td><td>{q_t:.4f}</td></tr>'
            
            results += '</table>'
            
        else:
            # Sin conexiones, mostrar estadísticas generales
            mtbfs = [comp.get_mtbf() for comp in self.components]
            avg_mtbf = sum(mtbfs) / len(mtbfs) if mtbfs else 0
            min_mtbf = min(mtbfs) if mtbfs else 0
            max_mtbf = max(mtbfs) if mtbfs else 0
            
            results += '<h3>Estadísticas del Sistema (sin conexiones definidas):</h3>'
            results += f'<p>MTBF Promedio: <b>{avg_mtbf:.2f} horas</b></p>'
            results += f'<p>MTBF Mínimo: <b>{min_mtbf:.2f} horas</b></p>'
            results += f'<p>MTBF Máximo: <b>{max_mtbf:.2f} horas</b></p>'
        
        results += '<hr>'
        results += '<h3>Fundamentos Teóricos Aplicados:</h3>'
        results += '<ul>'
        results += '<li><b>Confiabilidad R(t):</b> R(t) = e<sup>-λt</sup> = 1 - F(t)</li>'
        results += '<li><b>Tasa de fallo:</b> λ = 1 / MTBF</li>'
        results += '<li><b>MTBF:</b> ∫<sub>0</sub><sup>∞</sup> R(t)dt</li>'
        results += '<li><b>Sistema Serie:</b> λ<sub>sys</sub> = Σλ<sub>i</sub></li>'
        results += '</ul>'
        
        results += f'<p><small><i>Basado en el proyecto de investigación:<br>'
        results += f'"Metodología para evaluar el MTBF según etapas TRL"<br>'
        results += f'Universidad Tecnológica de Pereira</i></small></p>'
        
        self.results_text.setHtml(results)
        self.tabs.setCurrentIndex(1)  # Cambiar a pestaña de resultados


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    calculator = MTBFCalculator()
    calculator.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()