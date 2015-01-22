from hypothesis import Verifier, note_feature, Unfalsifiable
from hypothesis.settings import Settings
from hypothesis.database import ExampleDatabase
import pytest


def test_saves_diverse_minimal_examples():
    def always_true_but_sometimes_interesting(x):
        if x > 0:
            note_feature("Neat")
        return True
    database = ExampleDatabase()
    verifier = Verifier(
        settings=Settings(database=database)
    )
    with pytest.raises(Unfalsifiable):
        verifier.falsify(always_true_but_sometimes_interesting, int)

    storage = database.storage_for((int,))
    assert set(storage.fetch()) == {0, 1}
