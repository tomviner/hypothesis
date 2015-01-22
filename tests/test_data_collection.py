from hypothesis.collectors import DataCollector, note_feature


def test_collect_with_no_collectors_does_not_error():
    note_feature("Hello world")


def test_collect_with_a_collector_adds_data_to_it():
    c = DataCollector()
    with c:
        note_feature("Neat")
    assert c.features_seen == {"Neat"}


def test_a_collector_is_removed_from_the_stack():
    c = DataCollector()
    assert not DataCollector.active()
    with c:
        assert DataCollector.active() == c
    assert not DataCollector.active()


def test_things_go_on_a_collector_as_long_as_it_is_lowest_in_scope():
    c = DataCollector()
    d = DataCollector()
    with c:
        note_feature(1)
        with d:
            note_feature(2)
        note_feature(3)

    assert c.features_seen == {1, 3}
    assert d.features_seen == {2}
