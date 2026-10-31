# Tests for Celsius and Fahrenheit.

use v5.36;
use Test::More;
use Tempconv qw(convert format_temp);

is( format_temp( convert( 100, 'C', 'F' ) ), '212.0', 'C to F' );
is( format_temp( convert( 21.5, 'C', 'F' ) ), '70.7', 'C to F with decimals' );
is( format_temp( convert( -40, 'F', 'C' ) ), '-40.0', 'F to C' );
is( format_temp( convert( 12, 'C', 'C' ) ), '12.0', 'same unit' );

eval { convert( 1, 'X', 'C' ) };
like( $@, qr/unknown unit X/, 'unknown unit' );

is( qx{$^X bin/tempconv --from C --to F 21.5}, "70.7\n", 'command' );
is( system( $^X, 'bin/tempconv', '--from', 'R', '--to', 'C', '5' ) >> 8, 2, 'command: unknown unit exits 2' );

done_testing;
