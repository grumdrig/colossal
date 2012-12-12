#! /usr/bin/python

import sys, random, getopt, textwrap, shlex


ROOMS = { }  # Mapping from room names to rooms
DIRECTIONS = set()  # All possible directions one might go

class Vessel:
  def __init__(self, capacity=0, closed=None, locked=None):
    self.items = []
    self.capacity = capacity or 0
    self.closed = closed
    self.locked = locked
    
  def find(self, q):
    return [o for o in self.items if o.match(q)]

  def findOne(self, q):
    items = self.find(q)
    return items[0] if len(items) == 1 else None

  def onTake(self, item): pass
  def onArrive(self): pass

  

class Room(Vessel):
  def __init__(self, name, description, exits, resources=None):
    Vessel.__init__(self, capacity=float('inf'))
    self.name = name
    self.description = description
    self.exits = exits
    global DIRECTIONS
    DIRECTIONS |= set(exits.keys())
    self.resources = resources or {}
    ROOMS[name] = self

  def __str__(self):
    return self.name

  def describe(self, brief=False):
    if brief:
      return self.name
    result = self.name.upper()
    if not brief:
      result += '\n\n' + self.description
      for item in self.items:
        if item.type != 'You':
          result += '\n\nThere is ' + item.describe(True) + ' here.'
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


class Item(Vessel):
  def __init__(self, type, location, description=None,
               capacity=0, closed=None, locked=None):
    Vessel.__init__(self, capacity=capacity, closed=closed, locked=locked)
    if len(type.split(' ')) > 1:
      self.adjective, self.type = type.split(' ')
    else:
      self.type = type
      self.adjective = None
    self.name = None
    self.location = None
    self.fixed = False
    self.writing = []
    mass = type in MASS_NOUNS
    self.an = 'some' if mass else 'an' if self.type[0] in 'aeiou' else 'a'
    self.description = description or "It's " + self.an + ' ' + str(self) + '.'
    if location: self.move(location)

  def __str__(self):
    result = (self.adjective + ' ' if self.adjective else '') + self.type
    if self.name:
      result += ' called "' + self.name + '"'
    return result

  def describe(self, brief=False):
    if brief:
      return self.an + ' ' + str(self)
    result = self.description
    if self.writing:
      result += ' Written on it are these words:'
      for line in self.writing:
        result += '\n  ' + line
    if not self.closed and self.items:
      result += '\nThe ' + self.type + ' contains:'
      for item in self.items:
        result += '\n  ' + Cap(item.describe(True)) + '.'
    return result

  def write(self, text):
    self.writing += [line.strip() for line in text.split(';')]

  def match(self, q):
    def q0(b):
      return q and b and q[0].lower() == b.lower()
    if not q:
      return None
    if q0('all'):
      return not self.fixed and self
    elif q0('it'):
      q.pop(0)
      return self
    elif q0(self.name):
      q.pop(0)
      return self
    result = None
    if q0(self.adjective):
      result = self
      q.pop(0)
    if q0(self.type):
      result = self
      q.pop(0)
    return result
    
  def move(self, dest, *message):
    if self.fixed and (self.location and dest):
      say('The', self, "can't be moved.")
      return False
    if isinstance(dest, str):
      dest = ROOMS[dest]
    if dest and (dest.capacity <= 0):
      say('Not a container!')
      return False
    if dest and (len(dest.items) >= dest.capacity):
      say('No more room!')
      return False
    if self.location:
      self.location.items.remove(self)
    self.location = dest
    if message:
      say(*message)
    if dest:
      dest.items.append(self)
      self.onArrive()
      dest.onTake(self)
    return True


class Furniture(Item):
  def __init__(self, type, location, description=None,
               capacity=float('inf'), closed=None, locked=None):
    Item.__init__(self, type, location, description=description,
                  capacity=capacity, closed=closed, locked=locked)
    self.fixed = True


VERBS = {}

