Colossal Tarpit
===============

Programming is no game...until now! Colossal Tarpit is the text
adventure that's Turing complete, a prosegramming language. It was
written to be an entry in the [Dec 2012 PLT Games competition][1],
which calls for programming languages that can do anything, but never
should.

[1]: http://www.pltgames.com/competition/2012/12

Spoiler Alert
-------------

The code examples and discussion below are slight spoilers, since the
means of programming in Adventure is meant to be discovered in a
gamelike fashion. So stop reading this now.

Still here? Here's a "Hello, World!" script:

    go east
    east
    ne
    n
    get all from backpack
    erase page
    write on page with pen "Hello, World!"
    n
    n
    n
    n
    n 
    e
    put page into drain

Now let's run it.

    $ adventure.py -f hello.adv
    Hello, World!


Language Specification
----------------------

A complete specification of the language would be anathema to the
exploratory spirit of Advntr, so we do not present one here. Some
amount of explication is in order, however. We'll also dig into the
relationship between the dual aspects of Advntr as game and language.

### Prose

Advntr's source language follows the tradition of text adventure games
(aka prose games, or interactive fiction), particularly those
published by Infocom in the early eighties. The syntax consists of
(shorthand) prose commands, e.g.:

    > go south
    > get key

issued to a theoretical narrator, supplying the decisions made by the
avatar in the story, which is interactively written by the
interpreter/narrator and the programmer/player.

By one interpretation, then, in a traditional text adventure, the
narrator tells a story to the human playing the game, using the second
person narrative mode to cast the player in the role of the hero.
Hence the command examples given above might elicit responses of this
sort:

    > go south  
    You arrive at a fork in the road. There is a key here.
       
    > get key  
    You pick up the key. You notice something is written on it.

The narration is paused frequently to allow the player to supply
direction for the avatar in the story. It is the goal of the player to
find a happy ending to the story, from the avatar's point of view.

So commands alternate with short continuations of the story, commands
being most typically of the form

    VERB [OBJECT] [PREPOSITIONAL PHRASE]*

The implied subject in these commands being "I", the player, as
represented by his or her avatar. The story continues, separate from
this whispered suggestion (and here I explicitly supply some of the
scaffolding around the interaction that is in actuality only implied):
 
    NARRATOR: A troll appears from under the bridge... (what do you do
    now?)

    PLAYER: (I kill the troll!)

    N: ...so you swing your axe at the troll, but you miss!

But at other times, the narrator is forced to pause the story, break
the fourth wall, and express that the suggestion couldn't be taken due
to lack of clarity or for some other reason:

    N: A troll appears from under the bridge... (what do you do?)

    P: (I kill the troll!)

    N: (Uh...I'm not sure what you mean. Kill it with what? The axe or
    the sword?)

    P: (Oh, sorry. With the sword.)

    N: You swing your sword at the troll, and chop his arm off!


### Prosegramming

Advntr, run interactively, uses that same narrative metaphor; but with
respect to programming, the narration isn't available. The programmer
is required to either know that the key will be at the fork in the
road, or to allow for it and/or test for it in some way.

For example, a script might read:

    go south
    get key
    go east
    unlock chest with key

In the case that the key wasn't there, the chest will not be unlocked,
and the story will continue from there. The programmer will need to
know of and account for this possiblity, where it exists.

The interactive responses are something like an development
environment for an Advntr programmer. In a script running on its own,
there's no access to them.

### Procedure Calls

So what control structures are available to the Advenr programmer? The
most important programming mechanism is procedure calls, which are
implemented in-game by writing commands on paper, and later
instructing the avatar (or some other entity in the game) to obey
them. These procedures may include instructions to obey other written
instruction. Thus, in particular, we have recursion:

    > write "dig with shovel in dirt pile" on parchment
    > write "put dirt in basket" on parchment
    > write "obey parchment" on parchment
    > obey parchment

And so we have an infinite loop. The avatar will keep filling that
basket with dirt until the heat death of the universe.

### Conditionals

Such written procedures are not in and of themselves a complete
language, in a Turing sense at least. There's no notion of
conditionals or branches or other control structures beyond procedure
calls. The interpreter can't make sense of notions like "If the key is
here, take it. Otherwise go north." Procedures are just a sequence of
commands.

Instead, ambiguities of reference must be used. Game objects can be
referred to by name or description, or the nouns `first` and `last`
refer to the first and last objects within a container. Such
references are used against mechanisms available in the game world, a
prime example being the balance scale. The balance may contain
two items, the heavier of the two always moving to the first position.
This allows for the implementation of the pseudocode:

    if x > y:
      run procedure "win"
    else:
      run procedure "lose"

By including the instructions `win` in a container whose contents have
weight `x`, and `lose` in another with weight `y`, and placing them on
the balance, we implement this conditional through the command

    > Obey the parchment in the first bag on the balance scale.

### Numbers

We've already intimated that (positive) numerical values can be
represented as weights of some substance. In the actual event,
**dirt** is the resource readily at hand for this purpose. Even simple
things can be fairly involved; see `gcd.adv` among the example scripts
for a dirt-juggling implementation of Euler's algorithm.

There's more than one way to symbolize negative numbers. One could
perhaps use quantities of a different material for negative values, or
have a "positive" and "negative" bag, or use a token of some kind to
represent sign. Or, perhaps, helium? It's up to you!

### String

Manipulation of character strings is more straightforward: its just
writing on paper in-game. The text can be manipulated in various ways
by various in-game devices.
