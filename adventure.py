#! /usr/bin/python

import sys, random, getopt, textwrap

# http://www.pltgames.com/


ROOMS = {}


def find(q, vessel):
  return [o for o in vessel.items if o.match(q)]
  

class Room:
  def __init__(self, name, description, exits, resources=None, items=None):
    self.name = name
    self.description = description
    self.exits = exits
    self.furniture = {}
    self.resources = resources or {}
    self.inhabitants = {}
    self.items = [Item(item) for item in items or []]
    self.capacity = float('inf')
    ROOMS[name] = self

  def __str__(self):
    return self.name

  def describe(self, brief=False):
    result = self.name
    if not brief:
      result += '\n' + self.description
      for item in self.items:
        result += '\nThere is ' + item.describe(True) + ' here.'
    return result
          

class Furniture:
  def __init__(self, name, description, location,
               capacity=0, contents=None, closed=None, locked=None):
    self.name = name
    self.description = description
    self.capacity = capacity
    self.items = [Item(item) for item in contents or []]
    self.closed = closed
    self.locked = locked
    ROOMS[location].furniture[name] = self

  def __str__(self):
    return self.name

  def describe(self, brief=False):
    result = 'the ' + self.name if brief else self.description
    if not brief and not self.closed and self.items:
      result += '\nThe ' + self.name + ' contains:'
      for item in self.items:
        result += '\n  ' + Cap(item.describe(True)) + '.'
    return result


ADJECTIVES = [
  'common', 'regular', 'ordinary', 'everyday', 'humdrum', 'normal',
  'quotidian', 'run-of-the-mill', 'standard', 'typical', 'conventional',
  'orthodox', 'garden-variety', 'undistinguished', 'average',
  'unexceptional', 'bland', 'conventional', 'mundane', 'ordinary',
  'stereotypical', 'boilerplate', 'characterless', 'prosaic', 'unnoteworthy']

INSCRIBED = [
  'inscribed', 'written-upon', 'marked-up', 'filled-in', 'used',
  'readable'
  ]

MASS_NOUNS = ['dirt'];


class Item:
  def __init__(self, type, adj=False):
    if len(type.split(' ')) > 1:
      self.adjective, self.type = type.split(' ')
    else:
      self.type = type
      self.adjective = adj and random.choice(ADJECTIVES)
    self.location = None
    self.writing = None
    mass = type in MASS_NOUNS
    self.an = 'some' if mass else 'an' if self.type[0] in 'aeiou' else 'a'

  def __str__(self):
    return (self.adjective + ' ' if self.adjective else '') + self.type

  def describe(self, brief=False):
    if brief:
      return self.an + ' ' + str(self)
    elif self.writing:
      result = self.an + ' ' + str(self) + '. Written on it, it says:'
      for line in self.writing:
        result += '\n  ' + line
      return result
    else:
      return 'Just ' + self.an + ' ' + str(self)

  def match(self, q):
    if not q:
      return None
    if q[0] == 'all':
      return self
    elif q[0] == 'it':
      q.pop(0)
      return self
    result = None
    if q and q[0] == self.adjective:
      result = self
      q.pop(0)
    if q and q[0] == self.type:
      result = self
      q.pop(0)
    return result
    
  def move(self, dest):
    if dest and (dest.capacity <= 0):
      say('Not a container!')
      return False
    if dest and (len(dest.items) >= dest.capacity):
      say('No more room!')
      return False
    if self.location:
      self.location.items.remove(self)
    if dest:
      dest.items.append(self)
    self.location = dest
    return True