class Verb:
  def __init__(self, usage):
    usage = usage.split(' ')
    self.verb = usage.pop(0).lower()
    self.pps = {}
    self.object = None
    def parseparam(param):
      result = { 'optional': param[-1] == '?' }
      if result['optional']:
        param = param[:-1]
      object = param.split(':')
      result['name'] = object[0] or object[1]
      result['type'] = len(object) > 1 and object[1]
      return result
    while usage:
      if usage[0] == usage[0].upper():
        preposition = usage.pop(0).lower()
        self.pps[preposition] = parseparam(usage.pop(0))
      else:
        self.object = parseparam(usage.pop(0))
    VERBS[self.verb] = self

  def do(self, subject, input):
    input = input[:]
    arguments = {}
    while input:
      word = input.pop(0)
      if word.lower() in self.pps:
        pp = self.pps[word.lower()]
        item = input.pop(0)
        obj = subject.resolve([item])
        if not obj:
          return say('What ' + item + '?')
        if pp['type'] and pp['type'] != obj.type:
          return say('The', obj, "can't be used for that.")
        arguments[pp['name']] = obj
      elif not self.object or self.object['name'] in arguments:
        return say('You lost me at "' + word + '".')
      elif self.object['type'] == 'str':
        arguments[self.object['name']] = word
      else:
        obj = subject.resolve([word])
        if not obj:
          return say('What ' + word + '?')
        arguments[self.object['name']] = obj
    if (self.object and
        self.object['name'] not in arguments and
        not self.object['optional']):
      return say(self.verb, 'what?', self.object)
    for p,v in self.pps.items():
      if v['name'] not in arguments and not v['optional']:
        return say(self.verb, p, 'what?')
    getattr(subject, self.verb)(**arguments)
          

class Entity(Item):
  def __init__(self, type, location, description):
    Item.__init__(self, type, location, description, capacity=9)
    self.fixed = True

  def resolve(self, q):
    if not q: return None
    item = q[0]
    if item == 'self':
      return self
    elif item == 'here':
      return self.location
    else:
      items = self.find([item]) or self.location.find([item])
      return items and items[0] or None

  Verb('INVENTORY')
  def inventory(self):
    if self.items:
      say('You are currently holding:')
      for item in self.items:
        say('  ' + Cap(item.describe(True)) + '.')
    else:
      say('You are empty-handed.')

  Verb('GO direction:str')
  def go(self, direction):
    if direction not in self.location.exits:
      say("You can't go that way.")
    else:
      location = ROOMS[self.location.exits[direction]]
      self.move(None)
      self.move(location)

  Verb('WRITE text:str WITH :pen ON paper:parchment')
  def write(self, text, pen, paper):
    paper.write(text)
    say('You write on the', str(paper) + '.')

  Verb('DIG WITH :shovel')
  def dig(self, shovel):
    if 'dig' not in self.location.resources:
      say("Digging here is fruitless.")
    else:
      item = Item(self.location.resources['dig'], None)
      if item.move(self):
        say('You dig up some', item, 'and add it to your inventory.');

  Verb('ERASE :parchment')
  def erase(self, parchment):
    parchment.writing = []
    say('You erase everything written on ' + str(parchment) + '.')

  Verb('LOOK thing?')
  def look(self, thing=None):
    say((thing or self.location).describe())


  def parse(self, line, depth=0):
    words = [ALIASES.get(word,word) for word in shlex.split(line.strip())]
    if not words:
      return True
    command = words.pop(0).lower()

    if command == 'quit':
      say('Goodbye!')
      return False

    elif command == 'take':
      items = self.location.find(words)
      for furn in self.location.items:
        if not items and not furn.closed:
          items = furn.find(words)
      if not items:
        say("I can't take what ain't there.")
      else:
        for item in items:
          if item.move(self):
            say(str(item), 'taken.')

    elif command == 'drop':
      items = self.find(words)
      if not items:
        say("You can't drop what you ain't got.")
      else:
        for item in items:
          item.move(self.location, str(item), 'dropped.')

    elif command == 'call':
      items = self.find(words)
      if len(items) != 1:
        say("Call what what?")
      elif not words:
        say ('Call it what?')
      else:
        items[0].name = words[0]
      
    elif command == 'put' and len(words) >= 3 and words[1] == 'in':
      items = self.find(words)
      if not items:
        say("You can't put what you ain't got.")
      elif words.pop(0) != 'in':
        say("I did not understand that.")
      else:
        dest = self.location.findOne(words)
        if not dest:
          say("Where?")
        elif dest.closed:
          say("The " + str(dest) + " is closed.")
        else:
          for item in items:
            item.move(dest, 'You put the', item, 'in the', str(dest) + '.')

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
        what.onClose()

    elif command == 'unlock':
      what = self.resolve(words)
      if not what:
        say('Unlock what?')
      elif not what.locked:
        say('The', what, 'is not locked.')
      else:
        what.locked = False
        say('You unlock the', str(what) + '.')

    elif command == 'lock':
      what = self.resolve(words)
      if not what:
        say('Unlock what?')
      elif what.locked != False:
        say('The', what, 'is not unlocked.')
      else:
        what.locked = True
        say('You lock the', str(what) + '.')

    elif command == 'execute':
      orders = self.find(words)
      if len(orders) != 1:
        say('Execute what, exactly?')
      else:
        for line in orders[0].writing:
          say('>' * (depth+2), line)
          self.parse(line, depth+1)

    elif command == 'xyzzy':
      say('Nothing happens.')

    elif command in DIRECTIONS:
      self.go(command)

    elif command in VERBS:
      VERBS[command].do(self, words)

    else:
      say('I did not understand that.')

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
                    location,
                    "You are you. That's just who you are.")
  def onArrive(self):
    say(self.location.describe(self.location.name in self.visited))
    self.visited.add(self.location.name)



