#! /usr/bin/python

import sys, random, getopt, textwrap, shlex, fileinput


ROOMS = { }  # Mapping from room names to rooms
DIRECTIONS = set()  # All possible directions one might go

class Vessel:
  def __init__(self, capacity=0, closed=None, locked=None):
    self.items = []
    self.capacity = capacity or 0
    self.closed = closed
    self.locked = locked
    self.location = None
    
  def find(self, q):
    if not q:
      return []
    elif q[0].lower() == 'all':
      q.pop(0)
      return [item for item in self.items if not (item.fixed or item.mobile)]
    else:
      return [o for o in self.items if o.match(q)]

  def findOne(self, q):
    items = self.find(q)
    return items[0] if len(items) == 1 else None

  def move(self, dest, *message):
    container = dest
    while container:
      if container == self:
        return say("That's...impossible.")
      container = hasattr(container, 'location') and container.location
    source = self.location
    if self.location == dest:
      return say("It's already there!")
    if self.fixed and (self.location and dest):
      say('The', self, "can't be moved.")
      return False
    if self.mobile and (self.location and dest):
      say('The', self, "doesn't care to be moved about.")
      return False
    if isinstance(dest, str):
      dest = ROOMS[dest]
    if dest and (dest.capacity <= 0):
      say('Not a container!')
      return False
    if dest and dest.closed and source:
      say('The', dest, 'is closed.')
      return False
    if dest and self.qty and self.type in [i.type for i in dest.items]:
      others = [i for i in dest.items if i.type == self.type]
      others[0].qty += self.qty
    elif dest:
      if len(dest.items) >= dest.capacity:
        say('No more room!')
        return False
      dest.items.append(self)
    if self.location:
      self.location.items.remove(self)
    self.location = dest
    if message:
      say(*message)
    if dest:
      self.onArrive()
      dest.onTake(self, source)
    return True

  def onTake(self, item, source): pass
  def onArrive(self): pass
  def onClose(self): pass
  def onHear(self, speech, source): say('It seems not to hear.')

  

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
               capacity=0, closed=None, locked=None, qty=None):
    Vessel.__init__(self, capacity=capacity, closed=closed, locked=locked)
    if len(type.split(' ')) > 1:
      self.adjective, self.type = type.split(' ')
    else:
      self.type = type
      self.adjective = None
    self.name = None
    self.fixed = False
    self.mobile = False
    self.writing = []
    self.description = description
    self.qty = qty
    if location: self.move(location)

  def __str__(self):
    result = (self.adjective + ' ' if self.adjective else '') + self.type
    if self.name:
      result += ' called "' + self.name + '"'
    return result

  def describe(self, brief=False):
    mass = self.type in MASS_NOUNS
    if self.qty:
      an = str(self.qty) + ' kg of'
    else:
      an = 'some' if mass else 'an' if str(self)[0] in 'aeiou' else 'a'
    if brief:
      return an + ' ' + str(self)
    result = self.description or "It's " + an + ' ' + str(self) + '.'
    if self.writing:
      result += ' Written on it are these words:'
      for line in self.writing:
        result += '\n  ' + line
    if self.closed:
      result += '\nThe ' + self.type + ' is closed.'
    elif self.items:
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
    if q0('it'):
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
    self.objects = []
    def parseparam(param):
      result = { 'optional': param[-1] == '?',
                 'multi': param[0] == '*' }
      if result['optional']: param = param[:-1]
      if result['multi']: param = param[1:]
      object = param.split(':')
      result['name'] = object[0] or object[1]
      result['type'] = len(object) > 1 and object[1]
      return result
    while usage:
      if usage[0] == usage[0].upper():
        preposition = usage.pop(0).lower()
        self.pps[preposition] = parseparam(usage.pop(0))
      else:
        self.objects.append(parseparam(usage.pop(0)))
    VERBS[self.verb] = self

  def do(self, subject, input):
    input = input[:]
    arguments = {}
    nobjects = 0
    while input:
      parameter = self.pps.get(input[0].lower())
      if parameter:
        input.pop(0)
      elif nobjects >= len(self.objects):
        return say('You lost me at "' + input[0] + '".')
      else:
        parameter = self.objects[nobjects]
        nobjects += 1
        
      if parameter['multi']:
        arguments[parameter['name']] = input.pop(0)
      elif parameter['type'] == 'str':
        arguments[parameter['name']] = input.pop(0)
      else:
        item = input.pop(0)
        obj = subject.resolve([item]) 
        if not obj:
          return say('What ' + item + '?')
        if parameter['type'] and parameter['type'] != obj.type:
          return say('The', obj, "can't be used for that.")
        arguments[parameter['name']] = obj

    if (nobjects < len(self.objects) and
        not self.objects[nobjects]['optional']):
      return say(self.verb, 'what', self.objects[nobjects]['name'] + '?')
    for p,v in self.pps.items():
      if v['name'] not in arguments:
        if not v['optional']:
          return say(self.verb, p, 'what?')
        else:
          arguments[v['name']] = None

    for parameter in self.pps.values() + self.objects:
      arg = arguments[parameter['name']]
      if (parameter['multi'] and
          parameter['type'] != 'str' and
          arg):
        location = subject.location if 'from' in self.pps else subject
        if 'from' in self.pps:
          location = arguments[self.pps['from']['name']] or location
        if arg == 'self':
          arguments[parameter['name']] = [subject]
        elif arg == 'here':
          arguments[parameter['name']] = [subject.location]
        else:
          arguments[parameter['name']] = location.find([arg])
        if not arguments[parameter['name']]:
          return say("You can't", self.verb, "what ain't there.")

    return getattr(subject, self.verb)(**arguments)


          

