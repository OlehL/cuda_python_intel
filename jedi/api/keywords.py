import pydoc
import keyword

from jedi._compatibility import is_py3, is_py35
from jedi import common
from jedi.evaluate.helpers import FakeName
from jedi.parser.tree import Leaf
try:
    from pydoc_data import topics as pydoc_topics
except ImportError:
    # Python 2.6
    try:
        import pydoc_topics
    except:
        pydoc_topics=None

if is_py3:
    if is_py35:
        # in python 3.5 async and await are not proper keywords, but for
        # completion pursposes should as as though they are
        keys = keyword.kwlist + ["async", "await"]
    else:
        keys = keyword.kwlist
else:
    keys = keyword.kwlist + ['None', 'False', 'True']


def has_inappropriate_leaf_keyword(pos, module):
    relevant_errors = filter(
        lambda error: error.first_pos[0] == pos[0],
        module.error_statement_stacks)

    for error in relevant_errors:
        if error.next_token in keys:
            return True

    return False


def completion_names(evaluator, stmt, pos, module):
    keyword_list = all_keywords(evaluator)

    if not isinstance(stmt, Leaf) or has_inappropriate_leaf_keyword(pos, module):
        keyword_list = filter(
            lambda keyword: not keyword.only_valid_as_leaf,
            keyword_list
        )
    return [keyword.name for keyword in keyword_list]


def all_keywords(evaluator, pos=(0, 0)):
    return set([Keyword(evaluator, k, pos) for k in keys])


def keyword(evaluator, string, pos=(0, 0)):
    if string in keys:
        return Keyword(evaluator, string, pos)
    else:
        return None


def get_operator(evaluator, string, pos):
    return Keyword(evaluator, string, pos)


keywords_only_valid_as_leaf = (
    'continue',
    'break',
)


class Keyword(object):
    type = 'completion_keyword'

    def __init__(self, evaluator, name, pos):
        self.name = FakeName(name, self, pos)
        self.start_pos = pos
        self.parent = evaluator.BUILTINS

    def get_parent_until(self):
        return self.parent

    @property
    def only_valid_as_leaf(self):
        return self.name.value in keywords_only_valid_as_leaf

    @property
    def names(self):
        """ For a `parsing.Name` like comparision """
        return [self.name]

    @property
    def docstr(self):
        return imitate_pydoc(self.name)

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self.name)


def imitate_pydoc(string):
    """
    It's not possible to get the pydoc's without starting the annoying pager
    stuff.
    """
    if pydoc_topics is None: return ''
    # str needed because of possible unicode stuff in py2k (pydoc doesn't work
    # with unicode strings)
    string = str(string)
    h = pydoc.help
    with common.ignored(KeyError):
        # try to access symbols
        string = h.symbols[string]
        string, _, related = string.partition(' ')

    get_target = lambda s: h.topics.get(s, h.keywords.get(s))
    while isinstance(string, str):
        string = get_target(string)

    try:
        # is a tuple now
        label, related = string
    except TypeError:
        return ''

    try:
        return pydoc_topics.topics[label] if pydoc_topics else ''
    except KeyError:
        return ''