from pa_nlp import *
from pa_nlp import nlp
import tensorflow as tf

# must be tensorflow 1.x
assert re.match("^1\.", tf.__version__) is not None, "must be tensorflow 1.x"
