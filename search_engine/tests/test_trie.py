"""Tests for search_engine.trie"""

from search_engine.trie import Trie


def test_insert_and_search_exact_match():
    trie = Trie()
    trie.insert("database")
    assert trie.search("database") is True


def test_search_unseen_word():
    trie = Trie()
    trie.insert("database")
    assert trie.search("dataset") is False


def test_search_is_exact_not_prefix():
    trie = Trie()
    trie.insert("cats")
    assert trie.search("cat") is False  # "cat" was never inserted alone
    assert trie.search("cats") is True


def test_starts_with_true_for_prefix_of_inserted_word():
    trie = Trie()
    trie.insert("database")
    assert trie.starts_with("data") is True
    assert trie.starts_with("database") is True


def test_starts_with_false_for_unrelated_prefix():
    trie = Trie()
    trie.insert("database")
    assert trie.starts_with("xyz") is False


def test_starts_with_empty_prefix_matches_anything_inserted():
    trie = Trie()
    trie.insert("database")
    assert trie.starts_with("") is True


def test_suggest_multiple_matches():
    trie = Trie()
    for word in ["database", "dataset", "data", "datagram"]:
        trie.insert(word)

    results = trie.suggest("data")
    assert results == ["data", "database", "datagram", "dataset"]


def test_suggest_respects_limit():
    trie = Trie()
    for word in ["cat", "car", "card", "care", "careful"]:
        trie.insert(word)

    results = trie.suggest("car", limit=2)
    assert len(results) == 2
    # Must still be valid completions of "car"
    assert all(r.startswith("car") for r in results)


def test_suggest_no_matches_returns_empty():
    trie = Trie()
    trie.insert("database")
    assert trie.suggest("xyz") == []


def test_suggest_prefix_that_is_itself_a_word():
    trie = Trie()
    trie.insert("cat")
    trie.insert("catalog")
    results = trie.suggest("cat")
    assert "cat" in results
    assert "catalog" in results


def test_insert_duplicate_is_safe():
    trie = Trie()
    trie.insert("database")
    trie.insert("database")
    assert trie.suggest("data") == ["database"]


def test_case_sensitivity_is_caller_responsibility():
    # Trie does no lowercasing itself — that's tokenizer's job upstream.
    # Feeding it mixed case creates separate paths, documented here so
    # it's not a surprise later.
    trie = Trie()
    trie.insert("Database")
    assert trie.search("database") is False
    assert trie.search("Database") is True


def test_empty_trie_suggests_nothing():
    trie = Trie()
    assert trie.suggest("a") == []
    assert trie.search("a") is False
    assert trie.starts_with("a") is False