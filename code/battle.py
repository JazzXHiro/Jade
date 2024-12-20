from settings import *
from sprites import MonsterSprite, MonsterNameSprite, MonsterLevelSprite, MonsterStatSprite, MonsterOutlineSprite
from groups import BattleSprites

class Battle:
    def __init__(self, player_monsters, opponenet_monsters, monster_frames, bg_surf, fonts):
        #general
        self.display_surface = pygame.display.get_surface()
        self.bg_surf = bg_surf
        self.monster_frames = monster_frames
        self.fonts = fonts
        self.monster_data = {'player': player_monsters, 'opponent': opponenet_monsters} #this is sometimes necessary as sometimes you would wanna update all the monsters.
        
        #groups
        self.battle_sprites   = BattleSprites()
        self.player_sprites   = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()
        
        #control
        self.current_monster = None
        
        self.setup()
        
    def setup(self):
        for entity, monster in self.monster_data.items():
            for index, monster in {k:v for k,v in monster.items() if k <= 2}.items(): #using dictionary comprehension 
                self.create_monster(monster, index, index, entity) #first index is to keep track of the monster and 2nd index is for  monster positioning(battlewindow)
                
                
    #pos index is the position of the monster in the battle window
    def create_monster(self, monster, index, pos_index, entity): #purpose of index is to uniquely identify a same entries of a monster
        frames = self.monster_frames['monsters'][monster.name]
        outline_frames = self.monster_frames['outlines'][monster.name]
        if entity == 'player':
            pos = list(BATTLE_POSITIONS['left'].values())[pos_index] #.values() gives the actual position while ignoring the keys
            groups = (self.battle_sprites, self.player_sprites)
            frames = {state: [pygame.transform.flip(frame, True, False) for frame in frames] for state, frames in frames.items()} #.flip(frame, horizontal, vertical)
            outline_frames = {state: [pygame.transform.flip(frame, True, False) for frame in frames] for state, frames in outline_frames.items()}
        else:
            pos = list(BATTLE_POSITIONS['right'].values())[pos_index]
            groups = (self.battle_sprites, self.opponent_sprites)
        
        monster_sprite = MonsterSprite(pos, frames, groups, monster, index, pos_index, entity)
        MonsterOutlineSprite(monster_sprite, self.battle_sprites, outline_frames)
        
        #ui
        name_pos = monster_sprite.rect.midleft + vector(16, -70) if entity == 'player' else monster_sprite.rect.midright + vector(-40, -70)
        name_sprite = MonsterNameSprite(name_pos, monster_sprite, self.battle_sprites, self.fonts['regular'])
        anchor = name_sprite.rect.bottomleft if entity == 'player' else name_sprite.rect.bottomright
        MonsterLevelSprite(entity, anchor, monster_sprite, self.battle_sprites, self.fonts['small'])
        MonsterStatSprite(monster_sprite.rect.midbottom + vector (0, 20), monster_sprite, (150, 48), self.battle_sprites, self.fonts['small'])
        
    #battle system
    def check_active(self):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if monster_sprite.monster.initiative >= 100:
                self.update_all_monsters('pause')
                monster_sprite.monster.initiative = 0
                monster_sprite.self_highlight(True)
                self.current_monster = monster_sprite

    def update_all_monsters(self, option):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            monster_sprite.monster.paused = True if option == 'pause' else False
    
    def update(self, dt):
        #updates
        self.battle_sprites.update(dt)
        self.check_active()
        
        #drawing
        self.display_surface.blit(self.bg_surf, (0,0))
        self.battle_sprites.draw(self.current_monster)