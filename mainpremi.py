import sys
import math
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Estilos minimalistas - Solo Blanco, Azul y Naranja
STYLE = """
QMainWindow {
    background-color: #FFFFFF;
}

QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 4px;
    font-size: 10pt;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QPushButton#orange {
    background-color: #FF9800;
}

QPushButton#orange:hover {
    background-color: #F57C00;
}

QLabel {
    color: #212121;
    font-size: 10pt;
}

QLineEdit, QDoubleSpinBox, QSpinBox {
    padding: 8px;
    border: 2px solid #E0E0E0;
    border-radius: 4px;
    background-color: white;
}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
    border-color: #2196F3;
}

QGraphicsView {
    background-color: #FAFAFA;
    border: 2px solid #E0E0E0;
}

QTextEdit {
    background-color: white;
    border: 2px solid #E0E0E0;
    padding: 10px;
}

QTableWidget {
    border: 2px solid #E0E0E0;
    gridline-color: #E0E0E0;
}

QHeaderView::section {
    background-color: #2196F3;
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
}
"""


class Block(QGraphicsItem):
    """Bloque arrastrable simple"""
    
    def __init__(self, block_type, name, params):
        super().__init__()
        self.block_type = block_type
        self.name = name
        self.params = params
        self.w = 140
        self.h = 80
        
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(Qt.OpenHandCursor)
        
        self.dragging = False
        
    def boundingRect(self):
        return QRectF(-self.w/2, -self.h/2, self.w, self.h)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Color según tipo
        colors = {
            'Serie': '#2196F3',
            'Paralelo': '#FF9800',
            'k-de-n': '#2196F3'
        }
        color = QColor(colors.get(self.block_type, '#2196F3'))
        
        rect = QRectF(-self.w/2, -self.h/2, self.w, self.h)
        
        # Sombra si está seleccionado
        if self.isSelected():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 40))
            shadow = rect.adjusted(2, 2, 2, 2)
            painter.drawRoundedRect(shadow, 6, 6)
        
        # Bloque principal
        painter.setPen(QPen(color.darker(120), 2))
        painter.setBrush(color)
        painter.drawRoundedRect(rect, 6, 6)
        
        # Texto
        painter.setPen(Qt.white)
        font = QFont('Arial', 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect.adjusted(5, 5, -5, -30), Qt.AlignCenter, self.name)
        
        # Tipo
        font.setPointSize(7)
        painter.setFont(font)
        painter.drawText(rect.adjusted(5, 40, -5, -5), Qt.AlignCenter, self.block_type)
        
    def mousePressEvent(self, event):
        self.dragging = True
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        # Abrir configuración al doble clic
        if self.scene() and hasattr(self.scene().parent(), 'edit_block'):
            self.scene().parent().edit_block(self)
    
    def get_mtbf(self):
        """Calcula MTBF según configuración"""
        if self.block_type == 'Serie':
            n = self.params.get('n', 2)
            mtbf_comp = self.params.get('mtbf', 1000)
            return mtbf_comp / n
            
        elif self.block_type == 'Paralelo':
            n = self.params.get('n', 2)
            mtbf_comp = self.params.get('mtbf', 1000)
            return mtbf_comp * sum(1/i for i in range(1, n+1))
            
        elif self.block_type == 'k-de-n':
            n = self.params.get('n', 3)
            k = self.params.get('k', 2)
            mtbf_comp = self.params.get('mtbf', 1000)
            return mtbf_comp * sum(1/i for i in range(k, n+1))
        
        return 1000


