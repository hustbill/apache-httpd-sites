#!/usr/bin/perl -wT

#
# HTTP POST
#  username
#  password
#  action=login|logout  (default = login)
#
# On successful login return JSON with nonzero session token:
#   {"session_token" : "765ADF654A64D566D6F6E66A"}
#
# On successful logut return JSON with zero session token:
#   {"session_token" : "0"}
#
# Errors
#   500 Internal Server Error : my bad
#   400 Bad Request : both username and password not provided
#   401 Unauthorized : incorrect password
#   404 Not Found : no such user
#
# test via curl:
# curl -v --data "username=fred&password=foo" $BASEURL/login.cgi
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
my $action = $cgi->param("action");
$action = "login" if !defined($action) || length($action) <= 0;

unless (defined $username && length($username) > 0 &&
        defined $password && length($password) > 0 &&
	($action eq "login" || $action eq "logout")) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "400 Bad Request");
    exit 1;
}

my $query = 
    "SELECT user_id, passwd_hash, session_token ".
    "FROM $USERS WHERE username = ?";
my $sth = $dbh->prepare($query);
$sth->bind_param(1,$username);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}

my $user_id = -1;
my $passwd_hash;
my $session_token;

my $rows = $sth->fetchall_arrayref();
foreach my $row (@$rows) {  # should be exactly one row
    ($user_id, $passwd_hash, $session_token) = @$row;
}
$sth->finish();

unless ($user_id >= 0) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "404 Not Found");
    exit 1;
}

my $digest = sha1_hex($password);

unless (defined($passwd_hash) && $digest eq $passwd_hash) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "401 Unauthorized");
    exit 1;
}

my $update = 0;

if ($action eq "login") {
    unless (defined($session_token) && length($session_token) > 2) {
	$session_token = sha1_hex(time ^ $$);
	$update = 1;
    }
} else {
    unless ($session_token eq "0") {
	$session_token = "0";
	$update = 1;
    }
}

if ($update) {
    $sth = $dbh->prepare("UPDATE $USERS SET session_token = ? WHERE user_id = ?");
    $sth->bind_param(1,$session_token);
    $sth->bind_param(2,$user_id);
    unless (defined $sth->execute()) {
	print $cgi->header(-type => "application/json", 
			   -charset => "utf-8",
			   -status => "500 Internal Server Error");
	exit 1;
    }
    $sth->finish();
}

print $cgi->header(-type => "application/json", 
		   -charset => "utf-8");

print encode_json({"session_token" => $session_token});

$dbh->disconnect;