####################################################

osh = Room('Outside of a small house',
           'The day is warm and sunny. Butterflies careen about and bees hum from blossom to blossom. The smell of peonies and adventure fills the air.\nYou stand on a poor road running east-west, outside of a small house painted white.',
           { 'east': 'Dirt road',
             'west': 'Crossroads',
             'cheat': 'Cheaterville',
             'in': 'Inside the small house' })
Item('blank parchment', osh)
mb = Furniture('mailbox',
               osh,
               'A fairly ordinary mailbox, used mostly to receive mail. The kind with a flag on the side and so forth. The number "428" is proudly emblazoned with vinyl stickers on one side.',
               capacity=2,
               closed=True)
Item('letter', mb)

####################################################

cv = Room('Cheaterville',
          'Nothing to see here. Move along.',
          { 'uncheat': osh })
Item('parchment', cv).name = 'pp'
Item('pen', cv).name = 'pn'

####################################################

Room('Inside the small house',
     'The house is decorated in an oppressively cozy country style. There are needlepoints on every wall and pillow, and the furniture is overstuffed and outdated.',
     { 'out': 'Outside of a small house' })
class TrophyCase(Furniture):
  def onClose(self):
    if self.items:
      say('AN INFINITE EXHILARATION THRUMS IN YOUR HEART')
      for item in self.items:
        output(item.writing)
        say('The', item, 'vanishes!')
        item.move(None)
TrophyCase('trophy case',
           'Inside the small house',
           'Against one overdecorated wall there is a trophy case. This handsome case offers display space for a few treasured items.',
           capacity=3,
           closed=True,
           locked=True);

####################################################

Room('Dirt road',
     "You stand on a dirt road running east-west. The road is dirt. It's quite dirty. Beside the road is also dirt; there's dirt everywhere, in fact. Piles and piles of dirt, all around you!",
     { 'east': 'Fork in the road',
       'west': 'Outside of a small house' },
     resources={ 'dig': 'dirt' })
Item('shovel', 'Dirt road')

####################################################

class TarPit(Room):
  def onTake(self, item):
    item.move(None)
    say('The', item, 'sinks into the tar!')
TarPit('Tar pit',
       'The road leads to a noxious pit of tar. It emits noxious fumes and bubbles langoriously from time to time. Amidst the tar, out of reach, a tar-encrusted T-rex bobs, half-submerged.',
       { 'east': 'Outside of a small house' });

####################################################

Room('Crossroads',
     'You stand at a crossroads. Also, there are roads leading in all the cardinal directions.',
     { 'north': 'Dunno...',
       'south': 'Not sure',
       'east': 'Outside of a small house',
       'west': 'Tar pit' });
Item('devil', 'Crossroads',
     "This is the Lord Beelzebub. Satan. Lucifer. You've heard the stories. He's just hanging around here, not really doing too much. Just thinking about stuff.").name = 'Satan'

####################################################

Room('Dunno...',
     "I'm not sure what we're looking at here. I just don't know how to describe it. It's just...\nThe road continues north-south. Other than that it's just really indescribable. (Sorry.)",
     { 'north': 'TODO',
       'south': 'Crossroads' })
Item('something', 'Dunno...',
     'What the hell is this thing?')

####################################################

Room('Fork in the road',
     'The road leading in from the west forks here. The northeast fork seems to head towards a rocky, hilly area. The road to the southeast is narrower and lined with tall grass. Not much more to say about it than that. Should I mention the bees and butterflies again?',
     { 'west': 'Dirt road',
       'northeast': 'Mouth of a cave',
       'southeast': 'Grassy knoll', })

####################################################

class GrassyKnoll(Room):
  def onTake(self, whom):
    if whom.type == 'You':
      item = whom.items and random.choice(whom.items)
      if item and item.move(ROOMS['Deep grass']):
        say('Goddamn that Bograt. He stole your', str(item) + '. Then he tossed it somewhere into the deep grass.')