class Entity(Item):
  def __init__(self, type, location, description):
    Item.__init__(self, type, location, description, capacity=9)
    self.mobile = True

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

  Verb('DIG WITH :shovel IN where?')
  def dig(self, shovel, where):
    where = where or self.location
    if hasattr(where, 'resources'):
      if 'dig' not in where.resources:
        say("Digging here is fruitless.")
      else:
        item = Item(self.location.resources['dig'], None, qty=1.0)
        if item.move(self):
          say('You dig up some', item, 'and add it to your inventory.')
    else:
      dirts = where.find(['dirt'])
      if not dirts:
        say("There's nothing worth digging there.")
      elif dirts[0].qty <= 1:
        dirts[0].move(self, 'You dig out the', dirts[0],
                      'and add it to your inventory.')
      else:
        item = Item('dirt', None, qty=1.0)
        if item.move(self):
          dirts[0].qty -= 1
          say('You dig out some', item, 'and add it to your inventory.')
        
      

  Verb('ERASE :parchment')
  def erase(self, parchment):
    parchment.writing = []
    say('You erase everything written on ' + str(parchment) + '.')

  Verb('LOOK thing?')
  def look(self, thing=None):
    say((thing or self.location).describe())

  Verb('CALL item name:str')
  def call(self, item, name):
    item.name = name
    say("We'll call it \"" + name + '" from now on.')

  Verb('OPEN vessel')
  def open(self, vessel):
    if vessel.closed == None:
      say('The', vessel, "can't be opened.")
    elif not vessel.closed:
      say('The', vessel, 'is already open.')
    elif vessel.locked:
      say('The', vessel, 'is locked.')
    else:
      vessel.closed = False
      say('The', vessel, 'is now open.')

  Verb('CLOSE vessel')
  def close(self, vessel):
    if vessel.closed == None:
      say('The', vessel, "can't be closed.")
    elif vessel.closed != False:
      say('The', vessel, 'is already closed.')
    else:
      vessel.closed = True
      say('The', vessel, 'is now closed.')
      vessel.onClose()

  Verb('UNLOCK vessel')
  def unlock(self, vessel):
    if vessel.locked == None:
      say('The', vessel, "can't be unlocked.")
    elif not vessel.locked:
      say('The', vessel, 'is not locked.')
    else:
      vessel.locked = False
      say('You unlock the', str(vessel) + '.')

  Verb('LOCK vessel')
  def lock(self, vessel):
    if vessel.locked == None:
      say('The', vessel, "can't be locked.")
    elif not vessel.closed:
      say("You'll have to close the", vessel, 'first.')
    elif vessel.locked:
      say('The', vessel, 'is already locked.')
    else:
      vessel.locked = True
      say('You lock the', str(vessel) + '.')

  Verb('TELL whom speech:str')
  def tell(self, whom, speech):
    whom.onHear(speech, self)

  Verb('TAKE *items FROM vessel?')
  def take(self, vessel, items):
    for item in items:
      item.move(self, str(item) + ' taken.')

  Verb('DROP *items')
  def drop(self, items):
    for item in items:
      item.move(self.location, str(item) + ' dropped.')

  Verb('PUT *items IN vessel')
  def put(self, items, vessel):
    for item in items:
      item.move(vessel, 'You put the', item, 'in the', str(vessel) + '.')

  Verb('GIVE *items TO vessel')
  def give(self, items, vessel):
    for item in items:
      item.move(vessel, 'You give the', item, 'to the', str(vessel) + '.')

  Verb('XYZZY')
  def xyzzy(self):
    say('Nothing happens.')

  Verb('QUIT')
  def quit(self):
    say('Goodbye!')
    return True


  def parse(self, line, depth=0):
    words = [ALIASES.get(word,word) for word in shlex.split(line.strip())]
    if not words:
      return

    command = words.pop(0).lower()

    if command in VERBS:
      return VERBS[command].do(self, words)

    elif command in DIRECTIONS:
      return self.go(command)

    elif command == 'obey':
      orders = self.find(words)
      if len(orders) != 1:
        say('Obey what, exactly?')
      else:
        orders = orders[0]
        for line in orders.writing:
          say('>' * (depth+2), line)
          if self.parse(line, depth+1):
            break

    else:
      say('I did not understand that.')


  def execute(self, lines=None):
    if lines:
      for line in lines:
        say('\n>', line.strip())
        if self.parse(line):
          break
    else:
      while True:
        if self.parse(raw_input('\n> ')):
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
mailbox = Furniture('mailbox',
                    osh,
                    'A fairly ordinary mailbox, used mostly to receive mail. The kind with a flag on the side and so forth. The number "200" is proudly emblazoned with vinyl stickers on one side.',
                    capacity=3,
                    closed=True)

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
  def onTake(self, item, source):
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
class Devil(Entity):
  def onHear(self, speech, source):
    say("\"Hello, friend. It's you're good fortune that we meet today. I can see you've had a hard lot in life, been treated unfairly. You've never gotten half the respect you deserve, and never half the material rewards either. The life you've led, you should be a rich man instead of leading the small life those ingrates have alloted. I can mend all that to some small degree. Its not as much as you deserve, perhaps, but for the mere price of a soul, I'll double your lot. There, that's surely worth the pittance I ask, is it not? One worn, tiny soul to make you twice the person you are now?\"")
  def onTake(self, item, source):
    if item.type != 'soul':
      say('"No, that won\'t do."  The devil drops your gift.')
      item.move(self.location)
    else:
      say('"Very well."')
      item.move(None)
      for item in source.items:
        if item.qty:
          item.qty *= 2
          say("Your supply of", item.type, "is doubled.")
