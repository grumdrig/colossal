#! /usr/bin/python

"""Usage: adventure.py [OPTS] [PARAMETERS]

Runs the Tarpit Adventure, the text adventure that's also a
programming language.

OPTS:
  -f FILENAME  Perform the steps specified in the file FILENAME
  -v           Print feedback to stderr [default only in interactive mode]
  -V           Print feedback to stdout
  -q           Do not output feedback [default in noninteractive mode]
  -h           Print this stuff, right here.

If no filename arguments are specified, run an interactive session.

PARAMETERS:

Any further parameters passed on the command line appear within the
adventure somewhere. I won't spoil it by telling you where.
"""

import sys, random, getopt, textwrap, shlex, fileinput, math


ROOMS = { }  # Mapping from room names to rooms
DIRECTIONS = set()  # All possible directions one might go
NOUNS = set()
ADJECTIVES = set()
NAMES = set()

TYPES = {
  'page': 'parchment',
  'paper': 'parchment',
  'letter': 'parchment'
  }

class Vessel(object):
  def __init__(self, capacity=0, closed=None, locked=None):
    self.items = []
    self.capacity = capacity or 0
    self.closed = closed
    self.locked = locked
    self.location = None
    
  def find(self, spec):
    if not spec:
      return []
    if spec.selector:
      pool = [i for i in self.items if not (i.fixed or i.mobile)]
      if spec.selector == 'all':
        return pool
      elif spec.selector == 'first':
        return pool[:1]
      elif spec.selector == 'last':
        return pool[-1:]
    else:
      return [o for o in self.items if o.match(spec)]

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
  def onPush(self): say("That doesn't appear to do anything.")

  

class Room(Vessel):
  def __init__(self, name, description, exits, resources=None):
    Vessel.__init__(self, capacity=float('inf'))
    self.name = name
    self.description = description
    self.exits = dict([(n,ROOMS.get(n,x)) for (n,x) in exits.items()])
    global DIRECTIONS
    DIRECTIONS |= set(exits.keys())
    self.resources = resources or {}
    ROOMS[name] = self

  def __str__(self):
    return self.name

  def find(self, q):
    return Vessel.find(self, q) or sum([i.find(q)
                                        for i in self.items
                                        if i.fixed or i.mobile], [])

  def describe(self, brief=False):
    if brief:
      return self.name
    result = self.name.upper()
    if not brief:
      result += '\n\n' + self.description
      for item in self.items:
        if item.type != 'You' and not item.fixed:
          result += '\n\nThere is ' + item.describe(True) + ' here.'
    return result

  def onTick(self): pass
          

