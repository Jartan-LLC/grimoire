package Tempconv;

# Convert temperatures between units, by way of Celsius.

use v5.36;
use Exporter 'import';

our @EXPORT_OK = qw(convert format_temp);

my %TO_CELSIUS = (
    C => sub ($v) { $v },
    F => sub ($v) { ( $v - 32 ) * 5 / 9 },
);

my %FROM_CELSIUS = (
    C => sub ($c) { $c },
    F => sub ($c) { $c * 9 / 5 + 32 },
);

sub convert ( $value, $from, $to ) {
    my $to_celsius   = $TO_CELSIUS{$from} or die "unknown unit $from\n";
    my $from_celsius = $FROM_CELSIUS{$to} or die "unknown unit $to\n";
    return $from_celsius->( $to_celsius->($value) );
}

sub format_temp ($value) {
    return sprintf '%.1f', $value;
}

1;
