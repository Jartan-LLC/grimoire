# Tests for kelvin.

use v5.36;
use Test::More;
use Tempconv qw(convert);

sub near ( $got, $want, $name ) {
    ok( abs( $got - $want ) < 1e-9, $name ) or diag("got $got, want $want");
}

near( convert( 0,   'C', 'K' ), 273.15,  'C to K' );
near( convert( 300, 'K', 'C' ), 26.85,   'K to C' );
near( convert( 212, 'F', 'K' ), 373.15,  'F to K' );
near( convert( 0,   'K', 'F' ), -459.67, 'K to F' );

eval { convert( -1, 'K', 'C' ) };
like( $@, qr/absolute zero/, 'below 0 K' );
eval { convert( -300, 'C', 'F' ) };
like( $@, qr/absolute zero/, 'below absolute zero in Celsius' );

is( qx{$^X bin/tempconv --from C --to K 26.85}, "300.0\n", 'command' );
is( system( $^X, 'bin/tempconv', '--from', 'K', '--to', 'C', '--', '-5' ) >> 8, 2, 'command: below absolute zero exits 2' );

done_testing;