class Connection(QGraphicsItem):
    """Conexión entre bloques"""
    
    def __init__(self, start, end):
        super().__init__()
        self.start = start
        self.end = end
        self.setZValue(-1)
        
    def boundingRect(self):
        p1 = self.start.pos()
        p2 = self.end.pos()
        return QRectF(p1, p2).normalized().adjusted(-10, -10, 10, 10)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        p1 = self.start.pos()
        p2 = self.end.pos()
        
        # Línea
        painter.setPen(QPen(QColor('#757575'), 2))
        painter.drawLine(p1, p2)
        
        # Flecha
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        arrow_size = 10
        
        p_arrow1 = p2 - QPointF(
            math.cos(angle - math.pi/6) * arrow_size,
            math.sin(angle - math.pi/6) * arrow_size
        )
        p_arrow2 = p2 - QPointF(
            math.cos(angle + math.pi/6) * arrow_size,
            math.sin(angle + math.pi/6) * arrow_size
        )
        
        painter.setBrush(QColor('#757575'))
        painter.drawPolygon(QPolygonF([p2, p_arrow1, p_arrow2]))


class BlockConfig(QDialog):
    """Configuración de bloque"""
    
    def __init__(self, block, parent=None):
        super().__init__(parent)
        self.block = block
        self.setWindowTitle(f'Configurar: {block.block_type}')
        self.setModal(True)
        self.setFixedWidth(400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Nombre
        form = QFormLayout()
        self.name_input = QLineEdit(self.block.name)
        form.addRow('Nombre:', self.name_input)
        
        # Parámetros según tipo
        if self.block.block_type in ['Serie', 'Paralelo']:
            self.n_input = QSpinBox()
            self.n_input.setRange(2, 10)
            self.n_input.setValue(self.block.params.get('n', 2))
            form.addRow('Componentes (n):', self.n_input)
            
            self.mtbf_input = QDoubleSpinBox()
            self.mtbf_input.setRange(1, 1000000)
            self.mtbf_input.setValue(self.block.params.get('mtbf', 1000))
            self.mtbf_input.setSuffix(' h')
            form.addRow('MTBF por componente:', self.mtbf_input)
            
        elif self.block.block_type == 'k-de-n':
            self.n_input = QSpinBox()
            self.n_input.setRange(2, 10)
            self.n_input.setValue(self.block.params.get('n', 3))
            form.addRow('Total (n):', self.n_input)
            
            self.k_input = QSpinBox()
            self.k_input.setRange(1, 10)
            self.k_input.setValue(self.block.params.get('k', 2))
            form.addRow('Requeridos (k):', self.k_input)
            
            self.mtbf_input = QDoubleSpinBox()
            self.mtbf_input.setRange(1, 1000000)
            self.mtbf_input.setValue(self.block.params.get('mtbf', 1000))
            self.mtbf_input.setSuffix(' h')
            form.addRow('MTBF por componente:', self.mtbf_input)
        
        layout.addLayout(form)
        
        # Botones
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('Aceptar')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('Cancelar')
        cancel_btn.setObjectName('orange')
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(STYLE)
    
    def get_params(self):
        params = {'name': self.name_input.text()}
        
        if self.block.block_type in ['Serie', 'Paralelo']:
            params['n'] = self.n_input.value()
            params['mtbf'] = self.mtbf_input.value()
        elif self.block.block_type == 'k-de-n':
            params['n'] = self.n_input.value()
            params['k'] = self.k_input.value()
            params['mtbf'] = self.mtbf_input.value()
        
        return params


class MarkovAnalysis(QDialog):
    """Análisis de Markov simplificado"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Análisis de Markov')
        self.setModal(True)
        self.setMinimumSize(600, 550)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Info
        info = QLabel('Matriz de Transición de Estados (tasas por hora)')
        info.setStyleSheet('font-weight: bold; font-size: 11pt;')
        layout.addWidget(info)
        
        # Estados
        state_layout = QHBoxLayout()
        state_layout.addWidget(QLabel('Estados:'))
        self.states_spin = QSpinBox()
        self.states_spin.setRange(2, 5)
        self.states_spin.setValue(3)
        self.states_spin.valueChanged.connect(self.update_matrix)
        state_layout.addWidget(self.states_spin)
        state_layout.addStretch()
        layout.addLayout(state_layout)
        
        # Matriz
        self.matrix = QTableWidget(3, 3)
        self.matrix.setHorizontalHeaderLabels(['Operativo', 'Degradado', 'Fallo'])
        self.matrix.setVerticalHeaderLabels(['Operativo', 'Degradado', 'Fallo'])
        
        # Valores por defecto
        defaults = [
            ['-0.01', '0.008', '0.002'],
            ['0.05', '-0.08', '0.03'],
            ['0', '0', '0']
        ]
        
        for i in range(3):
            for j in range(3):
                item = QTableWidgetItem(defaults[i][j])
                item.setTextAlignment(Qt.AlignCenter)
                self.matrix.setItem(i, j, item)
        
        layout.addWidget(self.matrix)
        
        # Nota
        note = QLabel('Nota: Filas deben sumar cero. Ultimo estado es absorbente.')
        note.setStyleSheet('color: #757575; font-size: 9pt;')
        layout.addWidget(note)
        
        # Botones
        btn_layout = QHBoxLayout()
        calc_btn = QPushButton('Calcular')
        calc_btn.clicked.connect(self.calculate)
        close_btn = QPushButton('Cerrar')
        close_btn.setObjectName('orange')
        close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(calc_btn)
        layout.addLayout(btn_layout)
        
        # Resultados
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setMaximumHeight(120)
        layout.addWidget(self.results)
        
        self.setLayout(layout)
        self.setStyleSheet(STYLE)
    
    def update_matrix(self, n):
        self.matrix.setRowCount(n)
        self.matrix.setColumnCount(n)
        
        labels = ['Operativo', 'Degradado', 'Fallo', 'Estado 3', 'Estado 4'][:n]
        self.matrix.setHorizontalHeaderLabels(labels)
        self.matrix.setVerticalHeaderLabels(labels)
        
        for i in range(n):
            for j in range(n):
                if self.matrix.item(i, j) is None:
                    val = '-0.01' if i == j else ('0' if i == n-1 else '0.005')
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.matrix.setItem(i, j, item)
    
    def calculate(self):
        try:
            n = self.states_spin.value()
            Q = np.zeros((n, n))
            
            for i in range(n):
                for j in range(n):
                    Q[i, j] = float(self.matrix.item(i, j).text())
            
            # Validar
            sums = Q.sum(axis=1)
            if not np.allclose(sums, 0, atol=1e-5):
                QMessageBox.warning(self, 'Error', 'Las filas deben sumar cero')
                return
            
            # Estado estacionario
            A = np.vstack([Q.T, np.ones(n)])
            b = np.zeros(n + 1)
            b[-1] = 1
            pi = np.linalg.lstsq(A, b, rcond=None)[0]
            
            # MTBF
            mtbf = (1 - pi[-1]) / abs(Q[0, 0]) if Q[0, 0] < 0 else 0
            
            # Resultados
            result = f'<b>MTBF del Sistema: {mtbf:.2f} horas</b><br>'
            result += f'<b>Disponibilidad: {pi[0]:.4f} ({pi[0]*100:.2f}%)</b><br><br>'
            result += '<b>Probabilidades de Estado:</b><br>'
            
            names = ['Operativo', 'Degradado', 'Fallo', 'Estado 3', 'Estado 4']
            for i in range(n):
                result += f'{names[i]}: {pi[i]:.6f}<br>'
            
            self.results.setHtml(result)
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))


class MTBFApp(QMainWindow):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.connections = []
        self.connecting = False
        self.conn_start = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('MTBF Calculator')
        self.setGeometry(100, 100, 1200, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # Panel izquierdo
        left = QWidget()
        left.setMaximumWidth(220)
        left_layout = QVBoxLayout(left)
        
        title = QLabel('MTBF Calculator')
        title.setStyleSheet('font-size: 16pt; font-weight: bold; color: #2196F3; padding: 10px;')
        left_layout.addWidget(title)
        
        # Diagramas de bloques
        group1 = QLabel('Diagramas de Bloques')
        group1.setStyleSheet('font-weight: bold; margin-top: 10px;')
        left_layout.addWidget(group1)
        
        btn_serie = QPushButton('Sistema Serie')
        btn_serie.clicked.connect(lambda: self.add_block('Serie'))
        left_layout.addWidget(btn_serie)
        
        btn_paralelo = QPushButton('Sistema Paralelo')
        btn_paralelo.setObjectName('orange')
        btn_paralelo.clicked.connect(lambda: self.add_block('Paralelo'))
        left_layout.addWidget(btn_paralelo)
        
        btn_kn = QPushButton('Sistema k-de-n')
        btn_kn.clicked.connect(lambda: self.add_block('k-de-n'))
        left_layout.addWidget(btn_kn)
        
        # Markov
        group2 = QLabel('Análisis Avanzado')
        group2.setStyleSheet('font-weight: bold; margin-top: 20px;')
        left_layout.addWidget(group2)
        
        btn_markov = QPushButton('Cadenas de Markov')
        btn_markov.clicked.connect(self.show_markov)
        left_layout.addWidget(btn_markov)
        
        # Acciones
        group3 = QLabel('Acciones')
        group3.setStyleSheet('font-weight: bold; margin-top: 20px;')
        left_layout.addWidget(group3)
        
        self.btn_connect = QPushButton('Conectar Bloques')
        self.btn_connect.setCheckable(True)
        self.btn_connect.clicked.connect(self.toggle_connect)
        left_layout.addWidget(self.btn_connect)
        
        btn_delete = QPushButton('Eliminar')
        btn_delete.setObjectName('orange')
        btn_delete.clicked.connect(self.delete_selected)
        left_layout.addWidget(btn_delete)
        
        btn_clear = QPushButton('Limpiar Todo')
        btn_clear.setObjectName('orange')
        btn_clear.clicked.connect(self.clear_all)
        left_layout.addWidget(btn_clear)
        
        btn_calc = QPushButton('CALCULAR MTBF')
        btn_calc.setStyleSheet('background-color: #4CAF50; font-size: 11pt; padding: 12px;')
        btn_calc.clicked.connect(self.calculate)
        left_layout.addWidget(btn_calc)
        
        left_layout.addStretch()
        
        # Info
        info = QLabel('Doble clic en bloque\npara configurar')
        info.setStyleSheet('color: #757575; font-size: 9pt; padding: 10px;')
        info.setWordWrap(True)
        left_layout.addWidget(info)
        
        layout.addWidget(left)
        
        # Panel derecho - Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 900, 600)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.mousePressEvent = self.canvas_click
        
        self.tabs.addTab(self.view, 'Diseño')
        
        # Tab 2: Resultados
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.tabs.addTab(self.results, 'Resultados')
        
        layout.addWidget(self.tabs)
        
        self.setStyleSheet(STYLE)
        
        # Mensaje inicial
        self.results.setHtml(
            '<div style="padding: 50px; text-align: center;">'
            '<h2>Bienvenido</h2>'
            '<p>Arrastra bloques al canvas y conectalos.<br>'
            'Doble clic para configurar parametros.</p>'
            '</div>'
        )
    
    def add_block(self, block_type):
        # Configurar primero
        default_params = {'n': 2, 'mtbf': 1000, 'k': 2}
        temp_block = Block(block_type, f'{block_type} 1', default_params)
        
        dialog = BlockConfig(temp_block, self)
        if dialog.exec_() == QDialog.Accepted:
            params = dialog.get_params()
            name = params.pop('name')
            
            block = Block(block_type, name, params)
            
            # Posición
            x = 300 + (len(self.blocks) % 3) * 160
            y = 200 + (len(self.blocks) // 3) * 100
            block.setPos(x, y)
            
            self.scene.addItem(block)
            self.blocks.append(block)
    
    def edit_block(self, block):
        """Editar bloque existente"""
        dialog = BlockConfig(block, self)
        if dialog.exec_() == QDialog.Accepted:
            params = dialog.get_params()
            block.name = params.pop('name')
            block.params = params
            block.update()
    
    def toggle_connect(self):
        self.connecting = self.btn_connect.isChecked()
        if self.connecting:
            self.btn_connect.setText('Conectando...')
        else:
            self.btn_connect.setText('Conectar Bloques')
            self.conn_start = None
    
    def canvas_click(self, event):
        QGraphicsView.mousePressEvent(self.view, event)
        
        if self.connecting:
            pos = self.view.mapToScene(event.pos())
            item = self.scene.itemAt(pos, self.view.transform())
            
            if isinstance(item, Block):
                if self.conn_start is None:
                    self.conn_start = item
                    item.setSelected(True)
                else:
                    if item != self.conn_start:
                        conn = Connection(self.conn_start, item)
                        self.scene.addItem(conn)
                        self.connections.append(conn)
                    
                    self.conn_start.setSelected(False)
                    self.conn_start = None
    
    def delete_selected(self):
        for item in self.scene.selectedItems():
            if isinstance(item, Block):
                # Eliminar conexiones
                for conn in self.connections[:]:
                    if conn.start == item or conn.end == item:
                        self.scene.removeItem(conn)
                        self.connections.remove(conn)
                
                self.scene.removeItem(item)
                self.blocks.remove(item)
    
    def clear_all(self):
        reply = QMessageBox.question(
            self, 'Confirmar', 
            'Eliminar todo?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.scene.clear()
            self.blocks.clear()
            self.connections.clear()
            self.results.clear()
    
    def show_markov(self):
        dialog = MarkovAnalysis(self)
        dialog.exec_()
    
    def calculate(self):
        if not self.blocks:
            QMessageBox.warning(self, 'Error', 'Agrega bloques primero')
            return
        
        # Calcular
        result = '<h2>Resultados</h2><hr>'
        result += '<table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%;">'
        result += '<tr style="background: #2196F3; color: white;">'
        result += '<th>Bloque</th><th>Tipo</th><th>MTBF (h)</th></tr>'
        
        total_lambda = 0
        for block in self.blocks:
            mtbf = block.get_mtbf()
            lambda_val = 1/mtbf if mtbf > 0 else 0
            total_lambda += lambda_val
            
            result += f'<tr>'
            result += f'<td>{block.name}</td>'
            result += f'<td>{block.block_type}</td>'
            result += f'<td><b>{mtbf:.2f}</b></td>'
            result += '</tr>'
        
        result += '</table><br>'
        
        if self.connections:
            mtbf_sys = 1/total_lambda if total_lambda > 0 else 0
            
            result += '<div style="background: #E3F2FD; padding: 20px; border-radius: 5px;">'
            result += f'<h3>MTBF del Sistema: {mtbf_sys:.2f} horas</h3>'
            result += f'<p>Tasa de fallo: {total_lambda:.6f} fallos/hora</p>'
            result += '</div><br>'
            
            result += '<h4>Confiabilidad R(t):</h4>'
            result += '<table border="1" cellpadding="8" style="border-collapse: collapse;">'
            result += '<tr style="background: #2196F3; color: white;">'
            result += '<th>Tiempo (h)</th><th>R(t)</th><th>Disponibilidad</th></tr>'
            
            for t in [100, 500, 1000, 2000, 5000]:
                r_t = math.exp(-total_lambda * t)
                result += f'<tr>'
                result += f'<td>{t}</td>'
                result += f'<td><b>{r_t:.4f}</b></td>'
                result += f'<td>{r_t*100:.2f}%</td>'
                result += '</tr>'
            
            result += '</table>'
        
        self.results.setHtml(result)
        self.tabs.setCurrentIndex(1)


def main():
    app = QApplication(sys.argv)
    window = MTBFApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()