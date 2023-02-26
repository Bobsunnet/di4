horizontal_header = '''::section{
                        Background-color: #94ABA0; 
                        color: #1C3045;
                        border: thick double #32a1ce;
                        font-size: 15px;
                        }'''
vertical_header = '''::section{
                        Background-color:rgb(215, 227, 232); 
                        color: #1C3045;
                        border-style: inset;
                        font-size: 14px;
                        }
                        '''

label_finder = '''
                font: 14px;
                background-color: #fffff;
                max-height: 150px; 
            '''

label_info = ''' font-size: 13px;
                background-color: #f3f3d3;
                border-style: outset;
                border-width: 1px;
                border-radius: 4px;
                border-color: #1C3045;
                min-width: 120;
                 
            '''

text_edit = ''' QTextEdit {
                    font-size: 14px;
                    background-color: #e3e8f0;
                    border: 2px solid #1C3025;
                    border-radius: 5px;
                    max-width: 1400; 
                    max-height: 160;
                }
                QTextEdit:focus {
                    background-color: #f6f6f6;
                    border-color: #2C4065; 
                }
            '''

line_edit = ''' QLineEdit {
                    font-size: 14px;
                    font-family: Rubik;
                    background-color: #e3e8f0;
                    border: 1px solid #1C3025;
                    border-radius: 5px;
                }
                
                QLineEdit:focus {
                    background-color: #f5f5f5;
                    border-color: #2C4065;
                    }
            '''



button_general = '''QPushButton {
                        background-color: #94ABA0;
                        color: #1C2025;
                        font: 12px;
                        padding: 4px;
                        border-style: inset;
                        border-radius: 4px;
                        border-width: 1px;
                        border-color: #1C3045;
                        
                        }
                        
                    QPushButton:hover {
                        background-color: #b0b9b2;
                        font: 13px;
                        }
                        
                    QPushButton:pressed {
                        background-color: #888;
                        
                        }
'''

button_delete = '''QPushButton {
                        background-color: #761e1b;
                        color: #fafafa;
                        border-style: outset;
                        padding: 4px;
                        font:bold 12px;
                        border-width: 1px;
                        border-radius: 4px;
                        border-color: #1C3045;
                    }
                    
                    QPushButton:hover {
                        background-color: #A02924;
                        font:bold 13px;
                    }
                    
                    QPushButton:pressed {
                        background-color: #bd4239;                        
                    }
                    '''
