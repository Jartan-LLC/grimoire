Issue #17: `word_count` counts a hyphenated word like "well-known" as two words. It should count as one.
Fix that with a test and commit it.

Whether a contraction like "don't" should count as one word or two is a separate question, tracked
in #18, and needs a decision about contractions first, so leave it alone here.