class Entity:
  def __init__(self, name, description, location):
    self.name = name
    self.description = description
    self.location = None
    self.items = []
    self.capacity = 9
    self.go(ROOMS[location])

  def describe(self):
    return self.description

  def resolve(self, q):
    if not q: return None
    item = q[0]
    if item == 'self':
      return self
    elif item == 'here':
      return self.location
    elif item in self.location.furniture:
      return self.location.furniture[item]
    elif item in self.location.inhabitants:
      return self.location.inhabitants[item]
    else:
      items = find([item], self) or find([item], self.location)
      return items and items[0] or None

  def inventory(self):
    if self.items:
      say('You are currently holding:')
      for item in self.items:
        say('  ' + Cap(item.describe(True)) + '.')
    else:
      say('You are empty-handed.')

  def go(self, location):
    if self.location:
      del self.location.inhabitants[self.name.lower()]
      if isinstance(location, str):
        location = ROOMS[self.location.exits[location]]
      say(location.describe(location.name in self.visited))
    self.location = location
    self.location.inhabitants[self.name.lower()] = self
    for npc in self.location.inhabitants.values():
      npc.welcome(self)

  def welcome(self, whom):
    pass

  def parse(self, line):
    words = [ALIASES.get(word,word) for word in line.strip().lower().split()]
    if not words:
      return True
    command = words.pop(0)

    if command == 'quit':
      say('Goodbye!')
      return False

    elif command == 'inventory':
      self.inventory()

    elif command == 'look':
      thing = self.resolve(words) if words else self.location
      say(thing.describe() if thing else 'What ' + words[0] + '?')

    elif command == 'go':
      self.go(words.pop(0))

    elif command == 'take':
      items = find(words, self.location)
      for furn in self.location.furniture.values():
        if not items and not furn.closed:
          items = find(words, furn)
      if not items:
        say("I can't take what ain't there.")
      else:
        for item in items:
          if item.move(self):
            say(str(item), 'taken.')

    elif command == 'drop':
      items = find(words, self)
      if not items:
        say("You can't drop what you ain't got.")
      else:
        for item in items:
          if item.move(self.location):
            say(str(item), 'dropped.')

    elif command == 'put' and len(words) >= 3 and words[1] == 'in':
      dest = self.location.furniture[words[2]]
      items = find(words, self)
      if not items:
        say("You can't put what you ain't got.")
      elif dest.closed:
        say("The " + str(dest) + " is closed.")
      else:
        for item in items:
          if item.move(dest):
            say('You put the ' + str(item) + ' in the ' + str(dest) + '.')

    elif command == 'open':
      what = self.resolve(words)
      if not what:
        say('Open what?')
      elif not what.closed:
        say('The', str(what), 'is not closed.')
      elif what.locked:
        say('The', str(what), 'is locked.')
      else:
        what.closed = False
        say('The', str(what), 'is now open.')

    elif command == 'close':
      what = self.resolve(words)
      if not what:
        say('Close what?')
      elif what.closed != False:
        say('The', str(what), 'is not open.')
      else:
        what.closed = True
        say('The', str(what), 'is now closed.')

    elif command == 'write':
      if not find(['pen'], self):
        say('You lack a writing implement.')
      else:
        papers = find(['blank'], self)
        if not papers:
          say('You need some blank paper to write on.')
        elif not words:
          say('What do you want to write?')
        else:
          paper = papers[0]
          paper.writing = [line.strip() for line in ' '.join(words).split(';')]
          paper.adjective = random.choice(INSCRIBED)

    elif command == 'dig':
      if not find(['shovel'], self):
        say('Dig with what?')
      elif command not in self.location.resources:
        say('Dig in what?')
      else:
        item = Item(self.location.resources[command], True)
        if item.move(self):
          say('You dig up some ' + str(item) +
              ' and add it to your inventory.');

    elif command in self.location.exits.keys():
      # just a direction. "go" is implied
      self.go(command)

    else:
      say('I did not understand that command.')

    return True

  def execute(self, file=None):
    if file:
      for line in file.readlines():
        say('\n>', line.strip())
        if not self.parse(line):
          break
    else:
      while True:
        if not self.parse(raw_input('\n> ')):
          break

    

class Player(Entity):
  def __init__(self, location):
    self.visited = set()
    Entity.__init__(self,
                    "You",
                    "You are you. That's just who you are.",
                    location)

  def welcome(self, whom):
    if self == whom:
      self.visited.add(self.location.name)