GrassyKnoll('Grassy knoll',
            'A path leading from the northwest gives onto a grassy knoll. The knoll is home to a greasy gnoll. A gnoll is a cross between a gnome and a troll. This particular gnoll is named Bograt, and Bograt, I am sorry to tell you, is a jerk.',
            { 'northwest': 'Fork in the road' })
Item('gnoll',
     'Grassy knoll',
     'Bograt is a greasy gnoll who lives on a grassy knoll. No two ways about it: he is a jerk.').name = 'Bograt'

####################################################

Room('Deep grass',
     "The grass here is deep. It's like a needle in a haystack, minus the needle in here.",
     { 'out': 'Grassy knoll' })

####################################################

Room('Mouth of a cave',
     "The jaws of a cave yawn before you. To continue the metaphor, the cave's acrid breath recalls overcooked garlic bread. Sharp teeth (and here I'm hinting at stactites and stalagmites) gnash (poetically speaking) at the lips of the cave. I think that's descriptive enough.",
     { 'southwest': 'Fork in the road',
       'north': 'Cave foyer',
       'in': 'Cave foyer' })

####################################################

Room('Cave foyer',
     "Immediately inside the entrance to the cave, it opens up to a vaulted entryway. The skeletal remains and equipment of what must be the world's absolute worst spelunker slump against one wall. Deeper into the cave, a low passage winds north.",
     { 'out': 'Mouth of a cave',
       'south': 'Mouth of a cave',
       'north': 'Narrow passage' })
pack = Item('backpack', 'Cave foyer', capacity=6)
Item('pen', pack)
Item('journal page', pack).write('August 13;;Down to my last stick of gum. I should have brought more food and less gum.;;The exit from this cave must be somewhere around here, but I lack the strength to keep looking.;;...')

####################################################

Room('Narrow passage',
     "The passage soon becomes so low you have to belly crawl to get anywhere. It's also dark, very dark. The walls press your sides, unyielding cold stone. Despite the chill, sweat beads your brow. There is scuffling sound behind you. A footstep? No, no. You feel like you're suffocating. Is that a dim glow up ahead? Please let it be so...",
     { 'south': 'Cave foyer',
       'north': 'Chamber' });

####################################################

Room('Chamber',
     "Small fissures in the ceiling allow a bit of daylight to filter into this fairly roomy chamber. Passages extend in all four directions.",
     { 'south': 'Narrow passage',
       'north': 'North chamber',
       'east': 'East chamber',
       'west': 'West chamber' })
Entity('robot', 'Chamber',
       "Picure Bender from Futurama, without the drinking problem. That's pretty much this robot. Not that he's without his problems though; his problem is overenthusiasm.").name = 'Floyd'

####################################################

Room('North chamber',
     "The rough, natural passage entering this chamber from the south, not to mention the craggy subterranean setting in general, contrast sharply with the professional glass and steel facade to the north. The design work is modern and impeccable. Lettered over the door in 900pt Helvetica are the words:\n  Calloway, Papermaster, Turban and Hoyt LLC\n               Attorneys at Law",
     { 'south': 'Chamber',
       'north': 'Reception' })

####################################################

Room('Reception',
     "The room's centerpiece is an all-glass desk providing a clear view of the receptionist's knees, were there a receptionist present. Convenient to the desk is a document shredder.\nThe office exit is to the south, a doorway to a small room lies east and a hallway stretches to the north.",
     { 'south': 'North chamber',
       'north': 'Hallway',
       'east': 'Copier room' })
class Shredder(Furniture):
  def onTake(self, item):
    if item.type == 'parchment' and len(item.writing) > 1:
      item.move(None)
      for shred in item.writing:
        Item('shredded parchment', self).write(shred)
      say('The', item, 'is shredded into', str(len(item.writing)), 'strips.')
Shredder('shredder', 'Reception', 'Model 8678b Vellum Shredder. "For When You\'ve Got Something to Hide". (You may have missed it, but that was a pun, just there.)')

#-------------------------------------------------------------


     


def Cap(s):
  return s[:1].upper() + s[1:]


VERBOSE = False

def say(*args):
  if VERBOSE:
    for s in Cap(' '.join([str(a) for a in args])).split('\n'):
      sys.stderr.write(textwrap.fill(s) + '\n')

def output(lines):
  print '\n'.join(lines)


ALIASES = {
  'walk': 'go',
  'get': 'take',
  'grab': 'take',
  'throw': 'drop',
  'i': 'inventory',
  'l': 'look',
  'examine': 'look',
  'read': 'look',
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
  
  if args:
    for i in args:
      player.execute(open(i,'r'))
  else:
    player.execute()

if __name__ == '__main__':
  main()
