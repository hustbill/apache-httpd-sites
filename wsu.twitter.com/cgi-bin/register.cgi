#!/usr/bin/perl -wT

#
# HTTP POST
#  username
#  password
#
# Return JSON
#   {"session_token" : "765ADF654A64D566D6F6E66A"}
#
# Errors
#   500 Internal Server Error : my bad
#   400 Bad Request : both username and password not provided
#   409 Conflict User Exists : user already registered
#
# test via curl:
# curl -v --data "username=fred&password=foo" $BASEURL/register.cgi
#

use strict;
use CGI;
use DBI;
use HTML::Entities;
use JSON;
use Digest::SHA qw(sha1_hex);

my $cgi = new CGI;

my $DB = "wsu-twitter.db";
my $TWEETS = "tweets";
my $USERS = "users";

my $dbh = DBI->connect("DBI:SQLite:dbname=$DB", "", "");
unless ($dbh) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "503 Database Unavailable");
    exit 1;
}

my $username = $cgi->param("username");
my $password = $cgi->param("password");

unless (defined $username && length($username) > 0 &&
        defined $password && length($password) > 0) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "400 Bad Request");
    exit 1;
}

my $sth = $dbh->prepare("SELECT username FROM $USERS WHERE username = ?");
$sth->bind_param(1,$username);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}

my $rows = $sth->fetchall_arrayref();
$sth->finish();
if (@$rows != 0) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "409 Conflict User Exists");
    exit 1;
}

#
# passwd_hash is sha-1 hash.
# session token is some unique sha-1 hash
#
my $digest = sha1_hex($password);
my $token = sha1_hex(time ^ $$);

my $query =
     "INSERT INTO $USERS (username, passwd_hash, session_token) " .
     "VALUES(?, ?, ?)";
$sth = $dbh->prepare($query);
$sth->bind_param(1,$username);
$sth->bind_param(2,$digest);
$sth->bind_param(3,$token);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}
$sth->finish();

print $cgi->header(-type => "application/json", 
		   -charset => "utf-8");

print encode_json({"session_token" => $token});

$dbh->disconnect;
