package Listarc::Model;

# The values the listarc modules pass to one another.

use v5.36;

use Exporter 'import';
our @EXPORT_OK = qw(parse_header_block);

# (\@fields, $body) from the bytes of a message or a MIME part. CRLF becomes LF first. Each field
# is [name, value], in order, the value unfolded: a continuation line (one starting with a space or
# tab) is appended with its line break removed and its leading whitespace kept. The headers end
# at the first empty line, which belongs to neither; a line that is neither a field nor a
# continuation ends them too, and starts the body.
sub parse_header_block ($bytes) {
    $bytes =~ s/\r\n/\n/g;
    my @fields;
    my $pos = 0;
    while ($pos < length $bytes) {
        my $end  = index $bytes, "\n", $pos;
        my $stop = $end < 0 ? length $bytes : $end;
        my $line = substr $bytes, $pos, $stop - $pos;
        if ($line eq '') {
            $pos = $stop + 1;
            last;
        }
        if ($line =~ /\A([\x21-\x39\x3B-\x7E]+):[ \t]*(.*)\z/s) {
            push @fields, [ $1, $2 ];
        }
        elsif ($line =~ /\A[ \t]/ && @fields) {
            $fields[-1][1] .= $line;
        }
        else {
            last;
        }
        $pos = $stop + 1;
    }
    my $body = $pos < length $bytes ? substr $bytes, $pos : '';
    return ( \@fields, $body );
}

package Listarc::Message;

# One message as read from an archive. Header values and the body are bytes, undecoded.
#   headers  - arrayref of [name, value] pairs in order, as parse_header_block gives them
#   body     - the bytes after the header block, lines ending in LF
#   envelope - the mbox separator line without its leading "From ", or undef
#   position - the message's index in its archive, from 0, or undef

use v5.36;

sub new ( $class, %args ) {
    return bless {
        headers  => $args{headers} // [],
        body     => $args{body}    // '',
        envelope => $args{envelope},
        position => $args{position},
    }, $class;
}

# A message from its bytes; %args may give envelope and position.
sub parse ( $class, $bytes, %args ) {
    my ( $headers, $body ) = Listarc::Model::parse_header_block($bytes);
    return $class->new( %args, headers => $headers, body => $body );
}

sub headers ($self)  { return $self->{headers} }
sub body ($self)     { return $self->{body} }
sub envelope ($self) { return $self->{envelope} }
sub position ($self) { return $self->{position} }

# The value of the first field named $name, in any case, or undef.
sub header ( $self, $name ) {
    my ($value) = $self->header_all($name);
    return $value;
}

# Every value of the fields named $name, in any case, in order.
sub header_all ( $self, $name ) {
    my $want = lc $name;
    return map { $_->[1] } grep { lc $_->[0] eq $want } @{ $self->{headers} };
}

# The header block, one line per field, an empty line, then the body.
sub as_bytes ($self) {
    return join( '', map {"$_->[0]: $_->[1]\n"} @{ $self->{headers} } ) . "\n" . $self->{body};
}

package Listarc::Summary;

# What the command knows of a message once its headers and body are decoded; what a search
# query is matched against. Text fields are Perl character strings.
#   position     - the message's index in its archive, from 0
#   message_id   - the Message-ID without its angle brackets, or undef
#   from, to, cc - arrayrefs of addresses, each { name => text or '', address => 'local@domain' }
#   subject      - the decoded subject, '' when there is none
#   date         - seconds since the epoch, UTC, or undef when the message has no usable date
#   body         - the text of the message's main text part, '' when there is none
#   attachments  - arrayref of { filename => text, type => 'type/subtype', size => bytes }

use v5.36;

my @FIELDS = qw(position message_id from to cc subject date body attachments);

sub new ( $class, %args ) {
    my %self = (
        from        => [],
        to          => [],
        cc          => [],
        subject     => '',
        body        => '',
        attachments => [],
        %args,
    );
    my @unknown = grep { my $k = $_; !grep { $_ eq $k } @FIELDS } sort keys %self;
    die "unknown Summary field: @unknown\n" if @unknown;
    return bless \%self, $class;
}

for my $field (@FIELDS) {
    no strict 'refs';
    *{$field} = sub ($self) { return $self->{$field} };
}

package Listarc::Error;

# The exception every listarc module throws for input it refuses. `line` counts lines of the
# input from 1 and `column` characters of a query from 1; either may be undef.

use v5.36;

use overload '""' => sub ( $self, @ ) { $self->as_string }, fallback => 1;

sub new ( $class, %args ) {
    return bless { message => $args{message}, line => $args{line}, column => $args{column} },
        $class;
}

sub throw ( $class, %args ) { die $class->new(%args) }

sub message ($self) { return $self->{message} }
sub line ($self)    { return $self->{line} }
sub column ($self)  { return $self->{column} }

# "line 3: not an mbox", "column 7: unknown field foo", or the message alone.
sub as_string ($self) {
    return "line $self->{line}: $self->{message}"     if defined $self->{line};
    return "column $self->{column}: $self->{message}" if defined $self->{column};
    return $self->{message};
}

1;
