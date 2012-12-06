#! /usr/bin/python

import sys, getopt, textwrap

# http://www.pltgames.com/


ROOMS = {}


class Room:
  def __init__(self, name, description, exits,
               resources=None, items=None):
    self.name = name
    self.description = description
    self.exits = exits
    self.furniture = {}
    self.resources = resources or []
    self.inhabitants = {}
    self.items = items or []
    self.visited = False
    self.capacity = float('inf')
    ROOMS[name] = self

  def describe(self, brief=False):
    result = self.name
    if not brief:
      result += '\n' + self.description
      for item in self.items:
        result += '\nThere is ' + an(item) + ' here.'
    return result
          

Room('Outside of a small house',
     'The day is warm and sunny. Butterflies careen about and bees hum from blossom to blossom. The smell of peonies and adventure fills the air.\nYou stand on a poor road running east-west, outside of a small house painted white. There is a mailbox here.',
     { 'east': 'Dirt road',
       'west': 'Tar pit',
       'in': 'Inside the small house',
       },
     )

Room('Inside the small house',
     'The house is decorated in an oppressively cozy country style. There are needlepoints on every wall and pillow, and the furniture is overstuffed and outdated. Against one wall there is a trophy case.',
     { 'out': 'Outside of a small house' })

Room('Dirt road',
     'You stand on a dirt road running east-west. It\'s just a dirt road. Not much more to say about it than that. Should I mention the bees and butterflies again?',
     { 'east': 'Fork in the road',
       'west': 'Outside of a small house',
       },
     resources = ['dirt']
     )

Room('Tar pit',
     'The road leads to a noxious pit of tar. Amidst the tar, out of reach, a tar-encrusted T-rex bobs, half-submerged.',
     { 'east': 'Outside of a small house.' });

Room('Fork in the road',
     'The road leading in from the west forks here. The northeast fork seems to head towards a rocky, hilly area. The road to the southeast is narrower and lined with tall grass.',
     { 'west': 'Dirt road',
       'northeast': 'Mouth of a cave',
       'southeast': 'Grassy knoll', },
     )

Room('Grassy knoll',
     'A path leading from the northwest gives onto a grassy knoll. Upon the knoll is a greasy gnoll. A gnoll is a cross between a gnome and a troll. This particular gnoll is named Bograt, and Bograt, I am sorry to tell you, is a jerk.',
     { 'northwest': 'Fork in the road' })

Room('Deep grass',
     'The grass here is deep. It\'s like a needle in a haystack, minus the needle in here.',
     { 'out': 'Grassy knoll' })

class Furniture:
  def __init__(self, name, description, location,
               capacity=0, contents=None, closed=None, locked=None):
    self.name = name
    self.description = description
    self.capacity = capacity
    self.items = contents or []
    self.closed = closed
    self.locked = locked
    ROOMS[location].furniture[name] = self

  def describe(self, brief=False):
    return 'the ' + self.name if brief else self.description


Furniture('mailbox',
          'A fairly ordinary mailbox, used mostly to receive mail. The kind with a flag on the side and so forth. The number "428" is proudly emblazoned with vinyl stickers on one side.',
          'Outside of a small house',
          capacity = 2,
          closed = True,
          contents = ['letter'])

Furniture('trophy case',
          'This handsome trophy case features space to display up to three treasured items.',
          'Inside the small house',
          capacity = 3,
          closed = True,
          locked = True);

Furniture('tar pit',
          'The tar pit emits noxious fumes and bubbles langoriously from time to time.',
          'Tar pit',
          capacity = float('inf'));


MASS_NOUNS = ['dirt'];


class Npc:
  def __init__(self, name, description, location):
    self.name = name
    self.description = description
    self.capacity = 9
    ROOMS[location].inhabitants[name.lower()] = self

  def describe(self):
    return self.description

  def welcome(self, whom):
    pass


class Bograt(Npc):
  def welcome(self, whom):
    item = whom.items and whom.items[0]
    if item and move(item, whom, ROOMS['Deep grass']):
      say('Goddamn that Bograt. He stole your', item + '. Then he tossed it somewhere into the deep grass.')

Bograt('Bograt',
       'Bograt is a greasy gnoll who lives on a grassy knoll. No two ways about it: he is a jerk.',
       'Grassy knoll');
    

ITEMS = {}

class Item:
  def __init__(self, name, description, mass=False):
    self.name = name
    self.description = description
    self.mass = mass
    

