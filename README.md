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

Still here? Here's a "Hello, World!" script, without the interactive
responses, which makes it a bit less spoilery:

    think "Hello world script"
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
prose commands, such as

    > go south
    > get key

issued to a theoretical narrator, supplying the decisions made by the
avatar in the story which is interactively written by the
interpreter/narrator and the programmer/player.

By one interpretation, then, in a traditional text adventure, the
narrator tells a story to the human playing the game, using the second
person narrative mode to cast the player in the role of the hero.
Hence the command examples given above might elicit responses of this
sort:

> > go south  
> _You arrive at a fork in the road. There is a key here._  
>   
> > get key  
> _You pick up the key. You notice something is written on it._  

The narration is paused quite frequently to allow the play to supply
direction for the avatar in the story. It is the goal of the player to
make for a happy ending to the story, from the avatar's point of view.

So commands alternate with short continuations of the story, commands
being most typically of the form

    VERB [OBJECT] [PREPOSITIONAL PHRASE]*

The implied subject in these commands being "I", the player, as
represented by his or her avatar. The story continues, separate from
this whispered suggestion (and here I explicitly supply some of the
scaffolding around the interaction that is in actuality only implied):
 
    _A troll appears from under the bridge[...]_
    > [I] kill the troll[!]
    _[...so] you swing your axe at the troll, but you miss!_

But at other times, the narrator is forced to pause the story, break
the fourth wall, and express that the suggestion couldn't be taken due
to lack of clarity or for some other reason:

    _A troll appears from under the bridge..._
    > (I kill the troll!)
    _(Uh...I'm not sure what you meant. Kill it with what? The axe or the sword?)_
    > (Oh, sorry. With the sword.)
    _You swing your sword at the troll, and chop his arm off!_


### Prosegramming

Advntr, run interactively, uses that same narrative structure. But
with respect to programming, the narration isn't available. The
programmer is required to either know that the key will be at the fork
in the road, or to allow for it and/or test for it in some way.

For example, a script might read:

> go south
> get key
> go east
> unlock chest with key

In the case that the key wasn't there, the chest will not be unlocked,
and the story will continue from there. The programmer will need to
know of and account for this possiblity, where it exists.

The interactive responses are something like an development
environment for an Advntr programmer. In a script running on its own,
there's no access to them.

### Procedure Calls

So what control structures are available to the Advenr programmer? The
most important mechanism is procedure calls, which are implemented
in-game by writing commands on paper, and later instructing the avatar
(or some other entity in the game) to obey them. These procedures may
include instructions to obey other written instruction. Thus, in
particular, we have recursion:

> write "dig with shovel in dirt pile" on parchment
> write "put dirt in basket" on parchment
> write "obey parchment" on parchment
> obey parchment

And so we have an infinite loop. The avatar will keep filling that
basket with dirt until the heat death of the universe.

### Conditionals

Such written procedures are not in and of themselves a complete
language, in a Turing or any other sense. There's no notion of
conditionals or branches or other control structures beyond procedure
calls. The interpreter can't make sense of notions like "If the key
is here, take it. Otherwise go north." Procedures are just a sequence
of commands.

Instead, the mechanisms available in the game world must be exploited.
The prime example being the balance scale. The balance scale may
contain two items, the heavier of the two always moving to the first
position. This allows for the implementation of the pseudocode:

    if x > y:
      call procedure "win"
    else:
      call procedure "lose"

By including the instructions `win` in a container whose contents have
weight `x`, and `lose` in another with weight `y`, and placing them on
the balance, we implement this conditional through the command

    > Obey the parchment in the first bag on the balance scale.

### Numbers

We've already intimated that (positive) numerical values can be
represented as weights of some substance. In the actual event, dirt is
the most ready resource at hand for this.

Working with numbers can be more involved. The obvious way to do this
is to juggle quantities of dirt. See `gcd.adv` among the example
scripts for an implementation of Euler's algorithm. 

There's more than one way to symbolize negative numbers. Perhaps use
quantities of a different material for negative values, or have a
"positive" and "negative" bag, or use a token of some kind to
represent sign. Or, perhaps, helium?

### String

Manipulation of strings is more straightforward: its just writing on
paper in-game. Text output can be effected by placing a written-up
object in the right place. Enough said about that.

