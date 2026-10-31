#!/usr/bin/env perl

# Project lint: every Perl file says `use v5.36;`.

use v5.36;

my @files = sort( glob('lib/*.pm lib/*/*.pm bin/* t/*.t scripts/*.pl') );
my @bad;
for my $path (@files) {
    open my $fh, '<', $path or die "$path: $!\n";
    local $/;
    my $text = <$fh>;
    push @bad, $path unless $text =~ /^use v5\.36;$/m;
}
say "$_: no 'use v5.36;' line" for @bad;
exit( @bad ? 1 : 0 );