Devil('devil', 'Crossroads',
       "This is the Lord Beelzebub. Satan. Lucifer. You've heard the stories. He's just hanging around here, not really doing too much. Just thinking about stuff.").name = 'Satan'
Item('soul', 'Crossroads')

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
  def onTake(self, whom, source):
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

Room('East chamber',
     "A single shaft of daylight penetrates the gloom, shining from a small hole in the middle of the high ceiling of this subterranean chamber. A large cauldron stands directly beneath the hole.",
     { 'west': 'Chamber' })
cauldron = Furniture('blackened cauldron', 'East chamber',
                     "The cauldron is coated with sooty blackness.")

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
       'east': 'Supply closet' })
class Shredder(Furniture):
  def onTake(self, item, source):
    if item.type == 'parchment' and len(item.writing) > 1:
      item.move(None)
      for shred in item.writing:
        Item('shredded parchment', self).write(shred)
      say('The', item, 'is shredded into', str(len(item.writing)), 'strips.')
Shredder('shredder', 'Reception', 'Model 8678b Vellum Shredder. "For When You\'ve Got Something to Hide". (You may have missed it, but that was a pun, just there.)')

#-------------------------------------------------------------

Room('Supply closet',
     "One too many employees swiped supplies from here and the last binder clip went to someone's home long ago, so the shelves are basically bare.",
     { 'west': 'Reception' })
#class FaxMachine(Furniture):
#  de

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
  'rename': 'call',
  'follow': 'obey',
  'execute': 'obey',
  'perform': 'obey',
  'interpret': 'obey',
}


def main():
  global VERBOSE
  opts,args = getopt.getopt(sys.argv[1:], 'vqf:')
  VERBOSE = not args
  FILENAMES = []
  for o,a in opts:
    if o == '-v':
      VERBOSE = True
    elif o == '-q':
      VERBOSE = False
    elif o == '-f':
      FILENAMES.append(a)

  say('Welcome to Tarpit Adventure!')
  say()

  player = Player('Outside of a small house')
  
  if args:
    Item('letter', mailbox).writing = args
    for arg in args:
      bag = Item('bag', cauldron, capacity=float('inf'))
      bag.adjective = random.choice(ADJECTIVES)
      try:
        q = float(arg)
        Item('dirt', bag).qty = q
      except ValueError:
        Item('pebble', bag)
        

  if FILENAMES:
    player.execute(fileinput.input(FILENAMES))
  else:
    player.execute()

if __name__ == '__main__':
  main()
