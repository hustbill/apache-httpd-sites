#!/usr/bin/perl

use Digest::SHA qw(sha1_hex);

@ARGV == 1 or die "usage: $0 password\n";

my $digest = sha1_hex($ARGV[0]);

print "$digest\n";
