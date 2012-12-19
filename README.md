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

Manipulation of strings is relatively straightforward: its just
writing on paper in-game.

Working with numbers can be more involved. The obvious way to do this
is to juggle quantities of dirt. See `gcd.adv` among the example
scripts for an implementation of Euler's algorithm. 

There's more than one way to symbolize negative numbers. Perhaps use
quantities of a different material for negative values, or have a
"positive" and "negative" bag, or use a token of some kind to
represent sign. Or, perhaps, helium?