ALIASES = {
  'walk': 'go',
  'get': 'take',
  'grab': 'take',
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
  'into': 'in',
  'inside': 'in',
  'me': 'self',
  'myself': 'self',
}

class Player:
  def __init__(self):
    self.location = ROOMS['Outside of a small house']
    self.items = []
    self.capacity = 9
    self.dead = False
    say(self.location.describe())

  def describe(self):
    return 'You are you. That\'s just who you are.'

  def resolve(self, item):
    if item == 'self':
      return self
    elif item == 'here':
      return self.location
    elif item in self.location.furniture:
      return self.location.furniture[item]
    elif item in self.location.inhabitants:
      return self.location.inhabitants[item]
    else:
      say('What ' + item + '?')

  def inventory(self):
    if self.items:
      say('You are currently holding:')
      for item in self.items:
        say('  ' + Cap(an(item)) + '.')
    else:
      say('You are empty-handed.')

  def go(self, direction):
    self.location = ROOMS[self.location.exits[direction]]
    say(self.location.describe(self.location.visited))
    self.location.visited = True
    for npc in self.location.inhabitants.values():
      npc.welcome(self)

  def drop(self, item):
    if move(item, self, self.location):
      say(item, 'dropped.')
      
  def take(self, item):
    if move(item, self.location, self):
      say(item, 'taken.')


def move(item, source, dest):
  if dest.capacity <= 0:
    say('Not a container!')
    return False
  if len(dest.items) >= dest.capacity:
    say('No more room!')
    return False
  for i in range(len(source.items)):
    if source.items[i] == item:
      source.items[i:1] = []
      dest.items.append(item)
      return True
  if hasattr(source, 'resources') and item in source.resources:
    if item in MASS_NOUNS and item in dest.items:
      say('You already have', an(item) + '.')
      return False
    dest.items.append(item)
    return True
  say('What', item, 'now?')
  return False


def an(item):
  if item in MASS_NOUNS:
    return 'some ' + item
  elif item[0] in 'aeiou':
    return 'an ' + item
  else:
    return 'a ' + item

def Cap(s):
  return s[:1].upper() + s[1:]


VERBOSE = False

def say(*args):
  if VERBOSE:
    for s in Cap(' '.join(args)).split('\n'):
      print textwrap.fill(s)


def parse(player, line):
  ALIASES['this'] = (player.items[-1:]+['this'])[0]
  ALIASES['that'] = (player.location.items[-1:]+['that'])[0]
  words = [ALIASES.get(word,word) for word in line.strip().lower().split()]
  if not words:
    return True
  command = words.pop(0)

  if command == 'quit':
    say('Goodbye!')
    return False

  elif command == 'inventory':
    player.inventory()

  elif command == 'look':
    say(player.location.describe())

  elif command == 'examine':
    say(player.resolve(words[0]).describe())

  elif command == 'go':
    player.go(words.pop(0))

  elif command == 'take':
    available = player.location.items + player.location.resources
    if not available:
      say('Nothing here!')
    else:
      if not words:
        say('Take what?')
      elif words[0] == 'all':
        words = available[:]
      for item in words:
        player.take(item)

  elif command == 'drop':
    if not player.items:
      say('You don\'t have anything to drop!')
    else:
      if not words:
        say('Drop what?')
      elif words[0] == 'all':
        words = player.items[:]
      for item in words:
        player.drop(item)

  elif command == 'put' and len(words) >= 3 and words[1] == 'in':
    dest = player.location.furniture[words[2]]
    if move(words[0], player, dest):
      say('You put the', words[0], 'in the', words[2] + '.')
    
  elif command in player.location.exits.keys():
    # just a direction. "go" is implied
    player.go(command)

  else:
    say('I did not understand that command.')

  return True
    

def execute(player, file=None):
  if file:
    for line in file.readlines():
      say('\n>', line.strip())
      if not parse(player, line):
        break
  else:
    while not player.dead:
      if not parse(player, raw_input('\n> ')):
        break


def main():
  global VERBOSE
  opts,args = getopt.getopt(sys.argv[1:], 'vq')
  VERBOSE = not args
  for o,a in opts:
    if o == '-v':
      VERBOSE = True
    elif o == '-q':
      VERBOSE = False

  say('Welcome to Tarpit Adventure!')
  say()

  player = Player()
  
  if args:
    for i in args:
      execute(player, open(i,'r'))
  else:
    execute(player)

if __name__ == '__main__':
  main()
