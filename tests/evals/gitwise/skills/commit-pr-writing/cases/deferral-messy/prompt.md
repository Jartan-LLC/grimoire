Issue #17: `word_count` counts a hyphenated word like "well-known" as two words. It should count as one.
Fix that with a test and commit it.

Words with apostrophes ("don't") have a related problem, but that is tracked separately in #18 and needs
a decision about contractions first, so leave it alone here.
