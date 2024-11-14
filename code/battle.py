from settings import *

class Battle:
    def __init__(self, player_monsters, opponenet_monsters, monster_frames, bg_surf, fonts):
        self.display_surface = pygame.display.get_surface()
        self.bg_surf = bg_surf
        self.monster_frames = monster_frames
        self.fonts = fonts
        self.monster_data = {'player': player_monsters, 'opponent': opponenet_monsters} #this is sometimes necessary as sometimes you would wanna update all the monsters.
        self.setup()
        
    def setup(self):
        for entity, monster in self.monster_data.items():
            for index, monster in {k:v for k,v in monster.items() if k <= 2}.items(): #using dictionary comprehension 
                print(index, monster)
        
    def update(self, dt):
        self.display_surface.blit(self.bg_surf, (0,0))