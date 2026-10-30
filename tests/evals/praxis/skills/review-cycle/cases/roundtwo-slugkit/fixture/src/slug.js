'use strict';

// Lowercase ASCII letters and digits, with each run of anything else turned into one dash.
function toSlug(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// The slug cut to at most `max` characters.
function trimToLength(slug, max) {
  return slug.slice(0, max);
}

function slugify(text, options = {}) {
  const slug = toSlug(text);
  return options.maxLength ? trimToLength(slug, options.maxLength) : slug;
}

module.exports = { slugify, toSlug, trimToLength };