ORDINARY = [
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
  def __init__(self, phrase, location, description=None,
               capacity=0, closed=None, locked=None, qty=None):
    Vessel.__init__(self, capacity=capacity, closed=closed, locked=locked)
    if len(phrase.split(' ')) > 1:
      self.adjective, self.noun = phrase.split(' ')
    else:
      self.noun = phrase
      self.adjective = None
    self.type = TYPES.get(self.noun, self.noun)
    global ADJECTIVES
    NOUNS.add(self.noun.lower())
    if self.adjective:
      ADJECTIVES.add(self.adjective.lower())
    self._name = None
    self.fixed = False
    self.mobile = False
    self.writing = []
    self.description = description
    self.qty = qty
    if location: self.move(location)

  def __str__(self):
    result = (self.adjective + ' ' if self.adjective else '') + self.noun
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
      result += '\nThe ' + self.noun + ' is closed.'
    elif self.items:
      result += '\nThe ' + self.noun + ' contains:'
      for item in self.items:
        result += '\n  ' + Cap(item.describe(True)) + '.'
    return result

  @property
  def name(self):
    return self._name
  
  @name.setter
  def name(self, name):
    if name:
      NAMES.add(name.lower())
    self._name = name

  def write(self, text):
    self.writing += [line.strip() for line in text.split(';')]

  def match(self, spec):
    result = not not spec.selector
    if spec.selector == 'first' and self != self.location.items[0]:
      return False
    if spec.selector == 'last' and self != self.location.itens[-1]:
      return False
    for a in 'adjective','noun','name':
      if getattr(spec, a):
        if getattr(spec, a) == getattr(self, a):
          result = True
        else:
          return False
    return result

  def weight(self):
    return (self.qty or 0) + sum([i.weight() for i in self.items])
  

class Furniture(Item):
  def __init__(self, phrase, location, description=None,
               capacity=float('inf'), closed=None, locked=None):
    Item.__init__(self, phrase, location, description=description,
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
                 'multi': param[0] == '*',
                 'held': False }
      if result['optional']: param = param[:-1]
      if result['multi']: param = param[1:]
      result['held'] = param[-1:] == '@'
      if result['held']: param = param[:-1]
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

      if parameter['type'] == 'str':
        arguments[parameter['name']] = input.pop(0)
      else:
        root = subject if parameter['held'] else subject.location
        ob = subject.resolve(input, root,
                             parameter['multi'], parameter['type'])
        if not ob:
          return
        arguments[parameter['name']] = ob

    if (nobjects < len(self.objects) and
        not self.objects[nobjects]['optional']):
      return say(self.verb, 'what', self.objects[nobjects]['name'] + '?')
    for p,v in self.pps.items():
      if v['name'] not in arguments:
        if not v['optional']:
          return say(self.verb, p, 'what?')
        else:
          arguments[v['name']] = None

    return getattr(subject, self.verb)(**arguments)


class Itemspec:
  def __init__(self, q):
    self.adjective = None
    self.noun = None
    self.name = None
    self.selector = None
    def q0(ws):
      return (q and q[0].lower() in ws and q.pop(0)) or None
    q0(['the'])
    self.selector = q0(('all','first','last'))
    self.adjective = q0(ADJECTIVES)
    self.noun = q0(NOUNS)
    if q0(['called']):
      self.name = q and q.pop(0)
    if not (self.adjective or self.noun or self.name):
      self.name = q0(NAMES)

  def __bool__(self):
    return not not (self.adjective or self.noun or self.name or self.selector)

  def __repr__(self):
    return '"' + str(self) + '"'

  def __str__(self):
    return (self.selector or
            ' '.join([w for w in self.selector, self.adjective, self.noun, self.name if w]))


class Entity(Item):
  def __init__(self, phrase, location, description):
    Item.__init__(self, phrase, location, description, capacity=9)
    self.mobile = True
    self.active = True
    self.stack = []

  def resolve(self, q, root, multi=False, type=None):
    if q[0] == 'self':
      q.pop(0)
      return self
    elif q[0] == 'here':
      q.pop(0)
      return self.location

    spec = Itemspec(q)
    if spec.name == q:
      return say('Called what?')
    elif spec.selector == 'all' and not multi:
      return say("You can't specify multiple objects in this context.")

    if not spec:
      return say("I didn't understand. " + Cap(q[0]) + "?")

    if q and q[0] == 'in':
      q.pop(0)
      root = self.resolve(q, root)
      if not root:
        return say("I don't see a", spec, "there.")
    objs = root.find(spec)
    if not objs:
      return say('What ' + str(spec) + '?')
    elif len(objs) > 1 and spec.selector != 'all':
      return say('Which ' + str(spec) + '?')
    if type:
      for obj in objs:
        if type != obj.type:
          return say('The', obj, "can't be used for that.", type, obj.type)
    return objs if multi else objs[0]
      

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
      location = self.location.exits[direction]
      self.move(None)
      self.move(location)

  Verb('WRITE text:str WITH :pen@ ON paper:parchment')
  def write(self, text, pen, paper):
    paper.write(text)
    say('You write on the', str(paper) + '.')

  Verb('DIG WITH :shovel@ IN where?')
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
      dirts = where.find(Itemspec(['dirt']))
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
    say('You erase everything written on the ' + str(parchment) + '.')

  Verb('LOOK thing?')
  def look(self, thing=None):
    say((thing or self.location).describe())

  Verb('CALL item name:str')
  def call(self, item, name):
    item.name = None
    desc = str(item)
    item.name = name
    say("We'll call the", desc, '"' + item.name + '" from now on.')

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
      if vessel.items:
        say('Opening the', vessel, 'reveals:')
        for item in vessel.items:
          say('  ' + Cap(item.describe(True)) + '.')
      else: 
        say('The', vessel, 'is now open. It is empty.')

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

  Verb('TALK TO whom')
  def talk(self, whom):
    say('"Hello", you say.')
    whom.onHear("Hello", self)

  Verb('TAKE *items')
  def take(self, items):
    for item in items:
      item.move(self, str(item) + ' taken.')

  Verb('DROP *items@')
  def drop(self, items):
    for item in items:
      item.move(self.location, str(item) + ' dropped.')

  Verb('PUT *items@ INTO vessel')
  def put(self, items, vessel):
    for item in items:
      item.move(vessel, 'You put the', item, 'into the', str(vessel) + '.')

  Verb('GIVE *items@ TO vessel')
  def give(self, items, vessel):
    for item in items:
      item.move(vessel, 'You give the', item, 'to the', str(vessel) + '.')

  Verb('XYZZY')
  def xyzzy(self):
    say('Nothing happens.')

  Verb('HELLO')
  def hello(self):
    say('Uh...hello.')

  Verb('QUIT')
  def quit(self):
    say('Goodbye!')
    self.active = False

  Verb('THINK concept:str')
  def think(self, concept):
    pass

  Verb('PUSH item')
  def push(self, item):
    item.onPush()

  Verb('OBEY orders')
  def obey(self, orders):
    self.stack.append(orders)
    self.active = True
    for line in orders.writing:
      if not self.active:
        break
      say('>' * (len(self.stack)+1), line)
      self.parse(line)
    self.stack.pop()


  def parse(self, line):
    words = [ALIASES.get(word,word) for word in shlex.split(line.strip())]
    if not words:
      return

    command = words.pop(0).lower()

    if command in VERBS:
      VERBS[command].do(self, words)

    elif command in DIRECTIONS:
      self.go(command)

    else:
      say('I did not understand that.')

    self.location.onTick()


  def execute(self, lines=None):
    if lines:
      for line in lines:
        if not self.active:
          break
        say('\n>', line.strip())
        self.parse(line)
    else:
      while self.active:
        self.parse(raw_input('\n> '))
    

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



#=============================================================================#

osh = Room('Outside of a small house',
           'The day is warm and sunny. Butterflies careen about and bees hum from blossom to blossom. The smell of peonies and adventure fills the air.\n\nYou stand on a poor road running east-west, outside of a small house painted white. Planted in the ground in front of the house is a mailbox.',
           { 'east': 'Dirt road',
             'west': 'Crossroads',
             'cheat': 'Cheaterville',
             'in': 'Inside the small house' })
mailbox = Furniture('mailbox',
                    osh,
                    'A fairly ordinary mailbox, used mostly to receive mail. The kind with a flag on the side and so forth. The number "200" is proudly emblazoned with vinyl stickers on one side.',
                    capacity=3,
                    closed=True)

#-----------------------------------------------------------------------------#

cv = Room('Cheaterville',
          'Nothing to see here. Move along.',
          { 'uncheat': osh })
b = Item('nut bag', cv, capacity=float('inf'))
b.name = 'rex'


#-----------------------------------------------------------------------------#

Room('Inside the small house',
     'The house is decorated in an oppressively cozy country style. There are needlepoints on every wall and pillow, and the furniture is overstuffed and outdated. Against one overdecorated wall stands a case designed to display little league trophies and the like.',
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
           'This handsome case offers display space for a few treasured items.',
           capacity=3,
           closed=True,
           locked=True);

#-----------------------------------------------------------------------------#

Room('Dirt road',
     "You stand on a dirt road running east-west. The road is dirt. It's quite dirty. Beside the road is also dirt; there's dirt everywhere, in fact. Piles and piles of dirt, all around you!",
     { 'east': 'Fork in the road',
       'west': 'Outside of a small house' },
     resources={ 'dig': 'dirt' })
Item('shovel', 'Dirt road')

#-----------------------------------------------------------------------------#

class TarPit(Room):
  def onTake(self, item, source):
    item.move(None)
    say('The', item, 'sinks into the tar!')
TarPit('Tar pit',
       'The road leads to a noxious pit of tar. It emits noxious fumes and bubbles langoriously from time to time. Amidst the tar, out of reach, a tar-encrusted T-rex bobs, half-submerged.',
       { 'east': 'Crossroads' });

#-----------------------------------------------------------------------------#

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
          say("Your supply of", item.noun, "is doubled.")
Devil('devil', 'Crossroads',
       "This is the Lord Beelzebub. Satan. Lucifer. You've heard the stories. He's just hanging around here, not really doing too much. Just thinking about stuff.").name = 'Satan'
Item('soul', 'Crossroads')

#-----------------------------------------------------------------------------#

Room('Dunno...',
     "I'm not sure what we're looking at here. I just don't know how to describe it. It's just...\nThe road continues north-south. Other than that it's just really indescribable. (Sorry.)",
     { 'north': 'TODO',
       'south': 'Crossroads' })
Item('something', 'Dunno...',
     'What the hell is this thing?')

#-----------------------------------------------------------------------------#

Room('Fork in the road',
     'The road leading in from the west forks here. The northeast fork seems to head towards a rocky, hilly area. The road to the southeast is narrower and lined with tall grass. Not much more to say about it than that. Should I mention the bees and butterflies again?',
     { 'west': 'Dirt road',
       'northeast': 'Mouth of a cave',
       'southeast': 'Grassy knoll', })

#-----------------------------------------------------------------------------#

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

#-----------------------------------------------------------------------------#

Room('Deep grass',
     "The grass here is deep. It's like a needle in a haystack, minus the needle in here.",
     { 'out': 'Grassy knoll' })

#-----------------------------------------------------------------------------#

Room('Mouth of a cave',
     "The jaws of a cave yawn before you. To continue the metaphor, the cave's acrid breath recalls overcooked garlic bread. Sharp teeth (and here I'm hinting at stactites and stalagmites) gnash (poetically speaking) at the lips of the cave. I think that's descriptive enough.",
     { 'southwest': 'Fork in the road',
       'north': 'Cave foyer',
       'in': 'Cave foyer' })

#-----------------------------------------------------------------------------#

Room('Cave foyer',
     "Immediately inside the entrance to the cave, it opens up to a vaulted entryway. The skeletal remains and equipment of what must be the world's absolute worst spelunker slump against one wall. Deeper into the cave, a low passage winds north.",
     { 'out': 'Mouth of a cave',
       'south': 'Mouth of a cave',
       'north': 'Narrow passage' })
pack = Item('backpack', 'Cave foyer', capacity=6)
Item('pen', pack)
Item('journal page', pack).write('August 13;;Down to my last stick of gum. I should have brought more food and less gum.;;The exit from this cave must be somewhere around here, but I lack the strength to keep looking.;;...')

#-----------------------------------------------------------------------------#

Room('Narrow passage',
     "The passage soon becomes so low you have to belly crawl to get anywhere. It's also dark, very dark. The walls press your sides, unyielding cold stone. Despite the chill, sweat beads your brow. There is scuffling sound behind you. A footstep? No, no. You feel like you're suffocating. Is that a dim glow up ahead? Please let it be so...",
     { 'south': 'Cave foyer',
       'north': 'Chamber' });

#-----------------------------------------------------------------------------#

Room('Chamber',
     "Small fissures in the ceiling allow a bit of daylight to filter into this fairly roomy chamber. Passages extend in all four directions.",
     { 'south': 'Narrow passage',
       'north': 'North chamber',
       'east': 'East chamber',
       'west': 'West chamber' })
class Robot(Entity):
  def onHear(self, speech, source):
    self.stack.append(source)
    self.active = True
    for line in speech.split(';'):
      if not self.active:
        break
      say('>' * (len(self.stack)+1), line)
      self.parse(line)
    self.stack.pop()
Robot('robot', 'Chamber',
      "Picure Bender from Futurama, without the drinking problem. That's pretty much this robot. Not that he's without his problems though; his problem is overenthusiasm.").name = 'Floyd'

#-----------------------------------------------------------------------------#

Room('East chamber',
     "A single shaft of daylight penetrates the gloom, shining from a small hole in the middle of the high ceiling of this subterranean chamber. A large cauldron stands directly beneath the hole. There are openings to the west and southeast.",
     { 'west': 'Chamber',
       'southeast': 'Hall of justice' })
cauldron = Furniture('blackened cauldron', 'East chamber',
                     "The cauldron is coated with sooty blackness.")

#-----------------------------------------------------------------------------#

class HallOfJustice(Room):
  def onTick(self):
    balance.weigh()
HallOfJustice('Hall of justice',
              "In contrast with the natural caves nearby, this room seems to have been carved from the living stone, which, as it happens, is a pure white marble. Upon a stone dias in the middle of the room is a classical statue of a blindfolded woman. From her outstretched right hand dangles a golden balance scale. Her left arm is bent at the elbow and her middle finger is held upright, forever fixed in some ancient gesture whose meaning is now long lost.\nThe only exit is to the northwest.",
              { 'northwest': 'East chamber' })
class Balance(Furniture):
  def onTake(self, item, source):
    self.weigh()
  def weigh(self):
    if len(self.items) == 2:
      w1,w2 = [item.weight() for item in self.items]
      if w2 > w1:
        self.items.reverse()
        say('The far side of the', self, 'occupied by the', self.items[0],
            'rotates forwards.')
balance = Balance('balance scale', 'Hall of justice',
        "This ornate golden scale appears to be fully functional. It operates on a swivel so that the heavier item placed in it's two weighing pans will rotate to the front.",
        capacity=2)

#-----------------------------------------------------------------------------#

Room('North chamber',
     "The rough, natural passage entering this chamber from the south, not to mention the craggy subterranean setting in general, contrast sharply with the professional glass and steel facade to the north. The design work is modern and impeccable. Lettered over the door in 900pt Helvetica are the words:\n  Calloway, Papermaster, Turban and Hoyt LLC\n               Attorneys at Law",
     { 'south': 'Chamber',
       'north': 'Reception' })

#-----------------------------------------------------------------------------#

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

#-----------------------------------------------------------------------------#

Room('Hallway',
     "The hallway runs north-south. The walls are decorated with motivational posters and inexpertly-executed watercolors. There are doors on either side.",
     { 'south': 'Reception',
       'north': 'More hallway',
       'east': 'Bathroom',
       'west': 'Executive office' })

#-----------------------------------------------------------------------------#

Room('Executive office',
     "Though not a corner office, this roomy office is well appointed with mahogony panelling and a large picture window with an expansive view of a solid rock wall a few inches away. There's an impressive desk and commodious filing cabinet, and on the wall an original painting which, while abstract, manages to suggest a phallus pretty clearly.",
     { 'east': 'Hallway' })
Furniture('oak desk', 'Executive office',
          "An oppressively impressive oak desk. Under the front edge you notice a red button.")
fc = Furniture('filing cabinet', 'Executive office',
               "A tall filing cabinet in dark wood.",
               capacity=40, closed=True)
ff = Item('file folder', fc, capacity=24)
ff.write("Turban, Edward G.")
Item('personnel parchment', ff).write("PERSONNEL REPORT;Edward G. Turban;;  ...Mr. Turban shows antisocial tendencies...tends to act like a dick...often late to work...;;- Harold Papermaster""")

#-----------------------------------------------------------------------------#

Room('Bathroom',
     "The bathroom is equipped with the usual fixtures. In the floor, there is a large drain.",
     { 'west': 'Hallway',
       'out': 'Hallway' })
class StandardOut(Furniture):
  def onTake(self, item, source):
    for item in self.items:
      output(item.writing)
      say('The', item, 'vanishes into the drain.')
      item.move(None)
StandardOut('drain pipe', 'Bathroom',
            "The drain sits at the low point of the tiled floor. It is emblazoned with the words \"STANDARD PIPE CO.\".")

#-----------------------------------------------------------------------------#

mailroom = Room('Supply closet',
                "One too many employees swiped supplies from here and the last binder clip went to someone's home long ago, so the shelves are basically bare. On one shelf, there is a postal scale.",
                { 'west': 'Reception' })
class Scale(Furniture):
  def onTake(self, item, source):
    wt = str(self.weight())
    if wt[-2:] == '.0': wt = wt[:-2]  # remove .0 if integral
    self.writing = [wt]
scale = Scale('postal scale', mailroom,
              'The postal scale features a digital readout and a bold red button.')
class ScaleButton(Furniture):
  def onPush(self):
    label = Item('metering label', scale)
    label.write('\n'.join(scale.writing))
    say("Skrzzzzzzztkrrrrrzt... ", Cap(label.describe(True)), 'emerges.')
ScaleButton('red button', mailroom, "It's an inviting red button ergonomically positioned on the postal scale.")

#-----------------------------------------------------------------------------#

Room('More hallway',
     "The hallway from the south ends at a door to the north, and there are doors to the east and west as well.",
     { 'south': 'Hallway',
       'west': 'Kitchen',
       'east': 'Cubicles' })

#-----------------------------------------------------------------------------#

Room('Cubicles',
     "You are in a maze of cubibles, all alike.",
     { 'north': 'Cubicles',
       'south': 'Cubicles',
       'east': 'Cubicles',
       'west': 'Cubicles' })

#-----------------------------------------------------------------------------#

Room('Kitchen',
     "You stand in a small kitchen and break room. There's a sink and a cupboard and a toaster oven, and a motivational poster on the wall with a picture of a kitten and the words 'GET BACK TO WORK'.",
     { 'east': 'More hallway' })
cupboard = Furniture('cupboard', 'Kitchen',
                     "Just a cupboard.",
                     capacity=float('inf'),
                     closed=True)
class Pan(Item):
  def onTake(self, item, source):
    if item.type != 'dirt':
      item.move(source)
      return say('You cant put the', item, 'there.')
    elif self.items:
      excess = self.items[0].qty - self.capacity
      if excess > 0:
        say('The', self, 'is chock full.')
        Item('dirt', source).qty = excess
        self.items[0].qty = self.capacity
Pan('pie tin', cupboard, "A circular pie tin, suitable for pies.",
    capacity=math.pi)
Pan('cake pan', cupboard, "A square cake pan.", capacity=math.sqrt(2))

#=============================================================================#



     


def Cap(s):
  return s[:1].upper() + s[1:]


FEEDBACK = None


def say(*args):
  if FEEDBACK:
    for s in Cap(' '.join([str(a) for a in args])).split('\n'):
      FEEDBACK.write(textwrap.fill(s) + '\n')

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
  'from': 'in',
  'of': 'in',
  'inside': 'into',
  'onto': 'into',
  'me': 'self',
  'myself': 'self',
  'yourself': 'self',
  'rename': 'call',
  'name': 'call',
  'follow': 'obey',
  'execute': 'obey',
  'perform': 'obey',
  'interpret': 'obey',
  'wonder': 'think',
  'muse': 'think',
  'believe': 'think',
}


def main():
  global FEEDBACK
  opts,args = getopt.getopt(sys.argv[1:], 'vVqf:h')
  FEEDBACK = None
  FILENAMES = []
  for o,a in opts:
    if o == '-v':
      FEEDBACK = sys.stderr
    elif o == '-V':
      FEEDBACK = sys.stdout
    elif o == '-q':
      FEEDBACK = False
    elif o == '-f':
      FILENAMES.append(a)
    else:
      sys.stderr.write(__doc__)
      sys.exit()
  if FEEDBACK == None and not FILENAMES:
    FEEDBACK = sys.stderr

  say('Welcome to Tarpit Adventure!')
  say()

  player = Player('Outside of a small house')
  
  if args:
    Item('letter', mailbox).writing = args
    for arg in args:
      bag = Item(random.choice(ORDINARY) + ' bag', cauldron,
                 capacity=float('inf'))
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
