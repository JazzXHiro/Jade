from settings import *
from sprites import MonsterSprite, MonsterNameSprite, MonsterLevelSprite, MonsterStatSprite, MonsterOutlineSprite, AttackSprite, TimedSprite
from groups import BattleSprites
from game_data import ATTACK_DATA
from support import draw_bar
from timer import Timer
from random import choice

class Battle:
    #main
    def __init__(self, player_monsters, opponent_monsters, monster_frames, bg_surf, fonts, end_battle, character, sounds):
        #general
        self.display_surface = pygame.display.get_surface()
        self.bg_surf = bg_surf
        self.monster_frames = monster_frames
        self.fonts = fonts
        self.monster_data = {'player': player_monsters, 'opponent': opponent_monsters} #this is sometimes necessary as sometimes you would wanna update all the monsters.
        self.battle_over = False
        self.end_battle = end_battle
        self.character = character
        self.sounds = sounds

        self.timers = {
            'opponent delay' : Timer(600, func = self.opponent_attack)
        }
        
        #groups
        self.battle_sprites   = BattleSprites()
        self.player_sprites   = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()
        
        #control
        self.current_monster = None
        self.selection_mode = None
        self.selection_side = 'player'
        self.selected_attack = None
        self.indexes = {
            'general' : 0,
            'monster' : 0,
            'attacks' : 0,
            'switch' : 0,
            'target' : 0
        }
        
        self.setup()
        
    def setup(self):
        for entity, monster in self.monster_data.items():
            for index, monster in {k:v for k,v in monster.items() if k <= 2}.items(): #using dictionary comprehension 
                self.create_monster(monster, index, index, entity) #first index is to keep track of the monster and 2nd index is for  monster positioning(battlewindow)
                
            #remove opponent monster data
            for i in range(len(self.opponent_sprites)):
                del self.monster_data['opponent'][i]
        print(self.monster_data['opponent'])
    #pos index is the position of the monster in the battle window
    def create_monster(self, monster, index, pos_index, entity): #purpose of index is to uniquely identify a same entries of a monster
        monster.paused = False
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
        
        monster_sprite = MonsterSprite(pos, frames, groups, monster, index, pos_index, entity, self.apply_attack, self.create_monster)
        MonsterOutlineSprite(monster_sprite, self.battle_sprites, outline_frames)
        
        #ui
        name_pos = monster_sprite.rect.midleft + vector(16, -70) if entity == 'player' else monster_sprite.rect.midright + vector(-40, -70)
        name_sprite = MonsterNameSprite(name_pos, monster_sprite, self.battle_sprites, self.fonts['regular'])
        anchor = name_sprite.rect.bottomleft if entity == 'player' else name_sprite.rect.bottomright
        MonsterLevelSprite(entity, anchor, monster_sprite, self.battle_sprites, self.fonts['small'])
        MonsterStatSprite(monster_sprite.rect.midbottom + vector (0, 20), monster_sprite, (150, 48), self.battle_sprites, self.fonts['small'])
        
    def input(self):
        if self.selection_mode and self.current_monster:
            keys = pygame.key.get_just_pressed()
            
            match self.selection_mode:
                case 'general': limiter = len(BATTLE_CHOICES['full'])
                case 'attacks': limiter = len(self.current_monster.monster.get_abilities(all = False))
                case 'switch': limiter = len(self.available_monsters)
                case 'target': limiter = len(self.opponent_sprites) if self.selection_side == 'opponent' else len(self.player_sprites)
            
            if limiter > 0:
                if keys[pygame.K_DOWN] or keys[pygame.K_RIGHT] or keys[pygame.K_s] or keys[pygame.K_d]:
                    self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] + 1) % limiter
                if keys[pygame.K_UP] or keys[pygame.K_LEFT] or keys[pygame.K_w] or keys[pygame.K_a]:
                    self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] - 1) % limiter
            
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:

                if self.selection_mode == 'switch':
                    index, new_monster = list(self.available_monsters.items())[self.indexes['switch']]
                    self.current_monster.kill()
                    self.create_monster(new_monster, index, self.current_monster.pos_index, 'player')
                    self.selection_mode = None
                    self.update_all_monsters('resume')
                
                if self.selection_mode == 'target':
                    sprite_group = self.opponent_sprites if self.selection_side == 'opponent' else self.player_sprites
                    sprites = {sprite.pos_index: sprite for sprite in sprite_group}
                    if sprites:
                        target_index = self.indexes['target'] % len(sprites)
                        monster_sprite = sprites[list(sprites.keys())[target_index]]
                        
                        if self.selected_attack:
                            self.current_monster.activate_attack(monster_sprite, self.selected_attack)
                            self.selected_attack, self.current_monster, self.selection_mode = None, None, None
                        else:
                            if monster_sprite.monster.health < monster_sprite.monster.get_stat('max_health') * 0.9:
                                self.monster_data['player'][len(self.monster_data['player'])] = monster_sprite.monster
                                monster_sprite.delayed_kill((None))
                                self.update_all_monsters('resume')
                            else:
                                TimedSprite(monster_sprite.rect.center, self.monster_frames['ui']['cross'], self.battle_sprites, 1000)
                
                elif self.selection_mode == 'attacks':
                    self.selection_mode = 'target'
                    self.selected_attack = self.current_monster.monster.get_abilities(all = False)[self.indexes['attacks']]
                    self.selection_side = ATTACK_DATA[self.selected_attack]['target']
                    self.indexes['target'] = 0
                
                elif self.selection_mode == 'general':
                    if self.indexes['general'] == 0:
                        self.selection_mode = 'attacks'
                    
                    elif self.indexes['general'] == 1:
                        self.current_monster.monster.defending = True
                        self.update_all_monsters('resume')
                        self.current_monster, self.selection_mode = None, None
                        self.indexes['general'] = 0
                    
                    elif self.indexes['general'] == 2:
                        self.selection_mode = 'switch'
                    
                    elif self.indexes['general'] == 3:
                        self.selection_mode = 'target'
                        self.selection_side = 'opponent'
            if keys[pygame.K_ESCAPE]:
                if self.selection_mode in ('attacks', 'switch', 'target'):
                    self.selection_mode = 'general'

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()
        
    #battle system
    def check_active(self):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if monster_sprite.monster.initiative >= 100:
                monster_sprite.monster.defending = False
                self.update_all_monsters('pause')
                monster_sprite.monster.initiative = 0
                monster_sprite.self_highlight(True)
                self.current_monster = monster_sprite
                # t1 = len(self.current_monster.monster.get_abilities())
                # print(t1)
                if self.player_sprites in monster_sprite.groups():
                    self.selection_mode = 'general'
                else:
                    self.timers['opponent delay'].activate()
                # only one monster may take a turn per frame; without this a
                # second monster crossing 100 in the same frame overwrites
                # current_monster (e.g. an opponent stealing the player's turn)
                break

    def update_all_monsters(self, option):
        for monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            monster_sprite.monster.paused = True if option == 'pause' else False
            
    def apply_attack(self, target_sprite, attack, amount):
        AttackSprite(target_sprite.rect.center, self.monster_frames['attacks'][ATTACK_DATA[attack]['animation']], self.battle_sprites)
        self.sounds[ATTACK_DATA[attack]['animation']].play()
        
        #get correct attack damage amount (defense, element)
        attack_element = ATTACK_DATA[attack]['element']
        target_element = target_sprite.monster.element
        
        #double attack
        if attack_element == 'fire' and target_element == 'plant' or \
            attack_element == 'water' and target_element == 'fire' or \
            attack_element == 'plant' and target_element == 'water':
            amount *= 2
            
        #halved attack
        if attack_element == 'fire' and target_element == 'water' or \
            attack_element == 'water' and target_element == 'plant' or \
            attack_element == 'plant' and target_element == 'fire':
            amount *= 0.5
            
        target_defense = 1 - target_sprite.monster.get_stat('defense') / 2000
        if target_sprite.monster.defending:
            target_defense -= 0.2
        target_defense = max(0, min(1, target_defense))
    
        
        #update the monster health
        target_sprite.monster.health -= amount * target_defense
        self.check_death()
        
        #resume
        self.update_all_monsters('resume')
        
        # print(target_sprite)
        # print(attack)
        # print(amount)
    
    def check_death(self):
        for monster_sprite in self.opponent_sprites.sprites() + self.player_sprites.sprites():
            if monster_sprite.monster.health <= 0:
                if self.player_sprites in monster_sprite.groups(): #player
                    active_monsters = [(monster_sprite.index, monster_sprite.monster)for monster_sprite in self.player_sprites.sprites()]
                    available_monsters = [(index, monster) for index, monster in self.monster_data['player'].items() if monster.health > 0 and (index, monster) not in active_monsters]
                    if available_monsters:
                        new_monster_data = [(monster, index, monster_sprite.pos_index, 'player') for index, monster in available_monsters][0]
                    else:
                        new_monster_data = None
                else:
                    new_monster_data = (list(self.monster_data['opponent'].values())[0], monster_sprite.index, monster_sprite.pos_index, 'opponent') if self.monster_data['opponent'] else None
                    if self.monster_data['opponent']:
                        del self.monster_data['opponent'][min(self.monster_data['opponent'])]
                        
                    #xp
                    xp_amount = monster_sprite.monster.level * 100 / len(self.player_sprites)
                    for player_sprite in self.player_sprites:
                        player_sprite.monster.update_xp(xp_amount)
                        # print(player_sprite.monster.xp)
                        
                monster_sprite.delayed_kill(new_monster_data)
                    
    def opponent_attack(self):
        # the delay timer may fire after the active monster is gone (killed or
        # its turn already resolved), so guard before dereferencing it
        if not self.current_monster:
            return
        ability = choice(self.current_monster.monster.get_abilities())
        random_target = choice(self.opponent_sprites.sprites()) if ATTACK_DATA[ability]['target'] == 'player' else choice(self.player_sprites.sprites())
        self.current_monster.activate_attack(random_target, ability)

    def check_end_battle(self):
        # opponents have been defeated
        if len(self.opponent_sprites) == 0 and not self.battle_over:
            self.battle_over = True
            self.end_battle(self.character)
            for monster in self.monster_data['player'].values():
                monster.initiative = 0

        # player has been defeated
        if len(self.player_sprites) == 0:
            pygame.quit()
            exit()
    
    #ui
    def draw_ui(self):
        if self.current_monster:
            if self.selection_mode == 'general':
                self.draw_general()
            if self.selection_mode == 'attacks':
                self.draw_attacks()
            if self.selection_mode == 'switch':
                self.draw_switch()
    
    def draw_general(self):
        for index, (option, data_dict) in enumerate(BATTLE_CHOICES['full'].items()):
            # print(index, option, data_dict)
            if index == self.indexes['general']:
                surf = self.monster_frames['ui'][f"{data_dict['icon']}_highlight"]
            else:
                surf = pygame.transform.grayscale(self.monster_frames['ui'][data_dict['icon']])
            rect = surf.get_frect(center = self.current_monster.rect.midright + data_dict['pos'])
            self.display_surface.blit(surf, rect)
            
    def draw_attacks(self):
        #data
        abilities = self.current_monster.monster.get_abilities(all = False)
        width, height = 150, 200
        visible_attacks = 4
        item_height = height / visible_attacks
        v_offset = 0 if self.indexes['attacks'] < visible_attacks else -(self.indexes['attacks'] - visible_attacks + 1) * item_height
        
        #bg
        bg_rect = pygame.FRect((0,0), (width,height)).move_to(midleft = self.current_monster.rect.midright + vector(20,0))
        pygame.draw.rect(self.display_surface, COLORS['white'], bg_rect, 0, 5)
        
        for index, ability in enumerate(abilities):
            selected = index == self.indexes['attacks']
            
            #text
            if selected:
                element = ATTACK_DATA[ability]["element"]
                text_color = COLORS[element] if element!= 'normal' else COLORS['black']
            else:
                text_color = COLORS['light']
            text_surf = self.fonts['regular'].render(ability, False, text_color)
            
            #rect
            text_rect = text_surf.get_frect(center = bg_rect.midtop + vector(0, item_height / 2 + index * item_height + v_offset))
            text_bg_rect = pygame.FRect((0,0), (width, item_height)).move_to(center = text_rect.center)
            
            #draw
            if bg_rect.collidepoint(text_rect.center):
                if selected:
                    if text_bg_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(self.display_surface, COLORS['skin_sand'], text_bg_rect,0,0,5,5)
                    elif text_bg_rect.collidepoint(bg_rect.midbottom + vector(0,-1)):
                        pygame.draw.rect(self.display_surface, COLORS['skin_sand'], text_bg_rect,0,0,0,0,5,5)
                    else:
                        pygame.draw.rect(self.display_surface, COLORS['skin_sand'], text_bg_rect)
                self.display_surface.blit(text_surf, text_rect)
    
    def draw_switch(self):
		# data 
        width, height = 300, 320
        visible_monsters = 4
        item_height = height / visible_monsters
        v_offset = 0 if self.indexes['switch'] < visible_monsters else -(self.indexes['switch'] - visible_monsters + 1) * item_height
        bg_rect = pygame.FRect((0,0), (width, height)).move_to(midleft = self.current_monster.rect.midright + vector(20,0))
        pygame.draw.rect(self.display_surface, COLORS['white'], bg_rect, 0, 5)

		# monsters 
        active_monsters = [(monster_sprite.index, monster_sprite.monster) for monster_sprite in self.player_sprites]
        self.available_monsters = {index: monster for index, monster in self.monster_data['player'].items() if (index, monster) not in active_monsters and monster.health > 0}

        for index, monster in enumerate(self.available_monsters.values()):
            selected = index == self.indexes['switch']
            item_bg_rect = pygame.FRect((0,0), (width, item_height)).move_to(midleft = (bg_rect.left, bg_rect.top + item_height / 2 + index * item_height + v_offset))

            icon_surf = self.monster_frames['icons'][monster.name]
            icon_rect = icon_surf.get_frect(midleft = bg_rect.topleft + vector(10,item_height / 2 + index * item_height + v_offset))
            text_surf = self.fonts['regular'].render(f'{monster.name} ({monster.level})', False, COLORS['red'] if selected else COLORS['black'])
            text_rect = text_surf.get_frect(topleft = (bg_rect.left + 90, icon_rect.top))

            # selection bg
            if selected:
                if item_bg_rect.collidepoint(bg_rect.topleft):
                    pygame.draw.rect(self.display_surface, COLORS['skin_sand'], item_bg_rect, 0, 0, 5, 5)
                elif item_bg_rect.collidepoint(bg_rect.midbottom + vector(0,-1)):
                    pygame.draw.rect(self.display_surface, COLORS['skin_sand'], item_bg_rect, 0, 0, 0, 0, 5, 5)
                else:
                    pygame.draw.rect(self.display_surface, COLORS['skin_sand'], item_bg_rect)

            if bg_rect.collidepoint(item_bg_rect.center):
                for surf, rect in ((icon_surf, icon_rect), (text_surf, text_rect)):
                    self.display_surface.blit(surf, rect)
                health_rect = pygame.FRect((text_rect.bottomleft + vector(0,4)), (100,4))
                energy_rect = pygame.FRect((health_rect.bottomleft + vector(0,2)), (80,4))
                draw_bar(self.display_surface, health_rect, monster.health, monster.get_stat('max_health'), COLORS['red'], COLORS['black'])
                draw_bar(self.display_surface, energy_rect, monster.energy, monster.get_stat('max_energy'), COLORS['blue'], COLORS['black'])
        
    def update(self, dt):
        #updates
        self.check_end_battle()
        self.input()
        self.update_timers()
        self.battle_sprites.update(dt)
        self.check_active()
                
        #drawing
        self.display_surface.blit(self.bg_surf, (0,0))
        self.battle_sprites.draw(self.current_monster, self.selection_side, self.selection_mode, self.indexes['target'], self.player_sprites, self.opponent_sprites)
        self.draw_ui()