Room('Outside of a small house',
     'The day is warm and sunny. Butterflies careen about and bees hum from blossom to blossom. The smell of peonies and adventure fills the air.\nYou stand on a poor road running east-west, outside of a small house painted white. There is a mailbox here.',
     { 'east': 'Dirt road',
       'west': 'Tar pit',
       'in': 'Inside the small house',
       },
     items=['blank paper', 'pen'],
     )

Room('Inside the small house',
     'The house is decorated in an oppressively cozy country style. There are needlepoints on every wall and pillow, and the furniture is overstuffed and outdated. Against one wall there is a trophy case.',
     { 'out': 'Outside of a small house' })

# Use this is some other description:
# It\'s just a dirt road. Not much more to say about it than that. Should I mention the bees and butterflies again?
Room('Dirt road',
     "You stand on a dirt road running east-west. The road is dirt. It's quite dirty. Beside the road is also dirt; there's dirt everywhere, in fact. Piles and piles of dirt, all around you!",
     { 'east': 'Fork in the road',
       'west': 'Outside of a small house' },
     resources={ 'dig': 'dirt' },
     items=['shovel'])

Room('Tar pit',
     'The road leads to a noxious pit of tar. Amidst the tar, out of reach, a tar-encrusted T-rex bobs, half-submerged.',
     { 'east': 'Outside of a small house.' });

Room('Fork in the road',
     'The road leading in from the west forks here. The northeast fork seems to head towards a rocky, hilly area. The road to the southeast is narrower and lined with tall grass.',
     { 'west': 'Dirt road',
       'northeast': 'Mouth of a cave',
       'southeast': 'Grassy knoll', })

Room('Grassy knoll',
     'A path leading from the northwest gives onto a grassy knoll. Upon the knoll is a greasy gnoll. A gnoll is a cross between a gnome and a troll. This particular gnoll is named Bograt, and Bograt, I am sorry to tell you, is a jerk.',
     { 'northwest': 'Fork in the road' })

Room('Deep grass',
     'The grass here is deep. It\'s like a needle in a haystack, minus the needle in here.',
     { 'out': 'Grassy knoll' })

Furniture('mailbox',
          'A fairly ordinary mailbox, used mostly to receive mail. The kind with a flag on the side and so forth. The number "428" is proudly emblazoned with vinyl stickers on one side.',
          'Outside of a small house',
          capacity=2,
          closed=True,
          contents=['letter'])

Furniture('trophy case',
          'This handsome trophy case features space to display up to three treasured items.',
          'Inside the small house',
          capacity=3,
          closed=True,
          locked=True);

Furniture('tar pit',
          'The tar pit emits noxious fumes and bubbles langoriously from time to time.',
          'Tar pit',
          capacity=float('inf'));

class Bograt(Entity):
  def welcome(self, whom):
    if self != whom:
      item = whom.items and whom.items[0]
      if item and item.move(ROOMS['Deep grass']):
        say('Goddamn that Bograt. He stole your', item.describe(True) + '. Then he tossed it somewhere into the deep grass.')

Bograt('Bograt',
       'Bograt is a greasy gnoll who lives on a grassy knoll. No two ways about it: he is a jerk.',
       'Grassy knoll');



def Cap(s):
  return s[:1].upper() + s[1:]


VERBOSE = False

def say(*args):
  if VERBOSE:
    for s in Cap(' '.join(args)).split('\n'):
      print textwrap.fill(s)


ALIASES = {
  'walk': 'go',
  'get': 'take',
  'grab': 'take',
  'throw': 'drop',
  'i': 'inventory',
  'l': 'look',
  'examine': 'look',
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
  'yourself': 'self',
}


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

  player = Player('Outside of a small house')
  say(player.location.describe())
  
  if args:
    for i in args:
      player.execute(open(i,'r'))
  else:
    player.execute()

if __name__ == '__main__':
  main()
