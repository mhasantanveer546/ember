"""
Ember Search Engine — Trie (prefix tree)

Used for autocomplete: given a prefix a user has typed so far, quickly
suggest complete terms from the vocabulary. This is a separate structure
from InvertedIndex — it answers "what terms start with this prefix?"
rather than "which documents contain this exact term?"

Complexity notes:
    insert(word):        O(L), L = len(word)
    search(word):        O(L)
    starts_with(prefix):  O(L)
    suggest(prefix, k):   O(L + M) where M = number of nodes in the
                          subtree under the prefix (i.e. proportional to
                          how many matches exist, not vocabulary size)
"""


class _TrieNode:
    __slots__ = ("children", "is_end_of_word")

    def __init__(self) -> None:
        self.children: dict[str, "_TrieNode"] = {}
        self.is_end_of_word: bool = False


class Trie:
    """A prefix tree over lowercase terms."""

    def __init__(self) -> None:
        self._root = _TrieNode()

    def insert(self, word: str) -> None:
        """
        Insert a word into the trie. O(L) where L = len(word).
        Inserting the same word twice is a safe no-op the second time.
        """
        node = self._root
        for char in word:
            if char not in node.children:
                node.children[char] = _TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, word: str) -> bool:
        """
        Return True if `word` was inserted as a complete word. O(L).
        Note: this is exact-match, not prefix match — searching "cat"
        when only "cats" was inserted returns False. Use starts_with
        for prefix-only checks.
        """
        node = self._find_node(word)
        return node is not None and node.is_end_of_word

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word starts with `prefix`. O(L)."""
        return self._find_node(prefix) is not None

    def suggest(self, prefix: str, limit: int = 10) -> list[str]:
        """
        Return up to `limit` complete words starting with `prefix`,
        sorted alphabetically. Empty list if no matches or prefix unseen.

        Args:
            prefix: The partial input to complete.
            limit: Maximum number of suggestions to return.
        """
        node = self._find_node(prefix)
        if node is None:
            return []

        results: list[str] = []
        self._collect_words(node, prefix, results, limit)
        return sorted(results)[:limit]

    def _find_node(self, prefix: str) -> "_TrieNode | None":
        """Walk the trie along `prefix`; return the ending node or None."""
        node = self._root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def _collect_words(
        self, node: "_TrieNode", current_word: str, results: list[str], limit: int
    ) -> None:
        """
        DFS from `node`, collecting complete words into `results`.
        Stops early once `limit` words have been found — suggest() doesn't
        need to explore the entire subtree if the prefix is very common.
        """
        if len(results) >= limit:
            return
        if node.is_end_of_word:
            results.append(current_word)
        for char, child in node.children.items():
            if len(results) >= limit:
                return
            self._collect_words(child, current_word + char, results, limit)