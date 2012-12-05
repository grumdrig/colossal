#! /usr/bin/python

import sys

# http://www.pltgames.com/


ROOMS = {}

class Room:
  def __init__(self, name, description, exits,
               furniture=None, resources=None, inhabitants=None, items=None):
    self.name = name
    self.description = description
    self.exits = exits
    self.furniture = furniture or {}
    self.resources = resources or []
    self.inhabitants = inhabitants or []
    self.items = items or []
    self.visited = False
    ROOMS[name] = self

Room('Outside of a small house',
     'The day is warm and sunny. Butterflies careen about and bees hum from blossom to blossom. The smell of peonies and adventure fills the air.\nYou stand on a poor road running east-west, outside of a small house painted white. There is a mailbox here.',
     { 'east': 'Dirt road',
       'west': 'Tar pit',
       'in': 'Inside the small house',
       },
     furniture = { 'mailbox': {'open': False, 'contains': ['letter']} },
     )

Room('Inside the small house',
     'The house is decorated in an oppressively cozy country style. There are needlepoints on every wall and pillow, and the furniture is overstuffed and outdated. Against one wall there is a trophy case.',
     { 'out': 'Outside of a small house' },
     furniture = {
       'trophy case': {'open': False, 'locked': True, 'contains': []},
       }
     )

Room('Dirt road',
     'You stand on a dirt road running east-west. It\'s just a dirt road. Not much more to say about it than that. Should I mention the bees and butterflies again?',
     { 'east': 'Fork in the road',
       'west': 'Outside of a small house',
       },
     resources = ['dirt']
     )

Room('Tar pit',
     'The road leads to a noxious pit of tar. Amidst the tar, out of reach, a tar-encrusted T-rex bobs, half-submerged.',
     { 'east': 'Outside of a small house.' },
     furniture = { 'tar pit': {'contains': []} },
    )

Room('Fork in the road',
     'The road leading in from the west forks here. The northeast fork seems to head towards a rocky, hilly area. The road to the southeast is narrower and lined with tall grass.',
     { 'west': 'Dirt road',
       'northeast': 'Mouth of a cave',
       'southeast': 'Grassy knoll', },
     )

Room('Grassy knoll',
     'A path leading from the northwest gives onto a grassy knoll. Upon the knoll is a greasy gnoll. A gnoll is a cross between a gnome and a troll. This particular gnoll is named Bograt, and Bograt, I am sorry to tell you, is a jerk.',
     { 'northwest': 'Fork in the road' },
     inhabitants = ['Bograt']
     )


NPCs = {
  'Bograt': {
    'description': 'Bograt is a greasy gnoll who lives on a grassy knoll. No two ways about it: he is a jerk.'
    },
  }


ALIASES = {
  'walk': 'go',
  'get': 'take',
  'throw': 'drop',
  'i': 'inventory',
  'l': 'look',
  'n': 'north',
  's': 'south',
  'e': 'east',
  'w': 'west',
  'ne': 'northeast',
  'nw': 'northwest',
  'se': 'southeast',
  'sw': 'southwest',
  'exit': 'out',
  'enter': 'in',
}

class Player:
  def __init__(self):
    self.location = ROOMS['Dirt road']
    self.items = []

    self.go('west')
    say()
    self.inventory()

  def look(self, brief=False):
    import textwrap
    say(self.location.name)
    if not brief:
      say()
      say(textwrap.fill(self.location.description))
      if self.location.items:
        say()
        for item in self.location.items:
          say('There is', item, 'here.')

  def inventory(self):
    if self.items:
      say('You are currently holding:')
      for item in self.items:
        say('-', item)
    else:
      say('You are empty handed.')

  def go(self, direction):
    self.location = ROOMS[self.location.exits[direction]]
    self.look(self.location.visited)
    self.location.visited = True

  def drop(self, item):
    if move(item, self, self.location):
      say(item, 'dropped.')
    else:
      say('You dont have it.')
      
  def take(self, item):
    if len(self.items) >= 9:
      say('You can\'t hold any more!')
      return
    if move(item, self.location, self):
      say(item, 'taken.')
    else:
      say('That isn\'t here to be taken.')


def move(item, source, dest):
  for i in range(len(source.items)):
    if source.items[i] == item:
      source.items[i:1] = []
      dest.items.append(item)
      return True
  if hasattr(source, 'resources') and item in source.resources:
    dest.items.append(item)
    return True
  return False



INTERACTIVE = False

def say(*args):
  #if INTERACTIVE:
  print ' '.join(args).capitalize()

def parse(player, line):
  words = [ALIASES.get(word,word) for word in line.lower().split()]
  print line
  if not words:
    say('Huh?')
    return
  command = words.pop(0)
  if command == 'inventory':
    player.inventory()
  elif command == 'look':
    player.look()
  elif command == 'go':
    player.go(words.pop(0))
  elif command == 'take':
    available = player.location.items + player.location.resources
    if not available:
      say('Nothing here!')
    else:
      if not words:
        words = available[:1]
      elif words[0] == 'all':
        words = available[:]
      for item in words:
        player.take(item)
  elif command == 'drop':
    if not player.items:
      say('You don\'t have anything to drop!')
    else:
      if not words:
        words = player.items[:1]
      elif words[0] == 'all':
        words = player.items[:]
      for item in words:
        player.drop(item)
  elif command in player.location.exits.keys():
    player.go(command)
  else:
    say('I did not understand that command.')
    

def execute(player, file):
  if not INTERACTIVE:
    print '\n>',
  for line in file.readlines():
    parse(player, line)
    if not INTERACTIVE:
      print '\n>',


def main(args):
  global INTERACTIVE
  INTERACTIVE = not args

  say('Welcome to Tarpit Adventure!')
  say()
  player = Player()
  
  if args:
    for i in args:
      execute(player, open(i,'r'))
  else:
    execute(player, sys.stdin)

if __name__ == '__main__':
  main(sys.argv[1:])
