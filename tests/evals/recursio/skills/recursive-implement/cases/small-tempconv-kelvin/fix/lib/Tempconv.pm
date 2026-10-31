package Tempconv;

# Convert temperatures between units, by way of Celsius.

use v5.36;
use Exporter 'import';

our @EXPORT_OK = qw(convert format_temp);

my %TO_CELSIUS = (
    C => sub ($v) { $v },
    F => sub ($v) { ( $v - 32 ) * 5 / 9 },
    K => sub ($v) { $v - 273.15 },
);

my %FROM_CELSIUS = (
    C => sub ($c) { $c },
    F => sub ($c) { $c * 9 / 5 + 32 },
    K => sub ($c) { $c + 273.15 },
);

sub convert ( $value, $from, $to ) {
    my $to_celsius   = $TO_CELSIUS{$from} or die "unknown unit $from\n";
    my $from_celsius = $FROM_CELSIUS{$to} or die "unknown unit $to\n";
    my $celsius = $to_celsius->($value);
    die "$value $from is below absolute zero\n" if $celsius < -273.15;
    return $from_celsius->($celsius);
}

sub format_temp ($value) {
    return sprintf '%.1f', $value;
}

1;
