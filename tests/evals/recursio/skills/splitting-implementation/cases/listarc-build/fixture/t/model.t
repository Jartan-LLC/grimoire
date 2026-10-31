use v5.36;
use Test::More;

use Listarc::Model qw(parse_header_block);

subtest 'headers are unfolded and end at the empty line' => sub {
    my ( $fields, $body ) =
        parse_header_block("Subject: a long\r\n  subject\r\nX-Empty:\r\n\r\nHello\r\n");
    is_deeply $fields, [ [ 'Subject', 'a long  subject' ], [ 'X-Empty', '' ] ];
    is $body, "Hello\n";
};

subtest 'a line that is no field starts the body' => sub {
    my ( $fields, $body ) = parse_header_block("From: a\@example.org\nnot a header\nmore\n");
    is_deeply $fields, [ [ 'From', 'a@example.org' ] ];
    is $body, "not a header\nmore\n";
};

subtest 'a message finds its fields in any case' => sub {
    my $m = Listarc::Message->parse( "Received: one\nreceived: two\n\nbody\n", position => 4 );
    is $m->header('RECEIVED'), 'one';
    is_deeply [ $m->header_all('received') ], [ 'one', 'two' ];
    is $m->header('Subject'), undef;
    is $m->position, 4;
    is $m->as_bytes, "Received: one\nreceived: two\n\nbody\n";
};

subtest 'a summary refuses unknown fields' => sub {
    my $s = Listarc::Summary->new( position => 0, message_id => 'a@b' );
    is_deeply $s->from, [];
    is $s->subject, '';
    ok !eval { Listarc::Summary->new( position => 0, sender => 'x' ); 1 };
};

subtest 'errors say where they were found' => sub {
    my $error = eval { Listarc::Error->throw( message => 'not an mbox', line => 1 ) } || $@;
    isa_ok $error, 'Listarc::Error';
    is "$error", 'line 1: not an mbox';
    is Listarc::Error->new( message => 'unknown field foo', column => 7 )->as_string,
        'column 7: unknown field foo';
};

done_testing;
