# Définition de la classe modeleMainwindow




class modeleMainwindow:
    
    
    # Constructeur par défaut
    
    
    def __init__(self):
        
        self.logs = []
        self.screen_width = 0
        self.screen_height = 0
    
    
    # Définition des méthodes
    
    
    def log(self, message):
        
        if len(self.logs) > 10:
            self.logs = []
        self.logs.append(message)


    def set_screen_resolution(self, width, height):
        
        if width <= self.screen_width:
            self.screen_width = width
        if height <= self.screen_height:
            self.screen_height = height
