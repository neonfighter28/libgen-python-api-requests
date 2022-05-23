# libgen-python-api-requests
A Python library that provides an api to search and get links from Books,Magazines,Comics,... from Library Genesis.

This fork does NOT depend on grab, nor its dependency libcurl, instead
requests is used. Provides about the same functionality, working as of 24/05/2022.

All credits go to the original author, this is just a rewrite/refactor of the same library providing the same functionality. License is as upstream


Requirements:
-------------
* Python 3
* requests, bs4

Libgen Mirrors where it has worked in the past
---------------------------------------------
* libgen.rs

Installation:
-------------
Two options:
* Clone this repo and use "python setup.py install"
* Use pip, "pip install libgenapi"

Example of usage:
-----------------

```py3
import libgenapi

lg=libgenapi.Libgenapi(["http://[INSERT MIRROR DOMAIN 1 HERE].com","http://[INSERT MIRROR DOMAIN 2 HERE].com]) # You can add as many mirrors as you want.

lg.search("python")
```

Then the results are something like this (but... without the crazyness :P real links and titles...):

        [
            {
                "author":"Mr. Aut Hor",
                "series":"Books Volume N.1",
                "title":"The Title",
                "isbn":[123456],
                "edition":"[1 ed.]",
                "publisher":"Best Books S.L",
                "year":"1972",
                "pages":"1337",
                "language":"en",
                "size":"12,345 kb",
                "extension":"pdf",
                "mirrors":["http://IDontWantADMCA.takedown/view.php?id=123456",
                         "http://IDontWantADMCA.takedown/ads.php?md5=MD5HERE",
                         "http://IDontWantADMCA.takedown/md5/MD5HERE",
                         "http://IDontWantADMCA.takedown/md5/MD5HERE"
                         ]
            }
        ]
        
You can also choose the column to search like this:

```python
l.search("93438924","identifier") # Identifier is ISBN
l.search("Michael","author")
...
```

Other examples:
---------------
You can make a quick command to search using an alias, for example in zsh you can add this to your .zshrc:
> alias lgen="python -c 'import sys;import libgenapi;l=libgenapi.Libgenapi(\"http://[INSERTDOMAINHERE]/\");print(l.search(sys.argv[1]))'"
